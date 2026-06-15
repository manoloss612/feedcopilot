# FeedCopilot Codex Development Plan

This document is designed to be used with Codex CLI or another coding agent.

Development should be incremental. After each phase, run tests and keep the repository working.

## General Rules for Codex

- Do not implement everything at once.
- Keep functions small and testable.
- Prefer clear code over clever code.
- Preserve cross-platform behavior.
- Add tests for every core module.
- Do not add commercial AI API dependencies in v0.1.
- Do not send feed content to external services unless explicitly requested by the user.
- Use `ruff` for linting and `pytest` for testing.
- Update docs when behavior changes.

## Phase 0 — Project Skeleton

Prompt for Codex:

```text
Create the initial FeedCopilot Python project skeleton according to pyproject.toml and docs.
Ensure the package has these modules:
feedcopilot.cli, feedcopilot.core, feedcopilot.db, feedcopilot.rss, feedcopilot.exporters, feedcopilot.tui, feedcopilot.scheduler, feedcopilot.ai, feedcopilot.i18n.
Make `feedcopilot --help` and `fcp --help` work.
Do not implement full business logic yet.
Add a smoke test for CLI import.
```

Acceptance criteria:

```bash
python -m pytest
feedcopilot --help
fcp --help
```

## Phase 1 — Configuration System

Prompt:

```text
Implement the configuration system.
Use platformdirs for config and data directories.
Use TOML for config file.
Use Pydantic models from feedcopilot.core.config.
Implement:
- get_config_dir
- get_data_dir
- get_config_path
- load_config
- save_config
- create_default_config
- feedcopilot config path
- feedcopilot config show
- feedcopilot config set KEY VALUE
Add tests.
```

Acceptance criteria:

```bash
feedcopilot init
feedcopilot config path
feedcopilot config show
feedcopilot config set app.language zh
```

## Phase 2 — SQLite Database

Prompt:

```text
Implement SQLite database initialization and repository layer using SQLModel.
Use models from docs/database-schema.md.
Implement feeds, items, fetch_logs, and app_meta as needed.
Implement repository functions:
- create_feed
- list_feeds
- get_feed
- update_feed
- delete_feed
- create_item_if_new
- list_items
- search_items
- mark_read
- toggle_star
- delete_item
Add tests using temporary SQLite database.
```

Acceptance criteria:

```bash
feedcopilot init
pytest tests/test_db.py
```

## Phase 3 — RSS Fetching and Parsing

Prompt:

```text
Implement RSS fetching.
Use httpx and feedparser.
Default behavior: fetch RSS-provided content only.
Normalize entries into internal item structure.
Deduplicate by guid, link, title+published_at, content_hash.
Update feed health:
- last_fetched_at
- last_success_at
- last_error
- failure_count
Implement `feedcopilot fetch`.
Add tests using sample RSS XML fixtures, without network.
```

Acceptance criteria:

```bash
feedcopilot feed add <sample-or-real-feed-url>
feedcopilot fetch
feedcopilot item list --unread
pytest tests/test_fetcher.py
```

## Phase 4 — CLI Core Commands

Prompt:

```text
Implement CLI commands according to docs/cli-spec.md:
- feed add/list/remove/enable/disable/health
- item list/read/open/mark-read/mark-unread/star/unstar/delete/clear-read/clear-feed
- search
- fetch
Use Rich for readable output.
Use confirmation prompts for destructive operations.
Add tests using Typer CliRunner.
```

Acceptance criteria:

```bash
feedcopilot feed list
feedcopilot item list --unread
feedcopilot search "test"
```

## Phase 5 — OPML and JSON Import/Export

Prompt:

```text
Implement OPML import/export with defusedxml.
Implement JSON export/import for FeedCopilot data.
Commands:
- feedcopilot import opml feeds.opml
- feedcopilot export opml --output feeds.opml
- feedcopilot import json data.json
- feedcopilot export json --output data.json
Skip invalid OPML entries and report warnings.
Add tests with sample OPML.
```

Acceptance criteria:

```bash
feedcopilot import opml examples/feeds.opml
feedcopilot export opml --output /tmp/feeds.opml
```

## Phase 6 — Markdown Digest

Prompt:

```text
Implement Markdown digest generation.
Support:
- --since
- --output
- --category
- --language
- --unread
- --starred
Sort by:
1. interest score
2. published time
Group by category by default.
Output to stdout unless --output is provided.
Add tests.
```

Acceptance criteria:

```bash
feedcopilot digest --since 24h
feedcopilot digest --since 24h --output today.md
```

## Phase 7 — TUI

Prompt:

```text
Implement a minimal Textual three-column TUI.
Left: categories and feeds.
Middle: articles.
Right: preview.
Support shortcuts:
q, j/k, h/l, enter, o, r, s, f, /, ?, d.
It is acceptable for v0.1 to implement simple but stable interactions.
All UI strings must pass through i18n.
```

Acceptance criteria:

```bash
feedcopilot tui
```

## Phase 8 — Scheduling

Prompt:

```text
Implement schedule wizard:
feedcopilot schedule daily
feedcopilot schedule daily --time 08:00 --fetch --digest --no-ai
feedcopilot schedule status
feedcopilot schedule remove

Implement macOS launchd first.
Implement Linux cron second.
Implement Windows Task Scheduler if feasible; otherwise document limitation clearly.
Generate task files/scripts safely.
Ask confirmation before installing.
```

Acceptance criteria:

```bash
feedcopilot schedule daily
feedcopilot schedule status
```

## Phase 9 — External AI Command Interface

Prompt:

```text
Implement external AI command interface.
Do not add built-in commercial AI APIs.
Support:
- digest to stdout
- digest to file
- optional command execution when enabled
Config:
[ai]
enabled = false
command = ""
input_mode = "stdin"
output_mode = "stdout"
Add command:
feedcopilot ai run --since 24h
```

Acceptance criteria:

```bash
feedcopilot digest --since 24h | cat
feedcopilot ai run --since 24h
```

## Phase 10 — Backup and Restore

Prompt:

```text
Implement backup and restore.
Backup package should include:
- config.toml
- feedcopilot.db
- feeds.opml
- summaries/
Commands:
feedcopilot backup create
feedcopilot backup create --output backup.zip
feedcopilot backup restore backup.zip
Restore requires confirmation.
Add tests using temporary directories.
```

Acceptance criteria:

```bash
feedcopilot backup create
feedcopilot backup restore backup.zip
```

## Phase 11 — English and Chinese i18n

Prompt:

```text
Implement lightweight i18n.
Support en and zh.
Load strings from feedcopilot/i18n/en.toml and zh.toml.
Make CLI and TUI user-facing strings translatable where practical.
Add config app.language.
```

Acceptance criteria:

```bash
feedcopilot config set app.language zh
feedcopilot --help
```

## Phase 12 — Documentation and Release Prep

Prompt:

```text
Update README and docs.
Add examples:
- examples/feeds.opml
- examples/config.toml
- examples/openclaw-skill.md
- examples/hermes-integration.md
Add GitHub Actions workflow for tests.
Add MIT LICENSE.
Add CHANGELOG.md.
Make the repository ready for GitHub.
```

Acceptance criteria:

```bash
pytest
ruff check .
```

## Recommended First Codex Command

After creating the repository, start with:

```text
Read docs/codex-development-plan.md, README.md, pyproject.toml, and the current package skeleton. Implement Phase 0 only. Do not move to Phase 1 yet. Run tests and show the result.
```

Then proceed one phase at a time.
