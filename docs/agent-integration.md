# FeedCopilot Agent Integration

## 1. Principle

FeedCopilot should not depend on a specific agent runtime.

The stable integration surface is the CLI:

- stdout Markdown from `feedcopilot digest`;
- file output from `feedcopilot digest --output FILE`;
- external command execution from `feedcopilot ai run`.

FeedCopilot does not include vendor SDK integrations. Claude Code, Codex CLI,
OpenClaw, Hermes, and similar vibe coding tools can be connected when they
provide a shell command that reads stdin or accepts a Markdown file.

## 2. Basic Agent Patterns

### Stdout pipeline

```bash
feedcopilot digest --since 24h | hermes chat
```

```bash
feedcopilot digest --since 24h | openclaw run rss-summary
```

```bash
feedcopilot digest --since 24h | claude
```

```bash
feedcopilot digest --since 24h | codex
```

### File-based workflow

```bash
feedcopilot digest --since 24h --output summaries/today.md
hermes chat summaries/today.md
```

```bash
feedcopilot digest --since 24h --output summaries/today.md
claude summaries/today.md
```

```bash
feedcopilot digest --since 24h --output summaries/today.md
codex summaries/today.md
```

Use the actual command syntax required by the agent CLI installed on your
machine. If a tool does not read stdin reliably, prefer the file-based workflow.

## 3. External AI Command

Config:

```toml
[ai]
enabled = true
command = "hermes chat"
input_mode = "stdin"
output_mode = "stdout"
```

Command:

```bash
feedcopilot ai run --since 24h
```

Other command examples:

```bash
feedcopilot config set ai.command "openclaw run rss-summary"
feedcopilot config set ai.command "claude"
feedcopilot config set ai.command "codex"
```

Expected behavior:

1. generate Markdown digest;
2. pass it to the external command;
3. display or save external command output.

## 4. OpenClaw Example

Example skill prompt:

```text
You are an RSS digest assistant.
Run:
feedcopilot digest --since 24h
Then summarize the updates into:
1. top 5 important items;
2. grouped themes;
3. links for further reading.
```

Shell command:

```bash
feedcopilot digest --since 24h
```

## 5. Hermes Example

Pipeline:

```bash
feedcopilot digest --since 24h | hermes chat
```

Prompt template:

```text
Please summarize the following RSS updates.
Prioritize items related to the user's interests.
Keep links.
Return a concise daily briefing.
```

## 6. Token Policy

RSS fetching does not use tokens.

AI is only used when:

- user pipes output to an agent;
- user runs an AI command;
- user enables a scheduled AI digest.

Default is no AI.
