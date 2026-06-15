# Hermes Integration Example

## Pipeline

```bash
feedcopilot digest --since 24h | hermes chat
```

## File-based workflow

```bash
feedcopilot digest --since 24h --output summaries/today.md
hermes chat summaries/today.md
```

## Suggested Prompt

```text
Summarize the following RSS updates into a concise daily briefing.
Prioritize items related to the user's configured interests.
Keep original links.
```
