"""Minimal but functional Textual TUI."""

import webbrowser
from dataclasses import dataclass
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

from feedcopilot.core.config import get_data_dir, load_config
from feedcopilot.core.i18n import translate
from feedcopilot.db.models import Feed, Item
from feedcopilot.db.repository import list_feeds, list_items, mark_read, toggle_star
from feedcopilot.db.session import get_session
from feedcopilot.rss.fetcher import fetch_enabled_feeds


@dataclass(frozen=True)
class FeedFilter:
    label: str
    category: str | None = None
    feed_id: int | None = None
    kind: str = "all"


class FeedCopilotTUI(App):
    """Three-column RSS reader backed by the local SQLite database."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("h", "focus_left", "Left"),
        ("l", "focus_right", "Right"),
        ("enter", "select", "Select"),
        ("r", "toggle_read", "Read"),
        ("s", "toggle_star", "Star"),
        ("o", "open_item", "Open"),
        ("f", "fetch", "Fetch"),
        ("?", "show_help", "Help"),
    ]

    CSS = """
    Screen {
        layout: vertical;
        background: #1e1e2e;
        color: #cdd6f4;
    }

    Header {
        background: #181825;
        color: #cdd6f4;
    }

    Footer {
        background: #11111b;
        color: #a6adc8;
    }

    #columns {
        height: 1fr;
        background: #1e1e2e;
    }

    .pane {
        background: #181825;
        border: solid #45475a;
        padding: 0 1;
    }

    #left {
        width: 25%;
    }

    #middle {
        width: 35%;
    }

    #right {
        width: 40%;
        overflow-y: auto;
        scrollbar-background: #181825;
        scrollbar-color: #cba6f7;
        scrollbar-color-hover: #f5c2e7;
    }

    #preview-content {
        width: 100%;
        color: #cdd6f4;
    }

    .pane-title {
        text-style: bold;
        color: #cba6f7;
        height: 1;
    }

    ListView {
        height: 1fr;
        background: #181825;
        color: #cdd6f4;
    }

    ListItem {
        color: #bac2de;
        background: #181825;
        padding: 0 1;
    }

    ListItem.active-row {
        background: #313244;
        color: #cdd6f4;
        text-style: bold;
    }

    ListItem.filter-all {
        color: #89b4fa;
        text-style: bold;
    }

    ListItem.filter-category {
        color: #cba6f7;
        text-style: bold;
    }

    ListItem.filter-feed {
        color: #94e2d5;
    }

    ListItem.item-unread {
        color: #cdd6f4;
        text-style: bold;
    }

    ListItem.item-read {
        color: #6c7086;
    }

    ListItem.item-starred {
        color: #f9e2af;
        text-style: bold;
    }

    ListItem.item-unread.item-starred {
        color: #f9e2af;
    }
    """

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__()
        self.config = load_config()
        self.language = self.config.app.language
        self.db_path = db_path or get_data_dir() / self.config.storage.database
        self.filters: list[FeedFilter] = []
        self.items: list[Item] = []
        self.current_filter = FeedFilter("All")
        self.current_item_id: int | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="columns"):
            with Static(classes="pane", id="left"):
                yield Label(translate("tui_left", self.language), classes="pane-title")
                yield ListView(id="feed-list")
            with Static(classes="pane", id="middle"):
                yield Label(translate("tui_middle", self.language), classes="pane-title")
                yield ListView(id="item-list")
            with VerticalScroll(classes="pane", id="right"):
                yield Static(translate("tui_right", self.language), id="preview-content")
        yield Footer()

    async def on_mount(self) -> None:
        self.query_one("#feed-list", ListView).focus()
        await self.reload_all()

    async def reload_all(self) -> None:
        await self.load_filters()
        await self.load_items()

    async def load_filters(self) -> None:
        feed_list = self.query_one("#feed-list", ListView)
        await feed_list.clear()

        if not self.db_path.exists():
            self.filters = [FeedFilter("All")]
            await feed_list.append(ListItem(Label("All", markup=False), classes="filter-all"))
            self.update_preview("Database not found. Run `feedcopilot init` first.")
            return

        with get_session(self.db_path) as session:
            feeds = list_feeds(session)

        self.filters = build_filters(feeds)
        for feed_filter in self.filters:
            list_item = ListItem(
                Label(feed_filter.label, markup=False),
                classes=f"filter-{feed_filter.kind}",
            )
            list_item.feed_filter = feed_filter
            await feed_list.append(list_item)

    async def load_items(self, feed_filter: FeedFilter | None = None) -> None:
        if feed_filter is not None:
            self.current_filter = feed_filter

        item_list = self.query_one("#item-list", ListView)
        await item_list.clear()

        if not self.db_path.exists():
            self.items = []
            self.update_preview("No database loaded.")
            return

        with get_session(self.db_path) as session:
            self.items = list_items(
                session,
                feed_id=self.current_filter.feed_id,
                category=self.current_filter.category,
                limit=200,
            )

        if not self.items:
            self.current_item_id = None
            await item_list.append(ListItem(Label("No items found.", markup=False), disabled=True))
            self.update_preview("No items found.")
            return

        for item in self.items:
            classes = "item-read" if item.is_read else "item-unread"
            if item.is_starred:
                classes += " item-starred"
            list_item = ListItem(Label(format_item_label(item), markup=False), classes=classes)
            list_item.item_id = item.id
            await item_list.append(list_item)

        self.current_item_id = self.items[0].id
        self.update_preview(render_item_preview(self.items[0]))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        for list_item in event.list_view.query(ListItem):
            list_item.remove_class("active-row")
        if event.item is not None:
            event.item.add_class("active-row")

        if event.list_view.id != "item-list" or event.item is None:
            return
        item_id = getattr(event.item, "item_id", None)
        if item_id is None:
            return
        item = self.find_loaded_item(item_id)
        if item is not None:
            self.current_item_id = item.id
            self.update_preview(render_item_preview(item))

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "feed-list":
            feed_filter = getattr(event.item, "feed_filter", None)
            if feed_filter is not None:
                await self.load_items(feed_filter)
                self.query_one("#item-list", ListView).focus()
            return

        if event.list_view.id == "item-list":
            await self.mark_current_read(True)

    def action_cursor_down(self) -> None:
        if isinstance(self.focused, ListView):
            self.focused.action_cursor_down()

    def action_cursor_up(self) -> None:
        if isinstance(self.focused, ListView):
            self.focused.action_cursor_up()

    def action_focus_left(self) -> None:
        self.query_one("#feed-list", ListView).focus()

    def action_focus_right(self) -> None:
        self.query_one("#item-list", ListView).focus()

    def action_select(self) -> None:
        if isinstance(self.focused, ListView):
            self.focused.action_select_cursor()

    async def action_toggle_read(self) -> None:
        item = self.current_item()
        if item is not None:
            await self.mark_current_read(not item.is_read)

    async def action_toggle_star(self) -> None:
        item = self.current_item()
        if item is None or item.id is None:
            return
        with get_session(self.db_path) as session:
            updated = toggle_star(session, item.id)
        if updated is not None:
            self.notify("Starred" if updated.is_starred else "Unstarred")
        await self.load_items()

    async def action_open_item(self) -> None:
        item = self.current_item()
        if item is None:
            return
        if item.id is not None:
            await self.mark_current_read(True)
        webbrowser.open(item.link)

    async def action_fetch(self) -> None:
        if not self.db_path.exists():
            self.notify("Database not found.", severity="warning")
            return
        with get_session(self.db_path) as session:
            total, new = fetch_enabled_feeds(
                session,
                timeout=self.config.fetch.timeout,
                user_agent=self.config.fetch.user_agent,
                proxy=self.config.fetch.proxy,
            )
        self.notify(f"Fetched {total} items, {new} new.")
        await self.reload_all()

    def action_show_help(self) -> None:
        self.update_preview(
            "\n".join(
                [
                    "Keyboard shortcuts",
                    "",
                    "j/k: move",
                    "h/l: switch column",
                    "enter: select/read",
                    "r: toggle read",
                    "s: toggle star",
                    "o: open link",
                    "f: fetch",
                    "q: quit",
                ]
            )
        )

    async def mark_current_read(self, is_read: bool) -> None:
        item = self.current_item()
        if item is None or item.id is None:
            return
        with get_session(self.db_path) as session:
            mark_read(session, item.id, is_read)
        await self.load_items()

    def current_item(self) -> Item | None:
        if self.current_item_id is None:
            return None
        return self.find_loaded_item(self.current_item_id)

    def find_loaded_item(self, item_id: int) -> Item | None:
        return next((item for item in self.items if item.id == item_id), None)

    def update_preview(self, text: str) -> None:
        self.query_one("#preview-content", Static).update(text)
        self.query_one("#right", VerticalScroll).scroll_home(animate=False)


def build_filters(feeds: list[Feed]) -> list[FeedFilter]:
    filters = [FeedFilter("All")]
    seen_categories: set[str] = set()
    for feed in feeds:
        if feed.category not in seen_categories:
            filters.append(
                FeedFilter(f"[Category] {feed.category}", category=feed.category, kind="category")
            )
            seen_categories.add(feed.category)
        if feed.id is not None:
            filters.append(FeedFilter(f"  {feed.title}", feed_id=feed.id, kind="feed"))
    return filters


def format_item_label(item: Item) -> str:
    read_marker = "x" if item.is_read else " "
    star_marker = "*" if item.is_starred else " "
    return f"[{read_marker}][{star_marker}] {item.title}"


def render_item_preview(item: Item) -> str:
    lines = [
        item.title,
        "",
        f"Link: {item.link}",
        f"Published: {item.published_at or ''}",
        f"Read: {'yes' if item.is_read else 'no'}",
        f"Starred: {'yes' if item.is_starred else 'no'}",
        "",
    ]
    if item.author:
        lines.insert(2, f"Author: {item.author}")
    if item.summary:
        lines.extend(["Summary:", item.summary, ""])
    if item.content:
        lines.extend(["Content:", item.content])
    return "\n".join(lines)
