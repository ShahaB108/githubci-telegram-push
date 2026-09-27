"""Environment-driven configuration per the pipeline interface contract.

Credentials come ONLY from the environment; there are no defaults for secrets and
they are never logged (constitution Principle VI, spec FR-006). Non-secret defaults are
resolved against the repository root, so the pipeline behaves the same no matter which
directory it is invoked from.
"""

import os

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))  # <repo>/engine/pipeline
_ENGINE_DIR = os.path.dirname(_PACKAGE_DIR)                # <repo>/engine


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid (exit 10)."""


class Config:
    """Validated runtime configuration."""

    def __init__(self, token, chat_id, posts_dir, ledger_path,
                 repo_root=None, ignored_names=None, commit_ledger=True):
        self.token = token
        self.chat_id = chat_id
        self.posts_dir = posts_dir
        self.ledger_path = ledger_path
        self.repo_root = os.path.abspath(repo_root or os.getcwd())
        self.ignored_names = ignored_names
        self.commit_ledger = commit_ledger


def repo_root(environ=None):
    """Repository root: the PIPELINE_REPO_ROOT override, else the nearest .git ancestor."""
    env = os.environ if environ is None else environ
    override = env.get("PIPELINE_REPO_ROOT", "").strip()
    if override:
        return os.path.abspath(override)
    candidate = _ENGINE_DIR
    while True:
        if os.path.isdir(os.path.join(candidate, ".git")):
            return candidate
        parent = os.path.dirname(candidate)
        if parent == candidate:
            return os.getcwd()
        candidate = parent


def load_config(environ=None):
    """Load configuration from the environment; raise ConfigError when invalid."""
    env = os.environ if environ is None else environ
    token = env.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = env.get("TELEGRAM_CHAT_ID", "").strip()
    if not token:
        raise ConfigError("TELEGRAM_BOT_TOKEN is missing or empty")
    if not chat_id:
        raise ConfigError("TELEGRAM_CHAT_ID is missing or empty")
    root = repo_root(env)
    ignored = [name.strip() for name in env.get("PIPELINE_IGNORE", "").split(",")
               if name.strip()]
    return Config(
        token=token,
        chat_id=chat_id,
        posts_dir=env.get("PIPELINE_POSTS_DIR") or root,
        ledger_path=env.get("PIPELINE_LEDGER_PATH") or os.path.join(
            _ENGINE_DIR, "delivery", "ledger.json"),
        repo_root=root,
        ignored_names=ignored or None,
        # CI keeps delivery state outside the mirrored branch, so it disables the
        # commit-back; every other environment keeps the default (commit + push).
        commit_ledger=env.get("PIPELINE_COMMIT", "1").strip().lower()
        not in ("0", "false", "no"),
    )
