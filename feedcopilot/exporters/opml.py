"""OPML import/export helpers."""

from pathlib import Path
from xml.sax.saxutils import escape

from defusedxml import ElementTree


def import_opml(path: str | Path) -> list[dict]:
    tree = ElementTree.parse(path)
    feeds: list[dict] = []
    for outline in tree.findall(".//outline"):
        xml_url = outline.attrib.get("xmlUrl") or outline.attrib.get("xmlurl")
        if not xml_url:
            continue
        feeds.append(
            {
                "title": outline.attrib.get("title") or outline.attrib.get("text") or xml_url,
                "url": xml_url,
                "site_url": outline.attrib.get("htmlUrl") or outline.attrib.get("htmlurl"),
                "category": outline.attrib.get("category") or "General",
                "language": outline.attrib.get("language") or "en",
            }
        )
    return feeds


def export_opml(feeds: list[dict], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<opml version="2.0">',
        "  <head>",
        "    <title>FeedCopilot Feeds</title>",
        "  </head>",
        "  <body>",
    ]
    for feed in feeds:
        title = escape(str(feed.get("title") or feed.get("url") or "Untitled"))
        url = escape(str(feed.get("url") or ""))
        site_url = escape(str(feed.get("site_url") or ""))
        category = escape(str(feed.get("category") or "General"))
        language = escape(str(feed.get("language") or "en"))
        lines.append(
            "    "
            f'<outline text="{title}" title="{title}" type="rss" xmlUrl="{url}" '
            f'htmlUrl="{site_url}" category="{category}" language="{language}" />'
        )
    lines.extend(["  </body>", "</opml>", ""])
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
