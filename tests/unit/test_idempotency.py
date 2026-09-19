"""Unit tests for ledger idempotency semantics (spec FR-009, T018)."""

import pytest

from pipeline.ledger import LedgerError, empty_ledger, load, record_for, save, upsert_record


def test_record_for_missing_path_is_none():
    assert record_for(empty_ledger(), "posts/a.md") is None


def test_upsert_replaces_existing_record(tmp_path):
    ledger = empty_ledger()
    upsert_record(ledger, "posts/a.md", [1], "partial", "2026-09-18T00:00:00+00:00")
    upsert_record(ledger, "posts/a.md", [1, 2], "delivered", "2026-09-18T00:00:01+00:00")
    path = str(tmp_path / "ledger.json")
    save(path, ledger)
    records = load(path)["records"]
    assert len(records) == 1
    assert records[0]["status"] == "delivered"
    assert records[0]["message_ids"] == [1, 2]


def test_partial_record_keeps_progress(tmp_path):
    ledger = empty_ledger()
    upsert_record(ledger, "posts/a.md", [1, 2], "partial", "2026-09-18T00:00:00+00:00")
    path = str(tmp_path / "ledger.json")
    save(path, ledger)
    record = load(path) and record_for(load(path), "posts/a.md")
    assert record["status"] == "partial"
    assert record["message_ids"] == [1, 2]


def test_invalid_status_rejected():
    with pytest.raises(LedgerError):
        upsert_record(empty_ledger(), "posts/a.md", [1], "sent",
                      "2026-09-18T00:00:00+00:00")


def test_duplicate_paths_rejected_on_load(tmp_path):
    ledger = {"version": 1, "records": [
        {"post_path": "posts/a.md", "delivered_at": "t", "message_ids": [1],
         "status": "delivered"},
        {"post_path": "posts/a.md", "delivered_at": "t", "message_ids": [2],
         "status": "delivered"},
    ]}
    path = str(tmp_path / "dup.json")
    save(path, ledger)
    with pytest.raises(LedgerError):
        load(path)
