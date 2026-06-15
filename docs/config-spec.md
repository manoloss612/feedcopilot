# FeedCopilot Configuration Specification

## 1. Format

Main configuration format: TOML

Default file name:

```text
config.toml
```

Use `platformdirs` to locate config directory.

## 2. Example

```toml
[app]
language = "en"
theme = "default"

[storage]
database = "feedcopilot.db"
markdown_dir = "summaries"
backup_dir = "backups"
export_dir = "exports"

[fetch]
timeout = 20
user_agent = "FeedCopilot/0.1"
full_text = false
max_concurrent = 5

[digest]
default_since = "24h"
format = "markdown"
group_by = "category"
include_read = false
include_starred = true

[ai]
enabled = false
command = ""
input_mode = "stdin"
output_mode = "stdout"

[interests]
keywords = [
  "France",
  "AI",
  "translation",
  "higher education",
  "French literature"
]

[tui]
layout = "three_column"
show_health_status = true
preview_width = 40
```

## 3. Sections

### app

| Key | Type | Default | Notes |
|---|---|---|---|
| language | string | en | en or zh |
| theme | string | default | reserved |

### storage

| Key | Type | Default |
|---|---|---|
| database | string | feedcopilot.db |
| markdown_dir | string | summaries |
| backup_dir | string | backups |
| export_dir | string | exports |

### fetch

| Key | Type | Default |
|---|---|---|
| timeout | integer | 20 |
| user_agent | string | FeedCopilot/0.1 |
| full_text | boolean | false |
| max_concurrent | integer | 5 |

### digest

| Key | Type | Default |
|---|---|---|
| default_since | string | 24h |
| format | string | markdown |
| group_by | string | category |
| include_read | boolean | false |
| include_starred | boolean | true |

### ai

| Key | Type | Default | Notes |
|---|---|---|---|
| enabled | boolean | false | AI off by default |
| command | string | empty | external command |
| input_mode | string | stdin | stdin or file |
| output_mode | string | stdout | stdout or file |

### interests

| Key | Type | Default |
|---|---|---|
| keywords | list[string] | [] |

### tui

| Key | Type | Default |
|---|---|---|
| layout | string | three_column |
| show_health_status | boolean | true |
| preview_width | integer | 40 |

## 4. Config Commands

```bash
feedcopilot config path
feedcopilot config show
feedcopilot config set app.language zh
feedcopilot config set fetch.timeout 30
```
