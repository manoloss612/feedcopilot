import asyncio

from feedcopilot.db.models import Feed, Item
from feedcopilot.db.repository import create_feed, create_item_if_new
from feedcopilot.db.session import get_session, init_db
from feedcopilot.tui.app import (
    FeedCopilotTUI,
    build_filters,
    format_item_label,
    render_item_preview,
)


def create_tui_db(tmp_path):
    db_path = tmp_path / "feedcopilot.db"
    init_db(db_path)
    with get_session(db_path) as session:
        feed = create_feed(
            session,
            url="https://example.com/rss.xml",
            title="Example Feed",
            category="News",
        )
        item, _ = create_item_if_new(
            session,
            Item(
                feed_id=feed.id,
                title="Example Item",
                link="https://example.com/item",
                summary="Example summary",
                content_hash="hash",
            ),
        )
    return db_path, feed, item


def test_tui_format_helpers(tmp_path):
    feed = Feed(id=1, title="Example Feed", url="https://example.com/rss.xml", category="News")
    item = Item(
        feed_id=1,
        title="Example Item",
        link="https://example.com/item",
        summary="Example summary",
        content_hash="hash",
    )

    filters = build_filters([feed])
    label = format_item_label(item)
    preview = render_item_preview(item)

    assert filters[0].label == "All"
    assert filters[1].label == "[Category] News"
    assert filters[2].label == "  Example Feed"
    assert label == "[ ][ ] Example Item"
    assert "Example summary" in preview


def test_tui_loads_filters_items_and_preview(tmp_path):
    db_path, _, _ = create_tui_db(tmp_path)
    app = FeedCopilotTUI(db_path=db_path)
    preview = ""

    async def run_app():
        nonlocal preview
        async with app.run_test() as pilot:
            await pilot.pause()
            preview = str(app.query_one("#right").content)

    asyncio.run(run_app())

    assert len(app.filters) == 3
    assert len(app.items) == 1
    assert "Example Item" in preview


def test_tui_toggle_read_and_star_updates_db(tmp_path):
    db_path, _, item = create_tui_db(tmp_path)
    app = FeedCopilotTUI(db_path=db_path)

    async def run_app():
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_toggle_read()
            await app.action_toggle_star()

    asyncio.run(run_app())

    with get_session(db_path) as session:
        updated = session.get(Item, item.id)

    assert updated.is_read is True
    assert updated.is_starred is True
