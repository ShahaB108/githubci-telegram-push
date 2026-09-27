"""Unit tests for repository-root resolution and ledger post identity."""

import os

from pipeline import main as main_mod
from pipeline.config import load_config, repo_root


def test_repo_root_honours_override(tmp_path):
    assert repo_root({"PIPELINE_REPO_ROOT": str(tmp_path)}) == str(tmp_path)


def test_repo_root_is_the_directory_that_holds_engine():
    """repo_root() walks up from the package location, not from the current directory."""
    root = repo_root({})
    assert os.path.isfile(os.path.join(root, "engine", "pipeline", "config.py"))


def test_default_posts_dir_is_repo_root_and_ledger_lives_in_engine(monkeypatch, tmp_path):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "c")
    monkeypatch.setenv("PIPELINE_REPO_ROOT", str(tmp_path))
    monkeypatch.delenv("PIPELINE_POSTS_DIR", raising=False)
    monkeypatch.delenv("PIPELINE_LEDGER_PATH", raising=False)
    config = load_config()
    assert config.posts_dir == str(tmp_path)
    assert config.ledger_path.endswith(os.path.join("engine", "delivery", "ledger.json"))


def test_commit_back_is_on_by_default_and_can_be_disabled(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "c")
    monkeypatch.delenv("PIPELINE_COMMIT", raising=False)
    assert load_config().commit_ledger is True
    for value in ("0", "false", "no"):
        monkeypatch.setenv("PIPELINE_COMMIT", value)
        assert load_config().commit_ledger is False
    monkeypatch.setenv("PIPELINE_COMMIT", "1")
    assert load_config().commit_ledger is True


def test_relative_identity_is_repo_relative_with_forward_slashes(tmp_path):
    nested = tmp_path / "posts" / "hello.md"
    assert main_mod._relative(str(nested), str(tmp_path)) == "posts/hello.md"