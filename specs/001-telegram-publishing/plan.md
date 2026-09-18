# Implementation Plan: Markdown-to-Telegram Publishing Pipeline

**Branch**: `001-telegram-publishing` | **Date**: 2026-09-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-telegram-publishing/spec.md`

**Note**: The clarification session was closed early (no answers recorded); every pending
ambiguity is resolved as an explicit Decision in [research.md](./research.md) with rationale
and rejected alternatives.

## Summary

Publish newly added Markdown posts (files under `posts/` reaching the default branch) to a
configured Telegram channel via a Telegram bot. A repository-committed delivery ledger
distinguishes new posts from already-delivered ones; any publishing failure fails CI with a
non-zero exit code and per-post log entries. The pipeline is a small platform-neutral
command-line program wrapped by thin CI jobs (GitHub Actions now, self-hosted GitLab after
migration).

## Technical Context

**Language/Version**: Python 3.11+ (decision R1 in research.md)

**Primary Dependencies**: PyYAML (frontmatter), Markdown (HTML conversion), requests (Telegram
HTTP client) - three direct dependencies, no framework.

**Storage**: none beyond repository files and the committed delivery ledger (`delivery/ledger.json`)

**Testing**: pytest (unit + contract + integration suites)

**Target Platform**: CI runners (GitHub Actions ubuntu-latest now; GitLab runners after migration)

**Project Type**: cli (CI automation tool)

**Performance Goals**: a publishing run completes within 2 minutes for typical batches (up to
10 posts); each channel message paced to respect Telegram rate limits.

**Constraints**: platform-neutral core (no CI-platform-exclusive APIs inside the pipeline);
credentials supplied only via environment; Telegram per-message limit is 4096 characters.

**Scale/Scope**: one channel, one bot, human-authored post volume; v1 scope per spec
(Telegram only, no re-publish on edits, no scheduled publishing).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution item (v1.1.0) | Status | Evidence |
|---------------------------|--------|----------|
| I. Specification-Driven Delivery | PASS | plan derives entirely from specs/001-telegram-publishing/spec.md |
| II. Single Source of Truth | PASS | posts/ is canonical content; ledger.json is the single delivery record |
| III. Test-First Development | PASS (gated) | tasks.md MUST sequence failing tests before implementation (verified post-Phase 1) |
| IV. Quality Gates via Automation | PASS (gated) | lint + pytest required in CI before merge |
| V. Simplicity and Evolvability | PASS | one small program, three direct dependencies, no framework |
| VI. Secrets Never in Source | PASS | env-only credential contract (contracts/pipeline-interface.md) |
| VII. Reproducible, Portable Pipelines | PASS | platform-neutral core; CI wrappers isolated; GitLab parity via same entry point |
| Data & Content Standards | PASS | Markdown + frontmatter metadata under posts/ |
| Development Workflow & Delivery Scope | PASS | Telegram only; delivery failures visible via exit codes + logs |

**Post-Phase 1 re-check**: design adds no new dependencies beyond the three above, no extra
storage systems, and no platform coupling -> all gates remain PASS.

## Project Structure

### Documentation (this feature)

```text
specs/001-telegram-publishing/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── pipeline-interface.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created here)
```

### Source Code (repository root)

```text
posts/                        # Markdown posts - the only source content that gets published
delivery/
└── ledger.json               # delivery records committed back by the pipeline
pipeline/                     # platform-neutral publishing program
├── __init__.py
├── main.py                   # CLI entry point: detect -> convert -> deliver -> record
├── config.py                 # env-var configuration (no defaults for secrets)
├── detect.py                 # new-post detection against the ledger
├── convert.py                # Markdown -> Telegram HTML; 4096-character splitting
├── deliver.py                # Telegram sendMessage client with bounded retry + pacing
└── ledger.py                 # delivery-record load/update/commit
.github/
└── workflows/publish.yml     # GitHub Actions wrapper (current CI)
.gitlab-ci.yml                # GitLab wrapper - added at migration time (not now)
tests/
├── unit/                     # conversion, detection, splitting, ledger logic
├── contract/                 # env-var contract, exit codes, ledger schema
└── integration/              # end-to-end against the Telegram test channel (opt-in)
```

**Structure Decision**: single project (CLI automation tool). The platform-neutral
`pipeline/` package contains all logic; CI wrappers only check out the repo, map secrets to
environment variables, and invoke `python -m pipeline.main`.

## Complexity Tracking

No constitution violations; table intentionally empty.
