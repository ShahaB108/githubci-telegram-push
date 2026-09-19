"""Contract tests for the publish CLI happy path (spec FR-003/FR-005/FR-008, T009)."""

import json

from pipeline import main as main_mod


class FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def install_fake_post(monkeypatch, responses=None):
    from pipeline import deliver as deliver_mod
    calls = []
    queue = list(responses or [])
    def post(url, json=None, timeout=None):
        calls.append({"url": url, "payload": json})
        item = queue.pop(0) if queue else FakeResponse(
            200, {"result": {"message_id": 100 + len(calls)}})
        if isinstance(item, Exception):
            raise item
        return item
    monkeypatch.setattr(deliver_mod.requests, "post", post)
    return calls


def test_happy_path_exit_zero_and_ledger_updated(env, write_post, monkeypatch, capsys):
    write_post("hello.md")
    calls = install_fake_post(monkeypatch)
    assert main_mod.main([]) == 0
    out = capsys.readouterr().out
    assert "run summary" in out
    assert "posts/hello.md" in out
    ledger_path = env / "delivery" / "ledger.json"
    assert ledger_path.exists()
    records = json.loads(ledger_path.read_text(encoding="utf-8"))["records"]
    assert records[0]["post_path"].endswith("posts/hello.md")
    assert records[0]["status"] == "delivered"
    assert calls[0]["payload"]["parse_mode"] == "HTML"
    assert calls[0]["payload"]["chat_id"] == "@test_channel"


def test_dry_run_prints_plan_and_writes_nothing(env, write_post, monkeypatch, capsys):
    write_post("hello.md")
    calls = install_fake_post(monkeypatch)
    assert main_mod.main(["--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "would deliver" in out
    assert not (env / "delivery" / "ledger.json").exists()
    assert calls == []


def test_nothing_to_publish_exits_zero(env, capsys):
    assert main_mod.main([]) == 0
    assert "nothing to publish" in capsys.readouterr().out
