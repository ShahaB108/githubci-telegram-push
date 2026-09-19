# Tasks: Markdown-to-Telegram Publishing Pipeline

**Input**: Design documents from `specs/001-telegram-publishing/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md,
data-model.md, contracts/pipeline-interface.md, quickstart.md

**Tests**: INCLUDED - constitution Principle III (Test-First, NON-NEGOTIABLE) mandates
failing tests before implementation; every story phase lists tests first.

**Organization**: Tasks are grouped by user story to enable independent implementation and
testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project (CLI automation tool)**: `pipeline/` package, `tests/` at repository root,
  content in `posts/`, delivery state in `delivery/ledger.json` (per plan.md structure)

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create project scaffolding per plan.md: `pipeline/__init__.py`, `tests/unit/`,
      `tests/contract/`, `tests/integration/` (each with empty `__init__.py` or as pytest
      rootdir dirs), `posts/.gitkeep`, `delivery/.gitkeep`
- [x] T002 [P] Add dependency manifests: `requirements.txt` (PyYAML, Markdown, requests - the
      three direct dependencies from plan.md) and `requirements-dev.txt` (pytest, ruff)
- [x] T003 [P] Configure pytest in `pytest.ini`: testpaths `tests`, python_files `test_*.py`,
      addopts `-q`

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T004 [P] Implement environment configuration in `pipeline/config.py` per
      contracts/pipeline-interface.md: read TELEGRAM_BOT_TOKEN (secret, required, no default,
      never logged), TELEGRAM_CHAT_ID (required), PIPELINE_POSTS_DIR (default `posts`),
      PIPELINE_LEDGER_PATH (default `delivery/ledger.json`); configuration comes ONLY from
      the environment
- [x] T005 [P] Implement ledger store in `pipeline/ledger.py` per data-model.md: schema
      version 1; each record has post_path (unique per record), delivered_at (ISO 8601 UTC),
      message_ids (list of int), status enum `delivered` or `partial`; load/save with atomic
      write; provide lookup by post_path

## Phase 3: User Story 1 - New Post Is Published Automatically (Priority: P1) 🎯 MVP

**Goal**: adding a Markdown file under `posts/` and running the pipeline delivers it to the
configured Telegram channel and records it in the ledger.

**Independent Test**: add one post, run `python -m pipeline.main`, verify the channel message
and exit 0 (quickstart.md Scenario 1).

### Tests for User Story 1 (write first - they MUST fail before implementation)

- [x] T006 [P] [US1] Write failing unit tests for Markdown conversion in
      `tests/unit/test_convert.py`: title/headings/emphasis/links/code preserved as Telegram
      HTML (`b`, `i`, `u`, `s`, `code`, `pre`, `a`); unsupported constructs degrade to plain
      text without failing (spec FR-004)
- [x] T007 [P] [US1] Write failing unit tests for message splitting in
      `tests/unit/test_splitting.py`: posts over 4096 characters split at block boundaries
      into ordered parts with `Part N/M` markers; no part exceeds the limit (spec FR-010)
- [x] T008 [P] [US1] Write failing unit tests for detection in `tests/unit/test_detect.py`:
      only `.md` files under `posts/` are posts; new (unrecorded) posts detected;
      already-delivered paths skipped; `draft: true` frontmatter excluded; per data-model.md
      the body MUST be non-empty after frontmatter is stripped (spec FR-001, FR-002)
- [x] T009 [P] [US1] Write failing contract tests in `tests/contract/test_publish_cli.py`:
      happy-path run exits 0 with Telegram mocked and ledger updated; `--dry-run` prints the
      plan and writes nothing; stdout contains the run summary (posts considered, delivered,
      skipped, failed) per contracts/pipeline-interface.md

### Implementation for User Story 1

- [x] T010 [P] [US1] Implement `pipeline/convert.py`: Markdown to Telegram HTML conversion
      and 4096-character block-boundary splitting with part markers (satisfies T006, T007)
- [x] T011 [P] [US1] Implement `pipeline/detect.py`: scan `PIPELINE_POSTS_DIR` for `.md`
      files, apply draft/exclusion and empty-body rules, diff against the ledger via
      `pipeline/ledger.py` (satisfies T008; depends on T005)
- [x] T012 [US1] Implement `pipeline/deliver.py`: send each part via Telegram sendMessage
      with `parse_mode=HTML` and `disable_web_page_preview`, pacing at least 2 seconds
      between consecutive channel messages (FR-003); single attempt in this story
      (depends on T004, T010)
- [x] T013 [US1] Implement `pipeline/main.py` orchestration: detect -> convert -> deliver ->
      record; support `--dry-run` and `--limit N`; print per-run summary to stdout;
      verify T006-T009 pass (depends on T004, T005, T010-T012)

## Phase 4: User Story 2 - Publishing Failure Fails CI Loudly (Priority: P2)

**Goal**: every delivery failure produces a non-zero exit and a log entry naming the post
and reason; credentials problems fail fast before anything is sent.

**Independent Test**: inject each failure condition (missing secret, invalid token, malformed
post, unreachable service) and verify failing runs with named causes (quickstart.md Scenario 3).

### Tests for User Story 2 (write first - they MUST fail before implementation)

- [x] T014 [P] [US2] Write failing unit tests for bounded retry in `tests/unit/test_retry.py`:
      up to 3 attempts per message, backoff 2s/4s/8s, HTTP 429 honors `Retry-After`, final
      failure propagates (spec FR-007, research R7)
- [x] T015 [P] [US2] Write failing contract tests for failure modes in
      `tests/contract/test_failure_exit_codes.py`: exit 10 missing/invalid credential with
      fail-fast before any delivery; exit 20 malformed post (metadata parse or empty body)
      naming the file; exit 30 delivery failure after retries naming post, attempt count,
      error; exit 40 ledger I/O failure; secrets never appear in stdout or stderr
      (contracts/pipeline-interface.md exit-code table)

### Implementation for User Story 2

- [x] T016 [P] [US2] Add bounded retry with backoff and `Retry-After` handling to
      `pipeline/deliver.py` (satisfies T014; depends on T012)
- [x] T017 [US2] Implement failure paths in `pipeline/main.py` and `pipeline/config.py`:
      fail-fast credential validation, malformed-post detection, exit codes 10/20/30/40,
      error details to stderr, per-post outcome lines in the summary (satisfies T015;
      depends on T013, T016)

## Phase 5: User Story 3 - Only New Posts Are Published (Priority: P3)

**Goal**: repeat runs never duplicate content; nothing-to-publish runs succeed with an
explanatory log; the pipeline commits ledger updates back to the repository.

**Independent Test**: run the pipeline twice on identical content; the second run delivers
nothing new and exits 0 (quickstart.md Scenario 2).

### Tests for User Story 3 (write first - they MUST fail before implementation)

- [x] T018 [P] [US3] Write failing unit tests for idempotency in
      `tests/unit/test_idempotency.py`: already-delivered post skipped; run with nothing new
      reports success; a `partial` record resumes only the remaining parts of a multi-part
      post (spec FR-009, data-model.md status enum `delivered` or `partial`)
- [x] T019 [P] [US3] Write failing contract tests in `tests/contract/test_ledger_commit.py`:
      ledger changes are committed with message prefix `chore(delivery):` per
      contracts/pipeline-interface.md; second run on unchanged content exits 0 with no sends
      and logs nothing-to-publish (spec FR-006/FR-009)

### Implementation for User Story 3

- [x] T020 [US3] Implement ledger commit-back, delivered-post skip, and partial-resume logic
      in `pipeline/main.py` and `pipeline/ledger.py`: commit only `delivery/ledger.json` with
      the `chore(delivery):` prefix after runs that changed state; skip publishing when a
      push touches only `delivery/` (loop guard); verify T018 and T019 pass (depends on
      T013, T017)

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T021 [P] Create `.github/workflows/publish.yml`: trigger on push to `main` touching
      `posts/**` plus `workflow_dispatch`; ignore `delivery/**` pushes (loop guard);
      concurrency group per channel so overlapping runs serialize (FR-012); map repository
      secrets TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to environment variables only; jobs:
      quality gate (ruff lint + pytest) then publish via `python -m pipeline.main`
- [x] T022 [P] Create `README.md` publishing section: how to add a post, required secrets and
      environment variables, local runs with `--dry-run`, exit-code table (reference
      specs/001-telegram-publishing/contracts/pipeline-interface.md)
- [x] T023 [P] Add `ruff.toml` configuration and fix all lint findings in `pipeline/` and
      `tests/` (constitution Principle IV)
- [x] T024 Run the full pytest suite and ruff until green, then walk the quickstart.md
- [x] T025 [P] Add env-gated integration smoke test in `tests/integration/test_live.py`: a real single-message delivery against the test channel, skipped when TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID are absent (remediation F1)
      validation scenarios 1-4 (dry-run, publish, duplicate suppression, failure drills) and
      record results

## Dependencies

**Story completion order**: Setup (T001-T003) -> Foundational (T004-T005) -> US1 (T006-T013,
MVP) -> US2 (T014-T017) -> US3 (T018-T020) -> Polish (T021-T024).

- US1 depends on Foundational (config, ledger).
- US2 extends `pipeline/deliver.py` and `pipeline/main.py` created in US1.
- US3 extends `pipeline/main.py` and `pipeline/ledger.py` from US1/US2.
- Polish requires all stories complete (CI workflow runs the whole pipeline).

## Parallel Execution Examples

- Foundational: T004 and T005 touch different files - run in parallel.
- US1 tests: T006, T007, T008, T009 are separate test files - write in parallel.
- US1 implementation: T010 and T011 are independent modules - parallel; T012 then T013 are
  sequential.
- US2 tests: T014 and T015 in parallel; T016 parallel with nothing else in flight except
  test authoring.
- US3 tests: T018 and T019 in parallel.
- Polish: T021, T022, T023 all touch different files - run in parallel; T024 last.

## Implementation Strategy

- **MVP first**: complete Setup + Foundational + US1 (T001-T013). That alone satisfies the
  core value: a new post reaches Telegram automatically, with tests proving it.
  CAVEAT: do not enable unattended CI before T020 (ledger commit-back) - until then the
  pipeline cannot remember deliveries across CI runs and would re-publish everything.
- **Incremental delivery**: after US1 the pipeline is demonstrable; US2 adds operational
  trust (loud failures), US3 adds duplicate safety and unattended ledger bookkeeping.
- **Test-first discipline** (constitution Principle III): every story phase lists its failing
  tests before implementation tasks; run them, watch them fail, then implement.
- Verify each story against its quickstart.md scenario before moving to the next phase.
