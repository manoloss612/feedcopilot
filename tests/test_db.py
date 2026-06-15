from datetime import datetime

from feedcopilot.db.models import Item
from feedcopilot.db.repository import (
    create_feed,
    create_item_if_new,
    list_feeds,
    mark_read,
    search_items,
    toggle_star,
)
from feedcopilot.db.session import get_session, init_db


def test_feed_repository_crud(tmp_path):
    db_path = tmp_path / "feedcopilot.db"
    init_db(db_path)

    with get_session(db_path) as session:
        feed = create_feed(
            session,
            url="https://example.com/rss.xml",
            title="Example",
            category="News",
            language="en",
        )
        feeds = list_feeds(session)

    assert feed.id is not None
    assert len(feeds) == 1
    assert feeds[0].title == "Example"


def test_create_item_if_new_deduplicates_by_guid(tmp_path):
    db_path = tmp_path / "feedcopilot.db"
    init_db(db_path)

    with get_session(db_path) as session:
        feed = create_feed(session, url="https://example.com/rss.xml")
        item = Item(
            feed_id=feed.id,
            title="One",
            link="https://example.com/one",
            guid="guid-1",
            published_at=datetime(2026, 1, 1),
            content_hash="hash-1",
        )
        first, created_first = create_item_if_new(session, item)
        second, created_second = create_item_if_new(
            session,
            Item(
                feed_id=feed.id,
                title="One copy",
                link="https://example.com/other",
                guid="guid-1",
                content_hash="hash-2",
            ),
        )

    assert created_first is True
    assert created_second is False
    assert second.id == first.id


def test_search_and_item_state(tmp_path):
    db_path = tmp_path / "feedcopilot.db"
    init_db(db_path)

    with get_session(db_path) as session:
        feed = create_feed(session, url="https://example.com/rss.xml", category="News")
        item, _ = create_item_if_new(
            session,
            Item(
                feed_id=feed.id,
                title="Python RSS",
                link="https://example.com/python-rss",
                summary="Local-first feed reader",
                content_hash="hash-python",
            ),
        )
        mark_read(session, item.id)
        toggle_star(session, item.id, True)
        results = search_items(session, "Python")

    assert len(results) == 1
    assert results[0].is_read is True
    assert results[0].is_starred is True
