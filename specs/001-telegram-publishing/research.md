# Phase 0 Research: Markdown-to-Telegram Publishing Pipeline

Decisions below resolve every NEEDS CLARIFICATION, including the ambiguities left open when
the clarification session was closed early.

## R1. Implementation language

**Decision**: Python 3.11+ as a single command-line program.

**Rationale**: readable, testable with pytest (constitution Principle III), excellent minimal
libraries for frontmatter parsing, Markdown conversion, and HTTP; runs unchanged on GitHub
and GitLab runners.

**Alternatives considered**: Bash + curl (conversion and splitting logic becomes unmaintainable);
Node.js (equally viable, Python preferred for simplicity of a single-package layout); Go
(compilation step adds machinery without benefit at this scale).

## R2. CI wrappers

**Decision**: GitHub Actions workflow now; `.gitlab-ci.yml` added at migration time. Both
wrappers only check out the repository, map secrets to environment variables, and run
`python -m pipeline.main`.

**Rationale**: keeps every platform-specific detail inside a thin wrapper (constitution
Principle VII); the pipeline core never imports CI-platform features.

**Alternatives considered**: container-based jobs (most portable, rejected for v1 simplicity;
revisit if runner environments drift).

## R3. What counts as a post

**Decision**: every `.md` file under `posts/` is a post; other Markdown files (README, specs)
are never published.

**Rationale**: deterministic directory rule, zero per-file maintenance, excludes non-post
files by construction.

**Alternatives considered**: all `.md` files in the repo (would publish README - dangerous);
frontmatter opt-in flag (extra per-file work, easy to forget, silently skips posts).

## R4. Duplicate prevention / delivery state

**Decision**: pipeline maintains `delivery/ledger.json` in the repository and commits it back
after each successful delivery. The CI wrapper skips triggering a new publishing run when a
push touches only `delivery/` (loop guard).

**Rationale**: durable, human-readable, survives CI platform migration (no dependence on CI
artifact retention), and keeps a single source of truth for delivery state (constitution
Principle II).

**Alternatives considered**: CI run artifacts (expire and differ per platform - violates
portability); published flags written into post files (churns content files, same commit-back
need with worse diffs).

## R5. Post identity

**Decision**: the repository-relative file path is the identity used in the ledger.

**Rationale**: simplest stable key for v1; no required frontmatter.

**Alternatives considered**: frontmatter slug (better rename behavior - deferred as a future
enhancement); content hash (any edit would look like a new post - wrong semantics).

**Known limitation (v1, documented)**: renaming a post makes it look new; the old path's
ledger entry remains but never matches again.

## R6. Multiple new posts in one commit

**Decision**: one run publishes ALL new posts, in deterministic alphabetical order by path,
with at least 2 seconds between consecutive channel messages.

**Rationale**: matches user expectation that a commit containing several posts publishes all
of them; pacing respects Telegram rate limits (roughly 1 message/second per chat and about
20 messages/minute per group/channel).

**Alternatives considered**: one post per run (slower, surprise factor); newest-only (loses
content).

## R7. Telegram API failure and retry policy

**Decision**: per message, up to 3 attempts with exponential backoff (2s/4s/8s) and honoring
HTTP 429 `Retry-After` when present; if the final attempt fails, the run exits non-zero.
Already-delivered parts of a multi-part post stay in the channel; the next run delivers only
the remainder (ledger records per-message progress).

**Rationale**: transient blips should not page a human, while persistent failures still fail
CI per spec FR-007.

**Alternatives considered**: no retry (false alarms on transient errors); unlimited retry
(cannot guarantee "CI must fail when publishing fails").

## R8. Formatting conversion and message size

**Decision**: convert Markdown to the Telegram HTML subset (`b`, `i`, `u`, `s`, `code`,
`pre`, `a`); unsupported constructs degrade to plain text. Messages are limited to 4096
characters (Telegram Bot API limit); longer posts split at block boundaries with `Part N/M`
markers.

**Rationale**: implements spec FR-004/FR-010 and the graceful-degradation edge case; 4096 is
a platform constant, tested at boundary via fixtures.

**Alternatives considered**: MarkdownV2 parse mode (strict escaping causes frequent 400
errors); raw text only (loses required formatting preservation).

## R9. Credential configuration across CI platforms

**Decision**: the pipeline consumes exactly two environment variables - `TELEGRAM_BOT_TOKEN`
(secret) and `TELEGRAM_CHAT_ID` (configuration), no defaults in code. The GitHub wrapper maps
Actions secrets to these names; the future GitLab wrapper maps masked CI/CD variables to the
same names.

**Rationale**: a fixed env contract is the platform-neutral seam (spec FR-006/FR-011,
constitution Principles VI and VII); re-hosting then requires only secret re-entry (SC-005).

**Alternatives considered**: per-platform config files (couples core to platforms); optional
CLI flags for tokens (invites leaking secrets into logs).
