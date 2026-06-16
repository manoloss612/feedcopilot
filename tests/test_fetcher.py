import httpx
from feedcopilot.db.repository import create_feed, list_items
from feedcopilot.db.session import get_session, init_db
from feedcopilot.rss import fetcher
from feedcopilot.rss.fetcher import (
    _resolve_proxy,
    fetch_enabled_feeds,
    normalize_items,
    parse_feed_content,
)

RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example Feed</title>
    <link>https://example.com</link>
    <description>Example description</description>
    <item>
      <title>First Item</title>
      <link>https://example.com/first</link>
      <guid>first-guid</guid>
      <pubDate>Mon, 15 Jun 2026 08:00:00 GMT</pubDate>
      <description>First summary</description>
    </item>
  </channel>
</rss>
"""


def test_normalize_items_from_rss_xml():
    parsed = parse_feed_content(RSS_XML)

    items = normalize_items(parsed)

    assert len(items) == 1
    assert items[0].title == "First Item"
    assert items[0].guid == "first-guid"
    assert items[0].content_hash


def test_fetch_enabled_feeds_stores_new_items(tmp_path, monkeypatch):
    db_path = tmp_path / "feedcopilot.db"
    init_db(db_path)

    def fake_fetch_feed(url, timeout=20, user_agent="FeedCopilot/0.1", proxy=None):
        return parse_feed_content(RSS_XML)

    monkeypatch.setattr(fetcher, "fetch_feed", fake_fetch_feed)

    with get_session(db_path) as session:
        feed = create_feed(session, url="https://example.com/rss.xml")
        total, new = fetch_enabled_feeds(session)
        total_again, new_again = fetch_enabled_feeds(session)
        items = list_items(session, feed_id=feed.id)

    assert total == 1
    assert new == 1
    assert total_again == 1
    assert new_again == 0
    assert len(items) == 1
    assert items[0].title == "First Item"
