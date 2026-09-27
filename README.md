# Knowledge Hub

Markdown-to-Telegram publishing automation for DevOps Farsi.

## Layout

- Markdown posts live at the repository root: every root-level `.md` file is a post.
  The repository documents (`README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`,
  `SECURITY.md`, `CODE_OF_CONDUCT.md`, `LICENSE.md`) and dotfiles are never published;
  more names can be excluded with `PIPELINE_IGNORE`.
- All pipeline code lives in `engine/`: `engine/pipeline/` (package), `engine/tests/`
  and the tooling files (`pytest.ini`, `ruff.toml`, `requirements*.txt`).
- Re-runs never duplicate content: delivery state is tracked per post, and only one run
  per channel may execute at a time (enforced by the CI concurrency group, not by the
  pipeline core).
- A push to `main` that touches a root-level `.md` (or `engine/**`) runs
  `.github/workflows/publish.yml`: a quality gate (ruff + pytest), then the publish job.

## Delivery state

Where the delivery ledger lives depends on the environment:

| Environment | Ledger | Commit-back |
|-------------|--------|-------------|
| CI (GitHub Actions) | `delivery/ledger.json` on the reserved `delivery-state` branch, read and written through the GitHub API | disabled (`PIPELINE_COMMIT=0`) |
| Local runs | `engine/delivery/ledger.json` | committed and pushed by the pipeline (`chore(delivery): record deliveries`) |

CI deliberately keeps state off `main`: GitHub `main` is a pure mirror of the GitLab
source of truth, so a commit written there would either be overwritten by the next mirror
push or silently stop the mirror from updating. GitLab never deletes `delivery-state`
because that branch does not exist upstream.

Manual runs: `Actions -> publish -> Run workflow` with `dry_run` on exercises the whole
chain (mirror, CI, Telegram credentials) without publishing anything.

## Local usage

```bash
cd engine                        # the posts directory defaults to the repository root
pip install -r requirements.txt -r requirements-dev.txt

export TELEGRAM_BOT_TOKEN="..."  # secret - never commit it
export TELEGRAM_CHAT_ID="..."    # channel @name or numeric id

python -m pipeline.main --dry-run # plan only, writes nothing
python -m pipeline.main           # detect -> convert -> deliver -> record
```

## Configuration (environment only)

| Variable | Required | Meaning |
|----------|----------|---------|
| TELEGRAM_BOT_TOKEN | yes (secret) | bot token; never committed, never logged |
| TELEGRAM_CHAT_ID | yes | target channel (@name or numeric id) |
| PIPELINE_POSTS_DIR | no | posts directory, default: repository root |
| PIPELINE_LEDGER_PATH | no | ledger file, default `engine/delivery/ledger.json` |
| PIPELINE_IGNORE | no | extra root documents never published (comma separated) |
| PIPELINE_REPO_ROOT | no | override repository-root detection (post identity prefix) |
| PIPELINE_COMMIT | no | `0`/`false`/`no` disables the ledger commit-back (CI uses this) |

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | success (including "nothing to publish") |
| 10 | configuration error (missing or invalid environment) |
| 20 | malformed post (unparsable frontmatter or empty body) |
| 30 | delivery failed after the bounded retries |
| 40 | ledger I/O error |

## Development

Run these from `engine/`:

- Tests: `pytest` (unit + contract tests are hermetic; the integration smoke test runs
  only when Telegram credentials are present).
- Lint: `ruff check pipeline tests`.

