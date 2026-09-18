# Data Model: Markdown-to-Telegram Publishing Pipeline

## Entities

### Markdown Post

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| path | string (repo-relative) | yes | identity key (decision R5); MUST be under posts/ |
| frontmatter.title | string | no | falls back to first H1 or file name |
| frontmatter.tags | list[string] | no | reserved for future use |
| frontmatter.draft | boolean | no | true excludes the post from publishing |
| body | string | yes | MUST be non-empty; empty body = malformed post (exit 20) |

Validation rules: file MUST have `.md` extension and live under posts/; body MUST be
non-empty after frontmatter is stripped.

### Delivery Record

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| post_path | string | yes | unique per record; matches post identity |
| delivered_at | string (ISO 8601 UTC) | yes | timestamp of final successful part |
| message_ids | list[int] | yes | one Telegram message id per delivered part (progress tracking) |
| status | enum | yes | "delivered" or "partial" (multi-part post with remaining parts) |

### Ledger

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| version | integer | yes | schema version, starts at 1 |
| records | list[Delivery Record] | yes | zero or more; unique post_path |

Stored at `delivery/ledger.json`; committed back by the pipeline after each run that changed
it. Human-readable (indented) so maintainers can inspect delivery state directly.

### Delivery Run

| Field | Type | Notes |
|-------|------|-------|
| trigger | enum | "push" (default branch) or "manual" |
| before_sha / after_sha | string | commit range evaluated |
| considered | list[string] | post paths examined |
| delivered / skipped / failed | list[string] | per-run outcome lists (also emitted in the summary log) |
| exit_status | integer | 0 or the failure code (see contracts/pipeline-interface.md) |

## State Transitions

- Post: new (no record) -> detected (in run's considered list) -> delivered (record added)
- Multi-part post: -> partially delivered (record with status "partial" + message_ids) ->
  delivered (record completed on a later run)
- Failed delivery: NO record change -> post stays "new" -> next run retries it
- Run: started -> succeeded (exit 0, includes nothing-to-publish) or failed (exit 10/20/30/40)

## Relationships

- Ledger has many Delivery Records; each Delivery Record references exactly one Post by path.
- A Delivery Run consumes Posts and produces/updates Delivery Records and the run summary log.
