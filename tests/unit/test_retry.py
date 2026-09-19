"""Unit tests for bounded retry, backoff, and pacing (spec FR-007, T014)."""

import pytest
import requests

from pipeline.config import Config
from pipeline.deliver import MAX_ATTEMPTS, DeliveryError, send_parts


class FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def make_config():
    return Config(token="t", chat_id="c", posts_dir="posts", ledger_path="l.json")


def _ok(message_id):
    return FakeResponse(200, {"result": {"message_id": message_id}})


def _responder(responses):
    queue = list(responses)
    def post(url, json=None, timeout=None):
        item = queue.pop(0) if queue else FakeResponse(500)
        if isinstance(item, Exception):
            raise item
        return item
    return post


def test_first_attempt_success_no_sleeps(fast_sleep):
    post = _responder([FakeResponse(200, {"result": {"message_id": 101}})])
    ids = send_parts(make_config(), ["hello"], sleep=fast_sleep.append, post=post)
    assert ids == [101]
    assert fast_sleep == []


def test_transient_error_retries_then_succeeds(fast_sleep):
    post = _responder([FakeResponse(500), _ok(7)])
    ids = send_parts(make_config(), ["hello"], sleep=fast_sleep.append, post=post)
    assert ids == [7]
    assert fast_sleep == [2]


def test_rate_limit_honors_retry_after(fast_sleep):
    post = _responder([FakeResponse(429, {"parameters": {"retry_after": 7}}), _ok(9)])
    ids = send_parts(make_config(), ["hello"], sleep=fast_sleep.append, post=post)
    assert ids == [9]
    assert fast_sleep == [7]


def test_exhausted_retries_fail_with_attempt_count(fast_sleep):
    post = _responder([FakeResponse(500)] * 5)
    with pytest.raises(DeliveryError) as excinfo:
        send_parts(make_config(), ["hello"], sleep=fast_sleep.append, post=post)
    assert excinfo.value.attempts == MAX_ATTEMPTS
    assert "HTTP 500" in str(excinfo.value)
    assert fast_sleep == [2, 4]


def test_network_errors_count_as_attempts(fast_sleep):
    post = _responder([requests.ConnectionError("boom")] * 4)
    with pytest.raises(DeliveryError) as excinfo:
        send_parts(make_config(), ["hello"], sleep=fast_sleep.append, post=post)
    assert "network error" in str(excinfo.value)


def test_messages_paced_two_seconds_apart(fast_sleep):
    post = _responder([_ok(1), _ok(2)])
    ids = send_parts(make_config(), ["a", "b"], sleep=fast_sleep.append, post=post)
    assert ids == [1, 2]
    assert fast_sleep == [2]
