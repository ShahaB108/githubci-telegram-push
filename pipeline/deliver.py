"""Telegram delivery client with bounded retry and pacing (FR-003, FR-005, FR-007)."""

import time

import requests

API_URL_TEMPLATE = "https://api.telegram.org/bot{token}/sendMessage"
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (2, 4, 8)
PACING_SECONDS = 2  # minimum spacing between consecutive channel messages (FR-003)
REQUEST_TIMEOUT_SECONDS = 30


def _sleep(seconds):
    time.sleep(seconds)


class DeliveryError(Exception):
    """Raised when a message could not be delivered after all attempts (exit 30).

    Carries the number of attempts made and the ids of messages delivered so far
    within the same run, so partial progress can be recorded (spec FR-009).
    """

    def __init__(self, message, attempts, delivered_ids=None):
        super().__init__(message)
        self.attempts = attempts
        self.delivered_ids = list(delivered_ids or [])


def send_parts(config, parts, sleep=None, post=None):
    """Deliver each message part in order; returns the list of Telegram message ids."""
    sleep = sleep or _sleep
    post = post or requests.post
    sent = []
    for index, text in enumerate(parts):
        if index > 0:
            sleep(PACING_SECONDS)
        try:
            sent.append(_send_one(config, text, sleep, post))
        except DeliveryError as exc:
            raise DeliveryError(exc.args[0], exc.attempts, list(sent)) from exc
    return sent


def _send_one(config, text, sleep, post):
    """Send one message with up to MAX_ATTEMPTS attempts (bounded retry, FR-007)."""
    last_error = "unknown error"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = post(
                API_URL_TEMPLATE.format(token=config.token),
                json={
                    "chat_id": config.chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            last_error = f"network error: {exc}"
        else:
            if response.status_code == 200:
                return response.json()["result"]["message_id"]
            if response.status_code == 429:
                retry_after = _retry_after(response)
                last_error = f"HTTP 429 (retry_after={retry_after})"
                sleep(retry_after)
                continue
            last_error = f"HTTP {response.status_code}"
        if attempt < MAX_ATTEMPTS:
            sleep(BACKOFF_SECONDS[min(attempt - 1, len(BACKOFF_SECONDS) - 1)])
    raise DeliveryError(
        f"delivery failed after {MAX_ATTEMPTS} attempts: {last_error}",
        MAX_ATTEMPTS)


def _retry_after(response):
    """Extract the Retry-After hint from a 429 response, defaulting to 1 second."""
    try:
        return int(response.json().get("parameters", {}).get("retry_after", 1))
    except (ValueError, AttributeError):
        return 1
