# FeedCopilot Technical Design

## 1. Architecture

FeedCopilot has four layers:

```text
User Interface Layer
  - CLI using Typer/Rich
  - TUI using Textual

Application Layer
  - feed management
  - item management
  - search
  - digest generation
  - backup/restore
  - scheduling
  - external AI command runner

Data Layer
  - SQLite
  - TOML config
  - OPML/JSON/Markdown files

Integration Layer
  - external shell commands
  - OpenClaw/Hermes examples
  - OS scheduling systems
```

## 2. Technology Stack

- Language: Python 3.11+
- CLI: Typer
- Terminal formatting: Rich
- TUI: Textual
- RSS parsing: feedparser
- HTTP: httpx
- Database: SQLite
- ORM: SQLModel
- Config location: platformdirs
- Config format: TOML
- OPML parsing: defusedxml
- Tests: pytest
- Linting: ruff

## 3. Package Layout

```text
feedcopilot/
  cli/
    app.py
  core/
    config.py
    paths.py
    i18n.py
  db/
    models.py
    session.py
    repository.py
  rss/
    fetcher.py
    normalizer.py
    fulltext.py
  exporters/
    opml.py
    json_export.py
    markdown.py
  tui/
    app.py
    widgets.py
  scheduler/
    manager.py
    macos.py
    linux.py
    windows.py
  ai/
    external_command.py
  i18n/
    en.toml
    zh.toml
```

## 4. Data Flow

### Fetch Flow

```text
enabled feeds
  -> HTTP GET
  -> feedparser parse
  -> normalize entries
  -> deduplicate by guid/link/hash
  -> save new items
  -> update feed health status
```

### Digest Flow

```text
query items since range
  -> sort by interest score and publish time
  -> group by category/feed/language
  -> render Markdown
  -> write to stdout or file
  -> optionally pass to external AI command
```

### TUI Flow

```text
load categories and feeds
  -> display left column
  -> display matching items in middle column
  -> display item preview in right column
  -> user actions update SQLite
```

## 5. Cross-Platform Directories

Use `platformdirs`.

Expected examples:

```text
Windows: %APPDATA%\FeedCopilot\config.toml
macOS: ~/Library/Application Support/FeedCopilot/config.toml
Linux: ~/.config/FeedCopilot/config.toml
```

Data directory should contain:

```text
feedcopilot.db
summaries/
backups/
exports/
```

## 6. External AI Command Design

FeedCopilot should not include commercial AI APIs in v0.1.

It should support:

```bash
feedcopilot digest --since 24h
feedcopilot digest --since 24h --output today.md
feedcopilot digest --since 24h | hermes chat
```

Future enhancement:

```bash
feedcopilot ai summarize --since 24h
```

Where the external command is defined in config:

```toml
[ai]
enabled = true
command = "hermes chat"
```

## 7. Scheduling

FeedCopilot should provide:

```bash
feedcopilot schedule daily
feedcopilot schedule status
feedcopilot schedule remove
```

Implementation targets:

- macOS: launchd
- Linux: cron first, systemd timer later
- Windows: Task Scheduler

The schedule wizard should ask:

- execution time;
- fetch updates;
- generate Markdown digest;
- run external AI command;
- output directory.

## 8. Backup and Restore

Backup package should be a zip file containing:

```text
config.toml
feedcopilot.db
feeds.opml
summaries/
```

Restore must warn the user before overwriting existing data.

## 9. Error Handling

- Feed fetching errors should not stop the whole fetch process.
- Each feed should record last error and failure count.
- Database errors should be surfaced clearly.
- OPML import should skip invalid entries and report them.
- Batch delete operations require confirmation.

## 10. Security Notes

- Use defusedxml for OPML parsing.
- Do not execute arbitrary AI command unless explicitly configured by user.
- Do not send RSS content to external AI by default.
- Store everything locally by default.
