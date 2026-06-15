from feedcopilot.db.models import Item
from feedcopilot.db.repository import create_feed, create_item_if_new, list_feeds, list_items
from feedcopilot.db.session import get_session, init_db
from feedcopilot.exporters.json_export import export_json, import_json
from feedcopilot.exporters.markdown import render_digest
from feedcopilot.exporters.opml import export_opml, import_opml


def test_opml_import_export(tmp_path):
    path = tmp_path / "feeds.opml"

    export_opml(
        [
            {
                "title": "Example",
                "url": "https://example.com/rss.xml",
                "site_url": "https://example.com",
                "category": "News",
                "language": "en",
            }
        ],
        path,
    )
    feeds = import_opml(path)

    assert feeds == [
        {
            "title": "Example",
            "url": "https://example.com/rss.xml",
            "site_url": "https://example.com",
            "category": "News",
            "language": "en",
        }
    ]


def test_json_export_import(tmp_path):
    source_db = tmp_path / "source.db"
    target_db = tmp_path / "target.db"
    json_path = tmp_path / "data.json"
    init_db(source_db)
    init_db(target_db)

    with get_session(source_db) as session:
        feed = create_feed(session, url="https://example.com/rss.xml", title="Example")
        create_item_if_new(
            session,
            Item(
                feed_id=feed.id,
                title="Item",
                link="https://example.com/item",
                content_hash="hash",
            ),
        )
        export_json(session, json_path)

    with get_session(target_db) as session:
        feed_count, item_count = import_json(session, json_path)
        feeds = list_feeds(session)
        items = list_items(session)

    assert feed_count == 1
    assert item_count == 1
    assert feeds[0].title == "Example"
    assert items[0].title == "Item"


def test_render_digest_groups_items():
    digest = render_digest(
        [
            {
                "title": "Item",
                "link": "https://example.com/item",
                "summary": "Summary",
                "category": "News",
            }
        ]
    )

    assert "# FeedCopilot Digest" in digest
    assert "## News" in digest
    assert "[Item]" in digest
