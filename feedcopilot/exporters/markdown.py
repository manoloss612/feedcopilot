"""Markdown digest renderer skeleton."""


def render_digest(items: list[dict], title: str = "FeedCopilot Digest") -> str:
    lines = [f"# {title}", ""]
    if not items:
        lines.extend(["No items found.", ""])
        return "\n".join(lines)

    current_group = None
    for item in items:
        group = item.get("category", "General")
        if group != current_group:
            current_group = group
            lines.extend([f"## {group}", ""])
        lines.append(f"- [{item.get('title', 'Untitled')}]({item.get('link', '')})")
        if item.get("summary"):
            lines.append(f"  - {item['summary']}")
    lines.append("")
    return "\n".join(lines)
