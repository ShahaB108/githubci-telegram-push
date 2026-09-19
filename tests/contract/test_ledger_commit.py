"""Contract tests for ledger commit-back and re-run idempotency (spec FR-009, T019)."""

import json
from types import SimpleNamespace

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
        return item
    monkeypatch.setattr(deliver_mod.requests, "post", post)
    return calls


def install_git_spy(monkeypatch):
    commands = []
    def fake_run(command, capture_output=True, text=True, **_kwargs):
        commands.append(list(command))
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    monkeypatch.setattr("pipeline.main.subprocess.run", fake_run)
    return commands


def test_ledger_committed_with_chore_prefix(env, write_post, monkeypatch):
    write_post("hello.md")
    install_fake_post(monkeypatch)
    commands = install_git_spy(monkeypatch)
    assert main_mod.main([]) == 0
    joined = [" ".join(command) for command in commands]
    assert any(command.startswith("git add") and command.endswith("ledger.json")
               for command in joined)
    assert any("chore(delivery):" in command for command in joined)
    assert any(command == "git push" for command in joined)


def test_second_run_delivers_nothing_new(env, write_post, monkeypatch, capsys):
    write_post("hello.md")
    calls = install_fake_post(monkeypatch)
    install_git_spy(monkeypatch)
    assert main_mod.main([]) == 0
    assert main_mod.main([]) == 0
    assert "nothing to publish" in capsys.readouterr().out
    assert len(calls) == 1


def test_partial_delivery_resumes_remaining_parts(env, write_post, monkeypatch):
    write_post("long.md", body="sentence " * 1400)
    identity = str(env / "posts" / "long.md").replace("\\", "/")
    ledger_path = env / "delivery" / "ledger.json"
    ledger_path.parent.mkdir(exist_ok=True)
    ledger_path.write_text(json.dumps({
        "version": 1,
        "records": [{"post_path": identity,
                     "delivered_at": "2026-09-18T00:00:00+00:00",
                     "message_ids": [101, 102], "status": "partial"}],
    }), encoding="utf-8")
    calls = install_fake_post(monkeypatch, [
        FakeResponse(200, {"result": {"message_id": 103}}),
        FakeResponse(200, {"result": {"message_id": 104}}),
    ])
    install_git_spy(monkeypatch)
    assert main_mod.main([]) == 0
    assert len(calls) == 2
    records = json.loads(ledger_path.read_text(encoding="utf-8"))["records"]
    assert records[0]["status"] == "delivered"
    assert records[0]["message_ids"] == [101, 102, 103, 104]
