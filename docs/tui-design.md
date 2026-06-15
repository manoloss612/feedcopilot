# FeedCopilot TUI Design

## 1. Layout

FeedCopilot v0.1 uses a traditional three-column RSS reader layout.

```text
+----------------------+------------------------------+--------------------------------+
| Categories / Feeds   | Article List                 | Preview                        |
|                      |                              |                                |
| General              | [ ] Article title            | Title                          |
|   Feed A             | [*] Starred article          | Source                         |
|   Feed B             | [x] Read article             | Published time                 |
| French Media         |                              | Summary                        |
|   Le Monde           |                              | Link                           |
|   France Culture     |                              |                                |
+----------------------+------------------------------+--------------------------------+
```

## 2. Left Column

Displays:

- categories;
- feeds under categories;
- feed health status.

Health status symbols:

```text
✓ successful
! recent error
× repeated failure
```

## 3. Middle Column

Displays article list.

Indicators:

```text
[ ] unread
[x] read
[*] starred
```

Sorting default:

1. unread first;
2. interest score high to low;
3. published time newest first.

## 4. Right Column

Displays:

- title;
- source;
- category;
- language;
- published time;
- summary;
- original link;
- available actions.

## 5. Keyboard Shortcuts

```text
q          quit
j / down   next item
k / up     previous item
h / left   focus previous column
l / right  focus next column
enter      open/read selected item
o          open original link in browser
r          toggle read/unread
s          toggle starred
f          fetch updates
/          search
a          add feed
d          generate digest
?          help
```

## 6. Chinese Interface

All visible UI strings should go through the i18n layer.

Examples:

```text
Feeds -> 订阅源
Articles -> 文章
Preview -> 预览
Unread -> 未读
Starred -> 收藏
Fetch updates -> 抓取更新
```

## 7. TUI Implementation

Use Textual.

Suggested widgets:

- `FeedTree`
- `ItemList`
- `ItemPreview`
- `StatusBar`
- `CommandPalette`
- `SearchModal`
- `AddFeedModal`
- `ConfirmDialog`

For v0.1, a minimal layout with three panels is acceptable.
