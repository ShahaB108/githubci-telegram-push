# Feature Specification: Markdown-to-Telegram Publishing Pipeline

**Feature Branch**: `001-telegram-publishing`

**Created**: 2026-09-18

**Status**: Draft

**Input**: User description: "Build the first version of an automated Markdown-to-Telegram
publishing pipeline. This is currently a test repository; later it will be migrated to the
DevOps Farsi organization's self-hosted GitLab, so the implementation should avoid depending
on GitHub-specific features. Whenever a new Markdown post is added to the repository, the CI
pipeline should detect it and automatically publish the post to a configured Telegram channel
using a Telegram bot. Markdown files represent posts. Telegram credentials must be provided
through CI/CD secrets/environment variables; no token or chat ID may be committed. CI must
fail when publishing fails, and the workflow should provide useful logs. The first version
only needs Telegram publishing; LinkedIn is out of scope. Do not over-engineer, and do not
choose the implementation language or CI syntax yet."

## Clarifications

### Session 2026-09-18

- Q: Which Markdown files should the pipeline treat as publishable posts? → A: Only .md files under a dedicated posts directory (posts/); files elsewhere are never published.
- Q: Where should the pipeline record which posts have already been delivered, so that repeat runs never publish duplicates? → A: A ledger file in the repository (delivery/ledger.json), committed back by the pipeline after each run.
- Q: What should identify a post in the delivery ledger, so the pipeline can tell new posts apart from already-delivered ones? → A: The repository-relative file path; renaming a post makes it look new (documented v1 limitation).
- Q: When a single commit adds several new Markdown posts, what should one pipeline run publish? → A: All new posts in the run, alphabetical by file path, with spacing between messages.
- Q: When the Telegram service temporarily fails mid-delivery, how should the pipeline handle retries before it gives up and fails the CI run? → A: Bounded retry, up to 3 attempts per message with increasing waits; the run still fails if delivery never succeeds.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - New Post Is Published Automatically (Priority: P1)

A content author adds a new Markdown post to the default branch of the repository. The CI
pipeline runs on its own, detects the new post, converts it into a readable channel message,
and delivers it to the configured Telegram channel through the configured bot - with no
manual publishing steps for the author.

**Why this priority**: this is the core value of the feature - Markdown content reaching the
Telegram audience automatically.

**Independent Test**: can be fully tested by adding one Markdown post, letting the pipeline
run, and verifying the post appears in the channel and the run exits successfully.

**Acceptance Scenarios**:

1. **Given** a new Markdown post with valid content on the default branch, **When** the
   publishing pipeline runs, **Then** the post is delivered to the configured Telegram
   channel as a readable message (title, headings, emphasis, links, and code preserved as
   far as the platform supports) and the run exits with success.
2. **Given** a post whose text exceeds the platform's single-message limit, **When** the
   pipeline delivers it, **Then** the post arrives as sequential ordered parts (part markers
   included) and the run exits with success.

---

### User Story 2 - Publishing Failure Fails CI Loudly (Priority: P2)

A maintainer must be able to trust that "no failure signal means delivered". Whenever a
publishing attempt fails - missing or invalid credentials, unreachable Telegram service,
rejected message, malformed post - the CI run itself fails: non-zero exit code plus a useful
log entry naming the affected post and the reason.

**Why this priority**: the user explicitly requires CI to fail when publishing fails; silent
failure would make the whole pipeline untrustworthy.

**Independent Test**: can be fully tested by injecting each failure condition and verifying
that every one produces a failing run with a log entry identifying the post and the reason.

**Acceptance Scenarios**:

1. **Given** the bot token or chat ID is missing or invalid, **When** the pipeline runs,
   **Then** it fails fast before delivering anything, exits non-zero, and the log names the
   missing or invalid configuration.
2. **Given** a post that cannot be parsed (malformed metadata or empty body), **When** the
   pipeline runs, **Then** the run exits non-zero and the log identifies the offending file
   and the problem.
3. **Given** the Telegram service is unreachable mid-run, **When** the delivery fails,
   **Then** the run exits non-zero, already-delivered parts remain in the channel, and the
   log states where delivery stopped.

---

### User Story 3 - Only New Posts Are Published (Priority: P3)

A maintainer re-runs the pipeline (manually, or because a merge touched multiple files).
Posts that were already delivered must not be sent again; a run with nothing new to publish
completes successfully and says so.

**Why this priority**: the requirement is to detect *newly added* posts - repeat runs must
never spam the channel - but this only matters once publishing (P1) and failure visibility
(P2) exist.

**Independent Test**: can be fully tested by running the pipeline twice on identical content
and verifying the second run delivers nothing new and still exits with success.

**Acceptance Scenarios**:

1. **Given** a post that was already delivered in a previous run, **When** the pipeline runs
   again, **Then** no duplicate post appears in the channel and the run exits with success.
2. **Given** a run where no new post is due for delivery, **When** the pipeline runs, **Then**
   it exits with success and logs that there was nothing to publish.

---

### Edge Cases

- What happens when the bot token or chat ID is missing, expired, or invalid? -> fail fast,
  exit non-zero, nothing delivered (User Story 2).
- What happens when a post exceeds the single-message length limit? -> delivered as ordered
  parts; silent truncation is forbidden.
- What happens when two runs overlap or run concurrently? -> runs must effectively serialize
  per channel so no duplicate posts are produced.
- What happens when a post has valid metadata but an empty body? -> treated as a malformed
  post: run fails and names the file.
- What happens when formatting cannot be represented on the platform? -> degrade gracefully
  to the closest supported representation; do not fail delivery for formatting alone.
- What happens when a new post is added on a branch other than the default branch? -> not
  published; publishing happens only from the default branch.
