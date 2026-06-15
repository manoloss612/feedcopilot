# OpenClaw Skill Example for FeedCopilot

## Purpose

Use FeedCopilot to generate a daily RSS digest and ask OpenClaw to summarize it.

## Shell command

```bash
feedcopilot digest --since 24h
```

## Prompt

```text
You are an RSS digest assistant.
Read the FeedCopilot Markdown digest.
Return:
1. top 5 important items;
2. grouped themes;
3. concise summary;
4. original links.
```
