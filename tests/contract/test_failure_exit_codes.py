"""Contract tests for failure modes and exit codes (spec FR-006/FR-007/FR-008, T015)."""

from pipeline import main as main_mod


class FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def install_fake_post(monkeypatch, responses):
    from pipeline import deliver as deliver_mod
    calls = []
    queue = list(responses)
    def post(url, json=None, timeout=None):
        calls.append({"url": url, "payload": json})
        item = queue.pop(0) if queue else FakeResponse(500)
        return item
    monkeypatch.setattr(deliver_mod.requests, "post", post)
    return calls


def test_missing_token_fails_fast_exit_10(env, write_post, monkeypatch, capsys):
    write_post("hello.md")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    calls = install_fake_post(monkeypatch, [])
    assert main_mod.main([]) == 10
    assert "TELEGRAM_BOT_TOKEN" in capsys.readouterr().err
    assert calls == []


def test_malformed_post_exit_20_names_file(env, write_post, monkeypatch, capsys):
    write_post("broken.md", body="", frontmatter="title: X")
    install_fake_post(monkeypatch, [])
    assert main_mod.main([]) == 20
    assert "broken.md" in capsys.readouterr().err


def test_delivery_failure_after_retries_exit_30(env, write_post, monkeypatch,
                                                fast_sleep, capsys):
    write_post("hello.md")
    install_fake_post(monkeypatch, [FakeResponse(500)] * 5)
    assert main_mod.main([]) == 30
    err = capsys.readouterr().err
    assert "hello.md" in err
    assert "delivery failed after 3 attempts" in err
    assert "HTTP 500" in err


def test_secrets_never_logged(env, write_post, monkeypatch, fast_sleep, capsys):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "super-secret-token-value")
    write_post("hello.md")
    install_fake_post(monkeypatch, [FakeResponse(500)] * 5)
    assert main_mod.main([]) == 30
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "super-secret-token-value" not in combined
    assert "api.telegram.org" not in combined


def test_ledger_io_error_exit_40(env, monkeypatch, capsys):
    monkeypatch.setenv("PIPELINE_LEDGER_PATH", str(env))
    assert main_mod.main([]) == 40
    assert "ledger" in capsys.readouterr().err