- What happens when an already-published post is edited? -> not re-published in this version
  (documented scope; re-publishing on edits is a future extension).
- What happens when the pipeline commits the ledger update itself? -> the resulting push MUST
  NOT trigger another publishing run; ledger-only changes are skipped.
- What happens when an already-delivered post is renamed or moved? -> it is treated as a new
  post and published again (documented v1 limitation; a stable frontmatter identity is a
  future enhancement).
- What happens when a message is still undelivered after all retry attempts? -> the run
  fails with the post named in the log; the next run delivers only what is still missing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The pipeline MUST treat Markdown files under the `posts/` directory as posts;
  files elsewhere (for example README, specs) MUST NOT be published.
- **FR-002**: The pipeline MUST detect newly added posts that reach the default branch and
  distinguish them from posts that were already delivered; a post is identified by its
  repository-relative file path, so renaming a post makes it appear new (documented v1
  limitation).
- **FR-003**: A newly added post MUST trigger the publishing workflow automatically; manual
  triggering MUST also be supported with identical behavior. A run MUST publish ALL new
  posts in one pass, in ascending alphabetical order by file path, with at least 2 seconds
  between consecutive channel messages.
- **FR-004**: The pipeline MUST convert each post's Markdown into a channel message that
  preserves title, headings, emphasis, links, and code formatting as far as the platform
  supports.
- **FR-005**: The pipeline MUST send the post content to the configured Telegram channel
  using the configured Telegram bot.
- **FR-006**: All Telegram credentials (bot token and chat/channel identifier) MUST be
  provided exclusively through CI/CD secrets or environment variables; no token or chat ID
  MAY be committed to the repository, and the pipeline MUST fail fast before delivering
  anything if a required credential is missing or invalid.
- **FR-007**: The pipeline MUST retry a failed message delivery up to 3 attempts per message
  with increasing waits, honoring any retry-after hint from the service; if delivery still
  fails, the pipeline MUST exit non-zero with a log entry naming the affected post, the
  attempt count, and the failure reason; silent or partial delivery MUST NOT occur without
  a failure signal.
- **FR-008**: The workflow MUST provide useful logs: a per-run summary (posts considered,
  delivered, skipped, failed) and a per-post outcome entry.
- **FR-009**: Publishing MUST be idempotent: delivery state is kept in the committed ledger
  file `delivery/ledger.json`; already-delivered posts MUST NOT be sent again, a run with
  nothing new to publish MUST exit successfully with an explanatory log line, and edits to
  already-published posts MUST NOT trigger re-publishing in this version.
- **FR-010**: Posts longer than the platform's single-message limit MUST be delivered as
  ordered sequential parts; a post that cannot be delivered MUST fail the run with a clear
  error rather than be truncated silently.
- **FR-011**: The pipeline MUST NOT depend on features exclusive to one CI platform; it MUST
  be reproducible and runnable on the organization's self-hosted GitLab after migration,
  with re-hosting requiring only configuration and secret re-entry.
- **FR-012**: Overlapping runs MUST NOT produce duplicate posts; delivery per channel MUST
  effectively serialize.

### Key Entities *(include if feature involves data)*

- **Markdown Post**: a content file (with optional per-file metadata) and its body; the unit
  of publishing, identified by its repository-relative file path.
- **Publishing Channel**: the target Telegram channel and its linked bot identity;
  configured once, outside the repository.
- **Delivery Record**: the recorded evidence that a post was delivered, kept in the committed
  ledger file `delivery/ledger.json`; used to distinguish new posts from already-delivered
  ones.
- **Delivery Run**: one pipeline execution - trigger source (automatic or manual), posts
  considered, per-post outcomes (delivered / skipped / failed), and overall exit status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A newly added post appears in the Telegram channel within 5 minutes of the
  publishing run starting, in at least 95% of runs.
- **SC-002**: 100% of injected publishing failures (missing credential, unreachable service,
  malformed post) produce a non-zero exit code and a log entry naming the post and reason.
- **SC-003**: Re-running the pipeline on unchanged content produces zero duplicate posts in
  100% of runs.
- **SC-004**: An author publishes a post by adding a single Markdown file to the default
  branch, with no other manual steps required.
- **SC-005**: Moving the pipeline to the organization's self-hosted GitLab requires only
  re-entering configuration and secrets and reproduces identical behavior; target: under one
  working day.
- **SC-006**: A maintainer can determine a run's outcome (what was delivered, skipped, or
  failed, and why) from the logs alone, in under one minute, without re-running anything.
- **SC-007**: Zero silent-failure incidents (deliveries that failed without a failing run
  signal) during the first month of operation.

## Assumptions

- This is currently a test repository: validation happens against a test Telegram channel
  and bot before the production DevOps Farsi channel is configured; the channel and bot
  identity are configured once through CI/CD secrets and variables.
- The repository will migrate to the DevOps Farsi organization's self-hosted GitLab; the
  design avoids CI-platform-exclusive features accordingly.
- The default branch is `main`; publishing triggers when new posts reach `main`, plus manual
  runs. Scheduled or queued publishing is out of scope for the first version.
- Only newly added posts are published in this version; re-publishing on edits to
  already-published posts is a future extension.
- Content selection: Markdown posts under `posts/` that are not yet recorded in the committed
  ledger file `delivery/ledger.json` get published, so behavior is identical on any supported
  CI platform.
- Content language is Persian (Farsi); right-to-left rendering is the Telegram client's
  responsibility - the pipeline preserves text and formatting semantics only.
- The implementation language and CI workflow syntax are deliberately NOT chosen here; that
  selection happens in the planning phase, honoring the instruction to keep this
  specification technology-agnostic.
- Simplicity governs scope: the first version implements the simplest behavior that satisfies
  the requirements above; LinkedIn and all other publishing channels are explicitly out of
  scope.
