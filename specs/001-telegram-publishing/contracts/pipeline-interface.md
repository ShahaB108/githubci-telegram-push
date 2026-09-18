# Interface Contract: Publishing Pipeline (platform-neutral seam)

This is the complete interface between the CI wrappers and the pipeline core. CI wrappers
(GitHub Actions now, GitLab CI later) depend ONLY on what is defined here.

## Invocation

```text
python -m pipeline.main [--dry-run] [--limit N]
```

- `--dry-run`: detect and plan deliveries, print the summary, write nothing, exit 0
- `--limit N`: cap the number of posts delivered in this run (default: unlimited)
- Working directory MUST be the repository root.

## Environment contract

| Variable | Required | Secret | Meaning |
|----------|----------|--------|---------|
| TELEGRAM_BOT_TOKEN | yes | yes | bot token; no default, never logged |
| TELEGRAM_CHAT_ID | yes | no | target channel identifier (@name or numeric id) |
| PIPELINE_POSTS_DIR | no | no | posts directory, default `posts` |
| PIPELINE_LEDGER_PATH | no | no | ledger file, default `delivery/ledger.json` |

The pipeline reads configuration ONLY from the environment; no config files, no CLI secrets.

## Exit codes

| Code | Meaning | Log requirement |
|------|---------|-----------------|
| 0 | success, including nothing-to-publish | run summary always printed |
| 10 | missing/invalid credentials | names the missing/invalid variable, fails before any delivery |
| 20 | malformed post (parse or empty body) | names the file and the problem |
| 30 | delivery failed after retries | names the post, the attempt count, and the last error |
| 40 | ledger/detection I/O failure | names the path and the I/O problem |

## Output contract

- stdout: human-readable run summary - posts considered, delivered, skipped, failed, plus
  per-post outcome lines (spec FR-008).
- stderr: error details only; secrets MUST NEVER appear in stdout or stderr.

## Telegram API usage

- Endpoint: `POST https://api.telegram.org/bot<token>/sendMessage`, `parse_mode=HTML`,
  `disable_web_page_preview=true`.
- 429 responses: wait `Retry-After` seconds, counts as one of the 3 attempts (decision R7).
- 400/401/403 responses: treated as delivery failure for that message (exit 30 path).

## Ledger commit-back contract

After a run that changed delivery state, the pipeline commits `delivery/ledger.json` with the
message prefix `chore(delivery):` and pushes to the default branch. CI wrappers MUST skip
triggering a publishing run when a push only touches `delivery/` (loop guard, decision R4).
