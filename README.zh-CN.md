# FeedCopilot

[English](README.md)

FeedCopilot 是一个本地优先的跨平台 RSS 阅读工具，提供命令行、三栏终端界面、Markdown 摘要、定时任务、备份恢复，以及面向本地代理工具的外部 AI 命令接口。

## 项目目标

FeedCopilot 适合以下使用方式：

- 作为本地 RSS 阅读器管理订阅源和文章状态；
- 通过 CLI 自动抓取 RSS、搜索文章、生成摘要；
- 生成 Markdown 日报，供个人阅读、归档或传给外部工具；
- 通过 shell 管道或外部命令与 OpenClaw、Hermes 等本地代理工具集成。

RSS 抓取、解析、存储、搜索和摘要生成默认都在本地完成，不消耗 AI token。AI 功能默认关闭，只会在用户显式配置外部命令后执行。

## 当前状态

FeedCopilot 目前是早期 v0.1 开发版本。核心本地 RSS 工作流已经可用，并提供接入本地数据库的基础三栏 TUI。全文抓取尚未实现。

当前版本支持：

- `feedcopilot` 主命令和 `fcp` 短命令；
- Windows、macOS、Linux；
- 本地单用户模式；
- SQLite 数据库；
- TOML 配置；
- RSS/Atom 抓取与去重；
- 订阅源分类和语言标记；
- 未读/已读、收藏状态；
- 基础搜索；
- OPML 导入导出；
- JSON 数据导入导出；
- Markdown 摘要生成；
- 接入本地数据库的三栏 TUI，默认采用 Catppuccin Mocha 风格配色，并支持可配置图标；
- 通过系统任务文件实现定时任务；
- 备份和恢复；
- 英文和中文界面字符串；
- 外部 AI 命令接口，不内置商业 AI API。

## 安装

从 GitHub 安装：

```bash
git clone https://github.com/manoloss612/feedcopilot.git
cd feedcopilot
python -m pip install -e .
```

如果使用 `pipx`，可在本地 checkout 目录中安装：

```bash
pipx install -e .
```

当前项目尚未发布到 PyPI。

## 快速开始

```bash
feedcopilot init
feedcopilot feed add https://example.com/rss.xml --category News --language en
feedcopilot fetch
feedcopilot item list --unread
feedcopilot digest --since 24h --output today.md
```

也可以使用短命令：

```bash
fcp fetch
fcp digest --since 24h
```

切换中文界面配置：

```bash
feedcopilot config set app.language zh
```

## TUI 外观

TUI 默认使用 ASCII 状态标记，保证普通终端也能正常显示。如果你在 Ghostty
里使用 Maple Mono NF 等 Nerd Font 字体，可以开启更丰富的分类、订阅源、
未读/已读、收藏、链接和日期图标：

```bash
feedcopilot config set tui.icon_set nerd
feedcopilot tui
```

当前可选图标集为 `ascii`、`nerd` 和 `none`。

## 常用命令

初始化和配置：

```bash
feedcopilot init
feedcopilot config path
feedcopilot config show
feedcopilot config set app.language zh
```

订阅源管理：

```bash
feedcopilot feed add URL --category News --language en
feedcopilot feed list
feedcopilot feed update FEED_ID --category Tech --language en
feedcopilot feed enable FEED_ID
feedcopilot feed disable FEED_ID
feedcopilot feed health
feedcopilot feed remove FEED_ID --yes
```

文章操作：

```bash
feedcopilot fetch
feedcopilot item list --unread
feedcopilot item read ITEM_ID
feedcopilot item mark-read ITEM_ID
feedcopilot item mark-unread ITEM_ID
feedcopilot item star ITEM_ID
feedcopilot item unstar ITEM_ID
feedcopilot search QUERY
```

通过代理抓取（公司内网 / 区域网络环境）：

```bash
feedcopilot config set fetch.proxy "http://127.0.0.1:8080"
# 也可以直接设置 HTTPS_PROXY / HTTP_PROXY 环境变量，无需改 config。
```

导入导出：

```bash
feedcopilot import opml feeds.opml
feedcopilot export opml --output feeds.opml
feedcopilot import json data.json
feedcopilot export json --output data.json
```

Markdown 摘要：

```bash
feedcopilot digest --since 24h
feedcopilot digest --since 24h --output today.md
feedcopilot digest --since 7d --category News --unread
```

定时任务：

```bash
feedcopilot schedule daily --time 08:00 --fetch --digest --no-ai
feedcopilot schedule status
feedcopilot schedule remove
```

默认只生成可审查的本地任务文件。需要安装到操作系统任务系统时，使用：

```bash
feedcopilot schedule daily --time 08:00 --fetch --digest --no-ai --install
```

各平台后端：

- macOS：`launchd` 用户任务；
- Linux：用户 `crontab`；
- Windows：Task Scheduler，通过 `schtasks` 创建。

备份和恢复：

```bash
feedcopilot backup create --output backup.zip
feedcopilot backup restore backup.zip
```

外部 AI 命令：

```bash
feedcopilot ai run --since 24h
```

AI 默认关闭。需要先配置：

```bash
feedcopilot config set ai.enabled true
feedcopilot config set ai.command "your-command"
```

## 本地代理工具集成

FeedCopilot 不绑定特定代理运行时。它连接 Claude Code、Codex CLI、OpenClaw、Hermes 等 vibe coding / 本地代理工具的方式是通用 CLI 协议：

- `feedcopilot digest` 把 Markdown 摘要输出到 stdout；
- `feedcopilot digest --output FILE` 把 Markdown 摘要写入文件；
- `feedcopilot ai run` 把摘要通过 stdin 传给用户配置的外部命令。

当前项目没有内置任何厂商 SDK 或专用 API 适配器。只要目标工具提供 shell 命令，并且能读取 stdin 或消费 Markdown 文件，就可以连接。

### 通过管道传给代理工具

```bash
feedcopilot digest --since 24h | hermes chat
feedcopilot digest --since 24h | openclaw run rss-summary
feedcopilot digest --since 24h | claude
feedcopilot digest --since 24h | codex
```

不同工具的 CLI 参数可能不同，请以你本机安装的实际命令为准。如果工具不能稳定读取 stdin，建议使用文件方式。

### 文件方式

```bash
feedcopilot digest --since 24h --output summaries/today.md
claude summaries/today.md
codex summaries/today.md
```

### 配置外部代理命令

FeedCopilot 可以把 digest 作为 stdin 传给一个配置好的外部命令：

```bash
feedcopilot config set ai.enabled true
feedcopilot config set ai.command "hermes chat"
feedcopilot ai run --since 24h
```

其他示例，取决于你本机实际安装的 CLI：

```bash
feedcopilot config set ai.command "openclaw run rss-summary"
feedcopilot config set ai.command "claude"
feedcopilot config set ai.command "codex"
```

更多示例见：

- `docs/agent-integration.md`
- `examples/hermes-integration.md`
- `examples/openclaw-skill.md`

## 当前限制

- TUI 目前提供基础三栏阅读、预览、已读和收藏操作，仍会继续打磨交互体验；
- `--full-text` 参数保留给未来全文抓取实现；
- 外部 AI 命令只负责调用用户配置的本地或 shell 命令，不内置任何商业 AI API；
- 项目尚未发布到 PyPI。

## 开发检查

```bash
python -m pytest
python -m ruff check .
```
