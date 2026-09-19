"""Shared fixtures for pipeline tests."""

import pytest


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Isolated pipeline environment rooted at tmp_path (posts/, delivery/)."""
    posts_dir = tmp_path / "posts"
    posts_dir.mkdir()
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-secret-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "@test_channel")
    monkeypatch.setenv("PIPELINE_POSTS_DIR", str(posts_dir))
    monkeypatch.setenv("PIPELINE_LEDGER_PATH", str(tmp_path / "delivery" / "ledger.json"))
    return tmp_path


@pytest.fixture
def write_post(env):
    """Write a Markdown post under the isolated posts directory."""
    def _write(name, body="Hello **world** paragraph.", frontmatter=None):
        text = "" if frontmatter is None else f"---\n{frontmatter}\n---\n"
        path = env / "posts" / name
        path.write_text(text + body, encoding="utf-8")
        return path
    return _write


@pytest.fixture
def fast_sleep(monkeypatch):
    """Replace pipeline.deliver sleeps with recorded no-ops."""
    sleeps = []
    monkeypatch.setattr("pipeline.deliver.time.sleep", sleeps.append)
    return sleeps
