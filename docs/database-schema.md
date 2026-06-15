# FeedCopilot Database Schema

Database: SQLite

ORM: SQLModel

## 1. feeds

Stores RSS/Atom sources.

| Column | Type | Notes |
|---|---|---|
| id | integer primary key | |
| title | text | feed title |
| url | text unique | RSS/Atom URL |
| site_url | text nullable | website URL |
| category | text | default `General` |
| language | text | manually set: en, zh, fr, etc. |
| enabled | boolean | default true |
| last_fetched_at | datetime nullable | latest fetch attempt |
| last_success_at | datetime nullable | latest successful fetch |
| last_error | text nullable | latest error message |
| failure_count | integer | consecutive failure count |
| created_at | datetime | |
| updated_at | datetime | |

Indexes:

- url unique
- category
- language
- enabled

## 2. items

Stores RSS entries.

| Column | Type | Notes |
|---|---|---|
| id | integer primary key | |
| feed_id | integer | foreign key to feeds.id |
| title | text | |
| link | text | original article link |
| guid | text nullable | entry id if available |
| author | text nullable | |
| published_at | datetime nullable | |
| summary | text nullable | RSS summary |
| content | text nullable | RSS content or optional full text |
| content_hash | text | used for deduplication |
| is_read | boolean | default false |
| is_starred | boolean | default false |
| interest_score | integer | computed from local interest keywords |
| created_at | datetime | |
| updated_at | datetime | |

Indexes:

- feed_id
- link
- guid
- published_at
- is_read
- is_starred
- content_hash
- interest_score

Deduplication order:

1. guid + feed_id;
2. link;
3. title + published_at + feed_id;
4. content_hash.

## 3. fetch_logs

Optional but recommended.

| Column | Type | Notes |
|---|---|---|
| id | integer primary key | |
| feed_id | integer | |
| status | text | success/failure |
| message | text nullable | error or summary |
| started_at | datetime | |
| ended_at | datetime | |
| item_count | integer | number of parsed entries |
| new_item_count | integer | number of inserted entries |

## 4. app_meta

Stores schema version and small metadata.

| Column | Type | Notes |
|---|---|---|
| key | text primary key | |
| value | text | |

Example:

```text
schema_version = 1
created_by = FeedCopilot
```

## 5. Migration Strategy

For v0.1, `SQLModel.metadata.create_all()` is acceptable.

For v0.2+, consider Alembic if schema changes become frequent.
