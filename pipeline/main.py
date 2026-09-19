"""CLI entry point: detect -> convert -> deliver -> record.

Implements the interface contract in specs/001-telegram-publishing/contracts/
pipeline-interface.md: flags, environment configuration, exit codes, run summary,
and the ledger commit-back with the chore(delivery): prefix (FR-002..FR-010).
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import UTC, datetime

from pipeline import config as config_mod
from pipeline import convert
from pipeline import deliver as deliver_mod
from pipeline import detect as detect_mod
from pipeline import ledger as ledger_mod
from pipeline.config import ConfigError
from pipeline.deliver import DeliveryError
from pipeline.detect import MalformedPostError
from pipeline.ledger import LedgerError

EXIT_OK = 0
EXIT_CONFIG = 10
EXIT_MALFORMED_POST = 20
EXIT_DELIVERY = 30
EXIT_LEDGER_IO = 40
COMMIT_MESSAGE_PREFIX = "chore(delivery):"


def main(argv=None):
    """Run the publishing pipeline; returns the process exit code."""
    parser = argparse.ArgumentParser(prog="pipeline", description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="plan deliveries and print them without writing anything")
    parser.add_argument("--limit", type=int, default=None,
                        help="cap the number of posts delivered in this run")
    args = parser.parse_args(argv)
    try:
        return _run(args)
    except ConfigError as exc:
        return _fail(EXIT_CONFIG, f"configuration error: {exc}")
    except MalformedPostError as exc:
        return _fail(EXIT_MALFORMED_POST, f"malformed post: {exc}")
    except DeliveryError as exc:
        return _fail(EXIT_DELIVERY, f"delivery failed: {exc}")
    except LedgerError as exc:
        return _fail(EXIT_LEDGER_IO, f"ledger error: {exc}")


def _run(args):
    config = config_mod.load_config()
    ledger = ledger_mod.load(config.ledger_path)
    original = ledger_mod.snapshot(ledger)
    considered, to_publish, skipped = [], [], []
    for full_path in detect_mod.discover_posts(config.posts_dir):
        relative = _relative(full_path)
        considered.append(relative)
        record = ledger_mod.record_for(ledger, relative)
        meta, body = detect_mod.parse_post(full_path)
        if detect_mod.is_draft(meta):
            skipped.append(relative)
            print(f"skipped {relative}: draft")
            continue
        if record is not None and record.get("status") == "delivered":
            skipped.append(relative)
            print(f"skipped {relative}: already delivered")
            continue
        to_publish.append({"path": relative, "record": record,
                           "meta": meta, "body": body})
    if args.limit is not None:
        to_publish = to_publish[: args.limit]
    if not to_publish:
        print("nothing to publish: all posts are already delivered")
        return EXIT_OK
    delivered = []
    try:
        for entry in to_publish:
            _deliver_entry(args, config, ledger, entry, delivered)
    except DeliveryError:
        _persist(args, config, ledger, original)  # keep partial progress visible
        raise
    _persist(args, config, ledger, original)
    print(f"run summary: considered={len(considered)} delivered={len(delivered)} skipped={len(skipped)}")
    return EXIT_OK


def _deliver_entry(args, config, ledger, entry, delivered):
    relative, record = entry["path"], entry["record"]
    title = _title(entry["meta"], entry["body"], relative)
    message = convert.build_message(title, convert.to_telegram_html(entry["body"]))
    parts = convert.split_message(message)
    if args.dry_run:
        print(f"would deliver {relative} ({len(parts)} part(s))")
        return
    already = []
    if record is not None and record.get("status") == "partial":
        already = list(record.get("message_ids", []))
        parts = parts[len(already):]  # resume only the missing parts (FR-009)
        if not parts:
            ledger_mod.upsert_record(ledger, relative, already, "delivered", _now())
            delivered.append(relative)
            print(f"completed previously partial delivery: {relative}")
            return
    try:
        message_ids = deliver_mod.send_parts(config, parts)
    except DeliveryError as exc:
        if exc.delivered_ids:
            ledger_mod.upsert_record(ledger, relative, already + exc.delivered_ids,
                                     "partial", _now())
        raise DeliveryError(f"{relative}: {exc}", exc.attempts,
                            exc.delivered_ids) from exc
    ledger_mod.upsert_record(ledger, relative, already + message_ids,
                             "delivered", _now())
    delivered.append(relative)
    print(f"delivered {relative} ({len(already) + len(message_ids)} message(s))")


def _persist(args, config, ledger, original):
    """Save the ledger and commit it back when delivery state changed (FR-009)."""
    if args.dry_run or ledger == original:
        return
    ledger_mod.save(config.ledger_path, ledger)
    _commit_ledger(config)


def _commit_ledger(config):
    """Commit (and push) the ledger with the chore(delivery): prefix; non-fatal on failure."""
    for command in (["git", "add", config.ledger_path],
                    ["git", "commit", "-m",
                     f"{COMMIT_MESSAGE_PREFIX} record deliveries"],
                    ["git", "push"]):
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            print("ledger git step skipped ({}): {}".format(
                " ".join(command),
                (completed.stderr or completed.stdout or "").strip()),
                file=sys.stderr)
            return


def _title(meta, body, relative):
    if meta.get("title"):
        return str(meta["title"])
    match = re.match(r"^#\s+(.+)$", body.strip(), flags=re.MULTILINE)
    if match:
        return match.group(1).strip()
    return os.path.splitext(os.path.basename(relative))[0]


def _relative(full_path):
    return full_path.replace(os.sep, "/")


def _now():
    return datetime.now(UTC).isoformat()


def _fail(code, message):
    print(message, file=sys.stderr)
    return code

if __name__ == "__main__":
    sys.exit(main())
