"""Delivery ledger store per data-model.md (schema version 1).

Ledger shape: {"version": 1, "records": [DeliveryRecord, ...]} where each record has
post_path (unique per record), delivered_at (ISO 8601 UTC), message_ids (list of int)
and status ("delivered" or "partial"). Writes are atomic (temp file + os.replace).
"""

import copy
import json
import os
import tempfile

SCHEMA_VERSION = 1
VALID_STATUSES = ("delivered", "partial")


class LedgerError(Exception):
    """Raised on ledger load/save problems (exit 40)."""


def empty_ledger():
    return {"version": SCHEMA_VERSION, "records": []}


def load(path):
    """Load the ledger; a missing file yields an empty ledger (exit 40 on I/O errors)."""
    if not os.path.exists(path):
        return empty_ledger()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        raise LedgerError(f"cannot read ledger {path}: {exc}") from exc
    except ValueError as exc:
        raise LedgerError(f"ledger {path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict) or data.get("version") != SCHEMA_VERSION:
        raise LedgerError(f"unsupported ledger schema in {path}")
    paths = [record.get("post_path") for record in data.get("records", [])]
    if len(paths) != len(set(paths)):
        raise LedgerError(f"duplicate post_path entries in {path}")
    return data


def save(path, ledger):
    """Persist the ledger atomically (temp file + os.replace)."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    handle_fd, tmp_path = tempfile.mkstemp(
        dir=directory or ".", prefix=".ledger-", suffix=".tmp")
    try:
        with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
            json.dump(ledger, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp_path, path)
    except OSError as exc:
        raise LedgerError(f"cannot write ledger {path}: {exc}") from exc
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def record_for(ledger, post_path):
    """Return the record for post_path or None (spec FR-002 identity lookup)."""
    for record in ledger.get("records", []):
        if record.get("post_path") == post_path:
            return record
    return None


def upsert_record(ledger, post_path, message_ids, status, delivered_at):
    """Insert or replace the record for post_path (uniqueness per data-model.md)."""
    if status not in VALID_STATUSES:
        raise LedgerError(f"invalid record status: {status}")
    records = [record for record in ledger.get("records", [])
               if record.get("post_path") != post_path]
    records.append({
        "post_path": post_path,
        "delivered_at": delivered_at,
        "message_ids": list(message_ids),
        "status": status,
    })
    ledger["records"] = records
    return record_for(ledger, post_path)


def snapshot(ledger):
    """Deep copy used to detect whether a run changed delivery state."""
    return copy.deepcopy(ledger)
