# Quickstart: Validating the Publishing Pipeline End-to-End

Validation scenarios that prove the spec's success criteria without reading implementation.
Implementation lives in tasks.md and the code; this guide only runs the finished pipeline.

## Prerequisites

- Python 3.11+ available locally and on the CI runner
- A Telegram test bot (token) whose bot is an admin of a test channel; channel id available
- Credentials available as environment variables (never in files): `TELEGRAM_BOT_TOKEN`,
  `TELEGRAM_CHAT_ID` (see contracts/pipeline-interface.md)

## Scenario 1 - A new post gets published (US1, SC-001, SC-004)

1. Create `posts/hello-devops.md` with a heading, a paragraph, a code block, and a link.
2. `python -m pipeline.main --dry-run` -> summary lists the post as pending; nothing sent.
3. `python -m pipeline.main` -> exit 0; post appears in the test channel with preserved
   formatting; `delivery/ledger.json` contains a new record for the post.

## Scenario 2 - Re-runs never duplicate (US3, SC-003)

1. Run `python -m pipeline.main` again immediately -> exit 0, log says nothing to publish,
   no new channel message.
2. Inspect the ledger: unchanged (or no new entries).

## Scenario 3 - Failure visibility (US2, SC-002)

1. Unset `TELEGRAM_BOT_TOKEN`, run -> exit 10; log names the missing variable; nothing sent.
2. Set an invalid token, run -> exit 30 after the bounded attempts; log names the post and
   the final error; no partial silent state.
3. Add `posts/broken.md` with empty body, run -> exit 20; log names the file.

## Scenario 4 - Multi-part and multi-post behavior (FR-010, R6)

1. Add a post longer than 4096 characters -> delivered as ordered parts with Part N/M markers.
2. Add two new posts in one commit -> both delivered in one run, alphabetical order, with
   visible spacing between messages.
3. Interrupt a multi-part delivery (invalid token after first part), fix the token, re-run ->
   only the remaining parts are sent; no duplicated parts.

## Scenario 5 - CI end-to-end (SC-005 portability rehearsal)

1. Push a new post to the default branch -> CI workflow runs automatically and publishes.
2. Confirm the run summary in the CI log answers: what was considered, delivered, skipped,
   failed (SC-006).
3. Simulate migration rehearsal: run the same entry point with the same env variables in a
   different runner (locally or another CI) -> identical behavior with only secret re-entry.

## Expected outcomes at a glance

| Scenario | Expected result |
|----------|-----------------|
| 1 | post in channel, exit 0, ledger updated |
| 2 | exit 0, nothing to publish, no duplicates |
| 3 | exits 10 / 30 / 20 with named causes |
| 4 | ordered parts; all posts of a commit delivered |
| 5 | CI publishes on push; logs sufficient without re-runs |
