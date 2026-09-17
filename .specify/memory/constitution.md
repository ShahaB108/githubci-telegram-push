<!--
## Sync Impact Report
- Version change: 1.0.0 -> 1.1.0
- Bump rationale: MINOR - two new principles added and materially expanded delivery guidance;
  no principle was removed or incompatibly redefined.
- Modified principles: none renamed; Principles I-V unchanged
- Added principles: VI. Secrets Never in Source (NON-NEGOTIABLE); VII. Reproducible, Portable
  Delivery Pipelines
- Added sections: none (template structure preserved)
- Modified sections: Data & Content Standards (Markdown-source delivery rule added);
  Development Workflow renamed to Development Workflow & Delivery Scope (delivery-failure
  visibility and channel-scope rules added)
- Removed sections: none
- Project identity note: this repository is the DevOps Farsi content automation hub; Markdown
  files are the source content published to delivery channels (Telegram first, LinkedIn later).
- Deferred TODOs: none
- Review note: this report is temporary scratch material for the amendment review and MUST be
  removed before the amended constitution is committed.
-->

# Knowledge Hub Constitution

## Core Principles

### I. Specification-Driven Delivery (NON-NEGOTIABLE)

Every feature MUST begin as a numbered specification under `specs/` and progress through the
Spec Kit flow (specify -> clarify -> plan -> tasks -> implement). Implementation work MUST NOT
start without an approved spec, and shipped behavior MUST trace back to spec requirements.

Rationale: intent-to-code traceability and consistent use of the toolchain already installed in
this repository (Spec Kit 1.0.8, Cline integration).

### II. Single Source of Truth

Every knowledge artifact MUST have exactly one canonical location. Duplicates MUST be expressed
as links or redirects, never as copies. Each artifact MUST carry provenance metadata (origin,
author or collector, capture date). Broken internal links are defects and MUST be fixed with
the same urgency as a failing test.

Rationale: a knowledge hub that cannot be trusted to be current and non-redundant loses its
core value.

### III. Test-First Development (NON-NEGOTIABLE)

Tests MUST be written first and observed to fail before implementation begins; development
follows the red-green-refactor cycle. Every defect fix MUST include a regression test that
fails without the fix and passes with it. Ingestion, search, and linking behavior MUST be
covered by contract or integration tests.

Rationale: tests encode intended behavior and prevent regression-prone rewrites of
content-processing logic.

### IV. Quality Gates Enforced by Automation

Every change MUST pass linting, type checks, the full test suite, and content link-integrity
checks before merge. The CI pipeline MUST be the single authority for merge eligibility;
failing gates block merges. Manual overrides MUST NOT exist; exceptions require a documented
waiver in the pull request that names the specific gate and reason.

Rationale: automation applies repeatable checks uniformly and keeps the quality bar identical
for all contributors.

### V. Simplicity and Evolvability

Implementations MUST start with the simplest design that satisfies the current spec (YAGNI).
Every abstraction, dependency, or schema extension MUST be justified in the plan. Breaking
changes to stored content formats or public interfaces MUST ship with a versioned migration
path and a changelog entry.

Rationale: unbounded complexity is the primary long-term threat to a content system.

### VI. Secrets Never in Source (NON-NEGOTIABLE)

Secrets (tokens, credentials, private keys) MUST NEVER be committed to the repository. Pipelines
MUST consume credentials exclusively through CI-provided secret storage or environment
injection. A secret that reaches repository history is an incident: it MUST be rotated and
removed.

Rationale: this repository fronts public delivery channels; leaked credentials compromise the
channels and the audience's trust.

### VII. Reproducible, Portable Delivery Pipelines

CI/CD pipelines MUST be reproducible and easy to run on self-hosted GitLab later, and MUST
remain portable between GitHub and GitLab as much as practical. Pipeline definitions MUST avoid
platform-specific hard-coding where an equivalent portable alternative exists; any unavoidable
platform-specific step MUST be isolated and documented.

Rationale: hosting independence protects content delivery from platform churn and vendor
lock-in.

## Data & Content Standards

- Source content: Markdown files are the sole source content for delivery; the publishing
  pipeline MUST consume them directly, with per-file metadata (frontmatter) driving publishing
  behavior.
- Canonical format: plain-text first. Knowledge content MUST be stored in Markdown with YAML
  frontmatter; binary artifacts MUST be referenced, not embedded.
- Identifiers: slugs and IDs MUST be stable and permanent; an identifier MUST NOT be reused
  for different content after deletion.
- Metadata: every artifact MUST declare at minimum `id`, `title`, `created`, `updated`,
  `source`, and `tags`; the schema MUST be defined once and validated in CI.
- Attribution: imported or quoted content MUST record its origin and license; content without
  attributable origin MUST NOT be published.
- Privacy: personal data MUST NOT be indexed or exposed without explicit consent; search and
  export paths MUST respect the access rules defined per collection.
- Accessibility: images MUST have alt text; documents MUST use semantic headings.

## Development Workflow & Delivery Scope

- Feature branches MUST be created with `.specify/scripts/bash/create-new-feature.sh`, which
  assigns the next sequential number and scaffolds `specs/<NNN-slug>/`.
- Commits MUST follow Conventional Commits (`feat:`, `fix:`, `docs:`, and similar).
- Pull requests MUST link their spec and plan, track work in the generated `tasks.md`, and
  pass all quality gates (Principle IV).
- Reviews MUST verify constitution compliance: Principles I-VII, the Data & Content Standards,
  and justified complexity. A reviewer who finds a violation MUST block the merge until it is
  resolved or explicitly waived.
- Documentation MUST be updated in the same change that alters behavior; stale documentation
  is treated as a defect.
- Delivery visibility: any content delivery failure MUST be visible through CI logs and a
  non-zero pipeline exit code; silent or partial delivery MUST NOT occur without a failure
  signal.
- Channel scope: the first implementation MUST target Telegram publishing only; additional
  channels (for example LinkedIn) are future extensions and MUST NOT complicate the first
  version.
- Automation preference: simple, maintainable automation MUST be preferred over unnecessary
  complexity (reinforces Principle V).

## Governance

- This constitution supersedes all other practices; conflicts with any other document are
  resolved in its favor.
- Amendment procedure: propose the change with rationale, produce a Sync Impact Report, apply
  the semantic version bump, obtain approval, then commit.
- Versioning policy:
  - MAJOR: removal or incompatible redefinition of an existing principle.
  - MINOR: new principle, section, or materially expanded guidance.
  - PATCH: clarifications, wording, and non-semantic refinements.
- Compliance review: every PR and code review MUST verify compliance; complexity MUST be
  justified in the plan or review; deviations require an explicit, documented waiver.
- Runtime development guidance lives with the active spec and plan under `specs/`; agent
  workflow definitions live under `.clinerules/workflows/`.

**Version**: 1.1.0 | **Ratified**: 2026-09-18 | **Last Amended**: 2026-09-18
