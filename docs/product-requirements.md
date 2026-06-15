# FeedCopilot Product Requirements Document

## 1. Product Positioning

FeedCopilot is a cross-platform TUI RSS reader for ordinary users, with CLI and automation interfaces for advanced users and local agents.

It should be usable in three ways:

1. ordinary user opens a TUI and reads RSS updates;
2. advanced user runs CLI commands and schedules daily digest generation;
3. local agents call FeedCopilot through shell commands and consume Markdown output.

## 2. Target Users

### Primary users

Ordinary users who want a lightweight RSS reader with a terminal UI and local storage.

### Secondary users

Advanced users who use OpenClaw, Hermes, Codex CLI, Claude Code, or other agent systems.

### Tertiary users

Researchers, teachers, and knowledge workers who want to turn RSS updates into daily reading material, teaching material, or research monitoring notes.

## 3. Core Principles

- Local first.
- RSS fetching must not consume AI tokens.
- AI is optional.
- The CLI interface must be stable and agent-friendly.
- Default experience must be simple enough for ordinary users.
- Advanced features should not make the basic workflow complicated.
- Cross-platform support: Windows, macOS, Linux.

## 4. Version 0.1 Scope

### Must have

- Python package installation.
- `feedcopilot` and `fcp` commands.
- SQLite storage.
- TOML configuration.
- Three-column TUI.
- Add/delete/enable/disable feeds.
- Feed categories.
- Manual feed language setting.
- OPML import/export.
- JSON import/export.
- RSS/Atom fetching.
- Store title, link, summary, published time, source, author if available.
- Unread/read state.
- Star/unstar items.
- Basic search.
- Feed health check.
- Markdown digest.
- Schedule wizard.
- Backup and restore.
- English and Chinese UI strings.
- Optional full-text fetching.
- External AI command interface.

### Should have

- Interest keywords for local filtering and digest sorting.
- Safe delete confirmations.
- Source health indicators in TUI.
- Configurable data directories.
- Good README and docs.

### Out of scope for v0.1

- Cloud sync.
- User account system.
- Multi-user mode.
- Plugin marketplace.
- Built-in commercial AI APIs.
- Semantic search.
- Advanced recommendation algorithm.
- Web UI.
- Mobile app.

## 5. User Stories

### TUI user

As a user, I want to import my RSS feeds from OPML, open a TUI, browse categories, read new items, mark them as read, and star important items.

### CLI user

As a user, I want to run `feedcopilot fetch` and `feedcopilot digest --since 24h` from my terminal or scheduled task.

### Agent user

As an agent user, I want to pipe a Markdown digest into an external agent command:

```bash
feedcopilot digest --since 24h | hermes chat
```

### Backup user

As a user, I want to back up my feeds, config, database, and summaries into a zip file and restore them later.

## 6. Success Criteria

v0.1 is successful if:

- A new user can install it with pipx.
- A user can import OPML and read feeds in TUI.
- Fetching RSS works without AI configuration.
- Digest generation works as Markdown.
- Scheduling works on at least macOS and Linux, with Windows documented or implemented.
- OpenClaw/Hermes can consume FeedCopilot output through CLI.
