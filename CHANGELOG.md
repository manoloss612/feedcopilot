# Changelog

## 0.1.0

Initial development version.

- Added Typer CLI entrypoints for `feedcopilot` and `fcp`.
- Added TOML configuration loading, saving, and `config` commands.
- Added SQLite models and repository functions for feeds, items, fetch logs, and app metadata.
- Added RSS fetching and normalization with local deduplication.
- Added feed, item, search, digest, import/export, schedule, AI, backup, and TUI commands.
- Added OS-level schedule installation for macOS launchd, Linux cron, and Windows Task Scheduler.
- Added OPML and JSON import/export helpers.
- Added Markdown digest rendering.
- Added lightweight English and Chinese i18n resources.
- Added pytest coverage for configuration, database, RSS, exporters, CLI, and runtime helpers.
