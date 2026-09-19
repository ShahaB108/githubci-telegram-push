# Knowledge Hub

Markdown-to-Telegram publishing automation for DevOps Farsi, built with Spec Kit.

## Publishing pipeline

- Markdown posts live in `posts/` - every `.md` file there is a post.
- When new posts reach `main`, CI publishes them to the configured Telegram channel
  via a bot. Failures fail the CI run with named causes (see the exit-code table in
  specs/001-telegram-publishing/contracts/pipeline-interface.md).
- Delivery state is tracked in `delivery/ledger.json` (committed back by the pipeline),
  so re-runs never duplicate content. Only one run per channel may execute at a time;
  this is enforced by the CI wrapper (concurrency group), not the pipeline core.

## Local usage

```bash
pip install -r requirements.txt -r requirements-dev.txt

export TELEGRAM_BOT_TOKEN="..."   # secret - never commit it
export TELEGRAM_CHAT_ID="..."     # channel @name or numeric id

python -m pipeline.main --dry-run # plan only, writes nothing
python -m pipeline.main           # detect -> convert -> deliver -> record
```

## Configuration (environment only)

| Variable | Required | Meaning |
|----------|----------|---------|
| TELEGRAM_BOT_TOKEN | yes (secret) | bot token; never committed, never logged |
| TELEGRAM_CHAT_ID | yes | target channel (@name or numeric id) |
| PIPELINE_POSTS_DIR | no | posts directory, default `posts` |
| PIPELINE_LEDGER_PATH | no | ledger file, default `delivery/ledger.json` |

## Development

- Tests: `pytest` (unit + contract hermetic; the integration smoke test runs only
  when Telegram credentials are present).
- Lint: `ruff check pipeline tests`.
- Workflow documents: `specs/001-telegram-publishing/` (spec, plan, research,
  data model, contract, quickstart, tasks).
