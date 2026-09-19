"""Environment-driven configuration per contracts/pipeline-interface.md.

Credentials come ONLY from the environment; there are no defaults for secrets and
they are never logged (constitution Principle VI, spec FR-006).
"""

import os


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid (exit 10)."""


class Config:
    """Validated runtime configuration."""

    def __init__(self, token, chat_id, posts_dir, ledger_path):
        self.token = token
        self.chat_id = chat_id
        self.posts_dir = posts_dir
        self.ledger_path = ledger_path


def load_config(environ=None):
    """Load configuration from the environment; raise ConfigError when invalid."""
    env = os.environ if environ is None else environ
    token = env.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = env.get("TELEGRAM_CHAT_ID", "").strip()
    if not token:
        raise ConfigError("TELEGRAM_BOT_TOKEN is missing or empty")
    if not chat_id:
        raise ConfigError("TELEGRAM_CHAT_ID is missing or empty")
    return Config(
        token=token,
        chat_id=chat_id,
        posts_dir=env.get("PIPELINE_POSTS_DIR", "posts"),
        ledger_path=env.get("PIPELINE_LEDGER_PATH", "delivery/ledger.json"),
    )
