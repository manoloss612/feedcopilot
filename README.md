# FeedCopilot

[中文说明](README.zh-CN.md)

FeedCopilot is a cross-platform TUI RSS reader for ordinary users, with CLI, scheduling, Markdown digest, backup/restore, and external AI command support for advanced users and local agents.

## Goals

FeedCopilot is designed as:

- a local-first RSS reader;
- a three-column terminal UI reader;
- a CLI tool for automation;
- a Markdown digest generator;
- a bridge between RSS feeds and local agents such as OpenClaw, Hermes, or other shell-based tools.

RSS fetching, parsing, storage, reading-state management, search, and digest generation should work without consuming any AI tokens. AI is optional and is only invoked through external commands configured by the user.

## Current Status

FeedCopilot is currently an early v0.1 development build. It supports the local
RSS workflow end to end, including a basic database-backed three-column TUI.
Full-text article extraction is not implemented yet.

The current build supports:

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
- database-backed three-column TUI with a Catppuccin Mocha inspired palette;
- feed categories;
- manual feed language setting;
- unread/read state;
- starred items;
- basic search;
- feed health checks;
- scheduled jobs through generated OS task files;
- backup and restore;
- English and Chinese interface;
- external AI command interface.

## Installation

Install from GitHub:

```bash
git clone https://github.com/manoloss612/feedcopilot.git
cd feedcopilot
python -m pip install -e .
```

If you use `pipx`, install from the local checkout:

```bash
pipx install -e .
```

The package is not published to PyPI yet.

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

FeedCopilot does not require a specific agent runtime. It connects to vibe coding
and local agent tools through a generic CLI contract:

- `feedcopilot digest` writes Markdown to stdout;
- `feedcopilot digest --output FILE` writes Markdown to a file;
- `feedcopilot ai run` sends the digest to the configured external command.

There are no built-in vendor SDK integrations. Claude Code, Codex CLI, OpenClaw,
Hermes, and similar tools can be connected as long as they expose a shell command
that can read stdin or consume a Markdown file.

### Pipe a digest into an agent

```bash
feedcopilot digest --since 24h | hermes chat
feedcopilot digest --since 24h | openclaw run rss-summary
feedcopilot digest --since 24h | claude
feedcopilot digest --since 24h | codex
```

Use the actual command syntax required by your installed tool. If the tool does
not read stdin reliably, use the file-based workflow instead.

### File-based workflow

```bash
feedcopilot digest --since 24h --output summaries/today.md
claude summaries/today.md
codex summaries/today.md
```

### Configure an external agent command

FeedCopilot can run one configured command with the digest as stdin:

```bash
feedcopilot config set ai.enabled true
feedcopilot config set ai.command "hermes chat"
feedcopilot ai run --since 24h
```

Other examples, depending on the CLI installed on your machine:

```bash
feedcopilot config set ai.command "openclaw run rss-summary"
feedcopilot config set ai.command "claude"
feedcopilot config set ai.command "codex"
```

## Documentation

See:

- `docs/agent-integration.md`

## Implemented v0.1 Commands

The current v0.1 build includes the local-first core workflow:

```bash
feedcopilot init
feedcopilot config path
feedcopilot config show
feedcopilot config set app.language zh

feedcopilot feed add URL --category News --language en
feedcopilot feed list
feedcopilot feed update FEED_ID --category Tech --language en
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

# Fetch through a corporate / regional proxy
feedcopilot config set fetch.proxy "http://127.0.0.1:8080"
# ... or set HTTPS_PROXY / HTTP_PROXY in the environment, and run normally.

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
