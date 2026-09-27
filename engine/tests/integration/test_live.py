"""Integration smoke test against the real Telegram test channel (env-gated, T025).

Skipped unless TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are present, so CI and local
unit runs stay hermetic (constitution Principle VI: no credentials in the repo).
"""

import os

import pytest

from pipeline.config import load_config
from pipeline.deliver import send_parts

pytestmark = pytest.mark.skipif(
    not (os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID")),
    reason="live Telegram credentials not present; set TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID",
)


def test_live_single_message_delivery():
    config = load_config()
    message_ids = send_parts(config, ["pipeline integration smoke test"])
    assert isinstance(message_ids[0], int)
