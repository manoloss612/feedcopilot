# FeedCopilot

FeedCopilot is a cross-platform TUI RSS reader for ordinary users, with CLI, scheduling, Markdown digest, backup/restore, and external AI command support for advanced users and local agents.

## Goals

FeedCopilot is designed as:

- a local-first RSS reader;
- a three-column terminal UI reader;
- a CLI tool for automation;
- a Markdown digest generator;
- a bridge between RSS feeds and local agents such as OpenClaw, Hermes, Codex CLI, or other shell-based tools.

RSS fetching, parsing, storage, reading-state management, search, and digest generation should work without consuming any AI tokens. AI is optional and is only invoked through external commands configured by the user.

## First Version Scope

FeedCopilot v0.1 supports:

- Python package installation, preferably via `pipx`;
- official command: `feedcopilot`;
- short alias: `fcp`;
- Windows, macOS, and Linux;
- local single-user mode;
- SQLite database;
- TOML configuration;
- OPML import/export;
- JSON export/import for data portability;
- Markdown digest generation;
- TUI three-column reader;
- feed categories;
- manual feed language setting;
- unread/read state;
- starred items;
- basic search;
- feed health checks;
- optional full-text fetching;
- schedule wizard;
- backup and restore;
- English and Chinese interface;
- external AI command interface.

## Installation

Development installation:

```bash
git clone https://github.com/YOUR_USERNAME/feedcopilot.git
cd feedcopilot
pipx install -e .
```

Future PyPI installation:

```bash
pipx install feedcopilot
```

## Quick Start

```bash
feedcopilot init
feedcopilot feed add https://example.com/rss.xml --category News --language en
feedcopilot fetch
feedcopilot tui
feedcopilot digest --since 24h --output today.md
```

Short alias:

```bash
fcp fetch
fcp digest --since 24h
```

## Agent Usage

FeedCopilot does not require a specific agent runtime. It exposes stable CLI commands and Markdown output:

```bash
feedcopilot digest --since 24h | hermes chat
feedcopilot digest --since 24h | openclaw run rss-summary
```

Or save to file:

```bash
feedcopilot digest --since 24h --output summaries/today.md
```

## Documentation

See:

- `docs/product-requirements.md`
- `docs/technical-design.md`
- `docs/cli-spec.md`
- `docs/database-schema.md`
- `docs/config-spec.md`
- `docs/tui-design.md`
- `docs/agent-integration.md`
- `docs/codex-development-plan.md`

## Implemented v0.1 Commands

The current development build includes the local-first core workflow:

```bash
feedcopilot init
feedcopilot config path
feedcopilot config show
feedcopilot config set app.language zh

feedcopilot feed add URL --category News --language en
feedcopilot feed list
feedcopilot feed enable FEED_ID
feedcopilot feed disable FEED_ID
feedcopilot feed health
feedcopilot feed remove FEED_ID --yes

feedcopilot fetch
feedcopilot item list --unread
feedcopilot item read ITEM_ID
feedcopilot item mark-read ITEM_ID
feedcopilot item star ITEM_ID
feedcopilot search QUERY

feedcopilot import opml feeds.opml
feedcopilot export opml --output feeds.opml
feedcopilot import json data.json
feedcopilot export json --output data.json

feedcopilot digest --since 24h
feedcopilot schedule daily --time 08:00 --fetch --digest --no-ai
feedcopilot schedule daily --time 08:00 --fetch --digest --no-ai --install
feedcopilot schedule status
feedcopilot schedule remove
feedcopilot backup create --output backup.zip
feedcopilot ai run --since 24h
```

Scheduling writes reviewable local task files first. Passing `--install` asks
for confirmation before installing the OS-level task:

- macOS: `launchd` user agent in `~/Library/LaunchAgents`
- Linux: user `crontab` block
- Windows: Task Scheduler task created with `schtasks`

## Development Checks

```bash
python -m pytest
python -m ruff check .
```
