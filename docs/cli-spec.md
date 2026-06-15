# FeedCopilot CLI Specification

## 1. Commands

Official command:

```bash
feedcopilot
```

Short alias:

```bash
fcp
```

## 2. Global Options

```bash
feedcopilot --help
feedcopilot --version
feedcopilot --config PATH
feedcopilot --language en|zh
```

## 3. Initialization

```bash
feedcopilot init
```

Creates:

- config directory;
- data directory;
- SQLite database;
- summaries directory;
- default config.

## 4. Feed Management

### Add feed

```bash
feedcopilot feed add URL --category CATEGORY --language en
```

Example:

```bash
feedcopilot feed add https://www.lemonde.fr/rss/une.xml --category "French Media" --language fr
```

### List feeds

```bash
feedcopilot feed list
feedcopilot feed list --category "French Media"
feedcopilot feed list --disabled
```

### Remove feed

```bash
feedcopilot feed remove FEED_ID
feedcopilot feed remove FEED_ID --delete-items
feedcopilot feed remove FEED_ID --keep-items
```

Default behavior: ask user whether to keep historical items.

### Enable/disable feed

```bash
feedcopilot feed enable FEED_ID
feedcopilot feed disable FEED_ID
```

### Feed health

```bash
feedcopilot feed health
feedcopilot feed health FEED_ID
```

## 5. Fetch

```bash
feedcopilot fetch
feedcopilot fetch --feed FEED_ID
feedcopilot fetch --category CATEGORY
feedcopilot fetch --full-text
```

Default: only fetch RSS-provided content. Full-text fetching is optional.

## 6. Item Management

### List items

```bash
feedcopilot item list
feedcopilot item list --unread
feedcopilot item list --starred
feedcopilot item list --category CATEGORY
feedcopilot item list --language fr
```

### Read item

```bash
feedcopilot item read ITEM_ID
feedcopilot item open ITEM_ID
```

`open` should open the original link in the default browser.

### Mark read/unread

```bash
feedcopilot item mark-read ITEM_ID
feedcopilot item mark-unread ITEM_ID
```

### Star/unstar

```bash
feedcopilot item star ITEM_ID
feedcopilot item unstar ITEM_ID
```

### Delete

```bash
feedcopilot item delete ITEM_ID
feedcopilot item clear-read
feedcopilot item clear-feed FEED_ID
```

Batch operations require confirmation.

## 7. Search

```bash
feedcopilot search QUERY
feedcopilot search QUERY --category CATEGORY
feedcopilot search QUERY --language fr
```

Search scope:

- title;
- summary;
- feed title;
- category.

## 8. Import/Export

### OPML

```bash
feedcopilot import opml feeds.opml
feedcopilot export opml --output feeds.opml
```

### JSON

```bash
feedcopilot export json --output feedcopilot-data.json
feedcopilot import json feedcopilot-data.json
```

## 9. Digest

```bash
feedcopilot digest
feedcopilot digest --since 24h
feedcopilot digest --since 7d
feedcopilot digest --output summaries/today.md
feedcopilot digest --category "French Media"
feedcopilot digest --language fr
feedcopilot digest --unread
feedcopilot digest --starred
```

Default output: stdout.

File output:

```bash
feedcopilot digest --since 24h --output today.md
```

Agent pipeline:

```bash
feedcopilot digest --since 24h | hermes chat
```

## 10. TUI

```bash
feedcopilot tui
```

Opens three-column interface.

## 11. Scheduling

```bash
feedcopilot schedule daily
feedcopilot schedule daily --time 08:00 --fetch --digest --no-ai
feedcopilot schedule status
feedcopilot schedule remove
```

Default `schedule daily` should launch a wizard.

## 12. Backup/Restore

```bash
feedcopilot backup create
feedcopilot backup create --output feedcopilot-backup.zip
feedcopilot backup restore feedcopilot-backup.zip
```

Restore requires confirmation.

## 13. Config

```bash
feedcopilot config path
feedcopilot config show
feedcopilot config set app.language zh
feedcopilot config set ai.command "hermes chat"
```
