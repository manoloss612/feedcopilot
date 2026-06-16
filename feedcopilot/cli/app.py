"""FeedCopilot CLI entry point."""

import sys
import webbrowser
from datetime import timedelta
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy.exc import IntegrityError

from feedcopilot.ai.external_command import run_external_command
from feedcopilot.core.backup import create_backup, restore_backup
from feedcopilot.core.config import (
    ensure_config,
    get_config_path,
    get_data_dir,
    load_config,
    save_config,
    set_config_value,
)
from feedcopilot.core.i18n import translate
from feedcopilot.db.repository import (
    clear_feed_items,
    clear_read_items,
    create_feed,
    delete_feed,
    delete_item,
    get_feed,
    list_digest_items,
    list_feeds,
    list_items,
    mark_read,
    search_items,
    toggle_star,
    update_feed,
)
from feedcopilot.db.session import get_session, init_db
from feedcopilot.exporters.json_export import export_json, import_json
from feedcopilot.exporters.markdown import render_digest
from feedcopilot.exporters.opml import export_opml, import_opml
from feedcopilot.rss.fetcher import fetch_enabled_feeds
from feedcopilot.scheduler.manager import (
    create_daily_schedule,
    install_schedule,
    read_schedule,
    remove_schedule,
    uninstall_schedule,
)
from feedcopilot.tui.app import FeedCopilotTUI

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")

app = typer.Typer(help="FeedCopilot: local-first RSS reader with TUI and agent-friendly CLI.")
feed_app = typer.Typer(help="Manage RSS feeds.")
config_app = typer.Typer(help="Manage configuration.")
item_app = typer.Typer(help="Manage RSS items.")
import_app = typer.Typer(help="Import data.")
export_app = typer.Typer(help="Export data.")
ai_app = typer.Typer(help="Run external AI commands.")
backup_app = typer.Typer(help="Create and restore backups.")
schedule_app = typer.Typer(help="Manage scheduled jobs.")

app.add_typer(feed_app, name="feed")
app.add_typer(config_app, name="config")
app.add_typer(item_app, name="item")
app.add_typer(import_app, name="import")
app.add_typer(export_app, name="export")
app.add_typer(ai_app, name="ai")
app.add_typer(backup_app, name="backup")
app.add_typer(schedule_app, name="schedule")

console = Console()


def main() -> None:
    """Run the FeedCopilot command-line app."""
    app()


@app.command()
def init() -> None:
    """Initialize FeedCopilot config directory and database."""
    config_path = ensure_config()
    config = load_config(config_path)
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / config.storage.markdown_dir).mkdir(parents=True, exist_ok=True)
    (data_dir / config.storage.backup_dir).mkdir(parents=True, exist_ok=True)
    (data_dir / config.storage.export_dir).mkdir(parents=True, exist_ok=True)
    init_db(data_dir / config.storage.database)
    console.print(f"Config: {config_path}")
    console.print(f"Data: {data_dir}")
    console.print(f"[bold green]{translate('initialized', config.app.language)}[/bold green]")


@app.command()
def fetch(
    feed_id: int | None = typer.Option(None, "--feed", help="Fetch one feed by id."),
    category: str | None = typer.Option(None, "--category", help="Fetch feeds in one category."),
    full_text: bool = typer.Option(
        False,
        "--full-text",
        help="Reserved for future full-text fetching.",
    ),
) -> None:
    """Fetch updates from enabled RSS feeds."""
    config = load_config()
    db_path = get_data_dir() / config.storage.database
    if not db_path.exists():
        raise typer.BadParameter("Database not found. Run `feedcopilot init` first.")
    with get_session(db_path) as session:
        total, new = fetch_enabled_feeds(
            session,
            timeout=config.fetch.timeout,
            user_agent=config.fetch.user_agent,
            feed_id=feed_id,
            category=category,
            proxy=config.fetch.proxy,
        )
    suffix = " Full-text fetching is not implemented yet." if full_text else ""
    console.print(f"Fetched {total} items, {new} new.{suffix}")


@app.command()
def tui() -> None:
    """Launch the three-column TUI reader."""
    FeedCopilotTUI().run()


@app.command()
def digest(
    since: str = typer.Option("24h", help="Time range, e.g. 24h, 7d."),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write digest to a Markdown file.",
    ),
    category: str | None = typer.Option(None, "--category"),
    language: str | None = typer.Option(None, "--language"),
    unread: bool = typer.Option(False, "--unread"),
    starred: bool = typer.Option(False, "--starred"),
) -> None:
    """Generate a Markdown digest."""
    content = _build_digest_content(
        since=since,
        category=category,
        language=language,
        unread=unread,
        starred=starred,
    )
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(content, encoding="utf-8")
        console.print(f"Digest written to {output}")
    else:
        console.print(content, markup=False)


@feed_app.command("add")
def feed_add(
    url: str,
    category: str = typer.Option("General", "--category", "-c"),
    language: str = typer.Option("en", "--language", "-l"),
) -> None:
    """Add a new RSS/Atom feed."""
    config = load_config()
    db_path = _ensure_database(config.storage.database)
    with get_session(db_path) as session:
        feed = create_feed(session, url=url, category=category, language=language)
    console.print(f"Added feed #{feed.id}: {feed.url} [{feed.category}, {feed.language}]")


@feed_app.command("list")
def feed_list(
    category: str | None = typer.Option(None, "--category"),
    disabled: bool = typer.Option(False, "--disabled", help="Show only disabled feeds."),
) -> None:
    """List feeds."""
    config = load_config()
    db_path = _ensure_database(config.storage.database)
    with get_session(db_path) as session:
        feeds = list_feeds(session, category=category, include_disabled=True)
    if disabled:
        feeds = [feed for feed in feeds if not feed.enabled]
    if not feeds:
        console.print(translate("no_feeds", load_config().app.language))
        return
    table = Table("ID", "Title", "URL", "Category", "Language", "Enabled")
    for feed in feeds:
        table.add_row(
            str(feed.id),
            feed.title,
            feed.url,
            feed.category,
            feed.language,
            "yes" if feed.enabled else "no",
        )
    console.print(table)


@feed_app.command("remove")
def feed_remove(
    feed_id: int,
    delete_items: bool = typer.Option(False, "--delete-items"),
    keep_items: bool = typer.Option(False, "--keep-items"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Remove a feed."""
    if delete_items and keep_items:
        raise typer.BadParameter("Use either --delete-items or --keep-items, not both.")
    if not yes and not typer.confirm("Remove this feed?"):
        raise typer.Abort()
    config = load_config()
    with get_session(_ensure_database(config.storage.database)) as session:
        deleted = delete_feed(session, feed_id, delete_items=delete_items)
    console.print(
        translate("feed_removed" if deleted else "feed_not_found", load_config().app.language)
    )


@feed_app.command("enable")
def feed_enable(feed_id: int) -> None:
    """Enable a feed."""
    _set_feed_enabled(feed_id, True)


@feed_app.command("disable")
def feed_disable(feed_id: int) -> None:
    """Disable a feed."""
    _set_feed_enabled(feed_id, False)


@feed_app.command("update")
def feed_update(
    feed_id: int,
    url: str | None = typer.Option(None, "--url", help="New feed URL."),
    category: str | None = typer.Option(None, "--category", "-c", help="New category."),
    language: str | None = typer.Option(None, "--language", "-l", help="New language."),
) -> None:
    """Update a feed's url, category, or language."""
    changes: dict[str, str] = {}
    if url is not None:
        changes["url"] = url
    if category is not None:
        changes["category"] = category
    if language is not None:
        changes["language"] = language
    if not changes:
        lang = load_config().app.language
        console.print(translate("feed_update_no_changes", lang))
        raise typer.BadParameter(
            "At least one of --url, --category, or --language must be provided."
        )

    config = load_config()
    with get_session(_ensure_database(config.storage.database)) as session:
        feed = update_feed(session, feed_id, **changes)

    lang = load_config().app.language
    if feed is None:
        console.print(translate("feed_not_found", lang))
        raise typer.Exit(code=1)

    console.print(
        translate(
            "feed_updated",
            lang,
            id=feed.id,
            url=feed.url,
            category=feed.category,
            lang=feed.language,
        )
    )


@feed_app.command("health")
def feed_health(feed_id: int | None = None) -> None:
    """Show feed health."""
    config = load_config()
    with get_session(_ensure_database(config.storage.database)) as session:
        feeds = [get_feed(session, feed_id)] if feed_id else list_feeds(session)
        feeds = [feed for feed in feeds if feed is not None]
    if not feeds:
        console.print("No feeds found.")
        return
    table = Table("ID", "Title", "Last Success", "Failures", "Last Error")
    for feed in feeds:
        table.add_row(
            str(feed.id),
            feed.title,
            str(feed.last_success_at or ""),
            str(feed.failure_count),
            feed.last_error or "",
        )
    console.print(table)


@config_app.command("path")
def config_path() -> None:
    """Print the active config path."""
    console.print(str(get_config_path()))


@config_app.command("show")
def config_show() -> None:
    """Print the active configuration as TOML."""
    config_path = ensure_config()
    console.print(config_path.read_text(encoding="utf-8"), markup=False)


@config_app.command("set")
def config_set(key: str, value: str) -> None:
    """Set a configuration value by SECTION.KEY."""
    config_path = ensure_config()
    try:
        config = set_config_value(load_config(config_path), key, value)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    save_config(config, config_path)
    console.print(f"Set {key} = {value}")


@item_app.command("list")
def item_list(
    unread: bool = typer.Option(False, "--unread"),
    starred: bool = typer.Option(False, "--starred"),
    category: str | None = typer.Option(None, "--category"),
    language: str | None = typer.Option(None, "--language"),
) -> None:
    """List RSS items."""
    config = load_config()
    db_path = _ensure_database(config.storage.database)
    with get_session(db_path) as session:
        items = list_items(
            session,
            unread=unread,
            starred=starred,
            category=category,
            language=language,
        )
    if not items:
        console.print(translate("no_items", load_config().app.language))
        return
    table = Table("ID", "Title", "Link", "Read", "Starred")
    for item in items:
        table.add_row(
            str(item.id),
            item.title,
            item.link,
            "yes" if item.is_read else "no",
            "yes" if item.is_starred else "no",
        )
    console.print(table)


@item_app.command("read")
def item_read(item_id: int) -> None:
    """Show one item and mark it read."""
    config = load_config()
    with get_session(_ensure_database(config.storage.database)) as session:
        item = mark_read(session, item_id, True)
    if item is None:
        console.print(translate("item_not_found", load_config().app.language))
        return
    console.print(f"[bold]{item.title}[/bold]")
    console.print(item.link)
    if item.summary:
        console.print(item.summary)


@item_app.command("open")
def item_open(item_id: int) -> None:
    """Open one item in the default browser."""
    config = load_config()
    with get_session(_ensure_database(config.storage.database)) as session:
        item = mark_read(session, item_id, True)
    if item is None:
        console.print(translate("item_not_found", load_config().app.language))
        return
    webbrowser.open(item.link)
    console.print(f"Opened {item.link}")


@item_app.command("mark-read")
def item_mark_read(item_id: int) -> None:
    """Mark one item read."""
    _set_item_read(item_id, True)


@item_app.command("mark-unread")
def item_mark_unread(item_id: int) -> None:
    """Mark one item unread."""
    _set_item_read(item_id, False)


@item_app.command("star")
def item_star(item_id: int) -> None:
    """Star one item."""
    _set_item_star(item_id, True)


@item_app.command("unstar")
def item_unstar(item_id: int) -> None:
    """Unstar one item."""
    _set_item_star(item_id, False)


@item_app.command("delete")
def item_delete(
    item_id: int,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Delete one item."""
    if not yes and not typer.confirm("Delete this item?"):
        raise typer.Abort()
    config = load_config()
    with get_session(_ensure_database(config.storage.database)) as session:
        deleted = delete_item(session, item_id)
    console.print("Item deleted." if deleted else "Item not found.")


@item_app.command("clear-read")
def item_clear_read(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Delete all read items."""
    if not yes and not typer.confirm("Delete all read items?"):
        raise typer.Abort()
    config = load_config()
    with get_session(_ensure_database(config.storage.database)) as session:
        count = clear_read_items(session)
    console.print(f"Deleted {count} read items.")


@item_app.command("clear-feed")
def item_clear_feed(
    feed_id: int,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Delete all items for one feed."""
    if not yes and not typer.confirm("Delete all items for this feed?"):
        raise typer.Abort()
    config = load_config()
    with get_session(_ensure_database(config.storage.database)) as session:
        count = clear_feed_items(session, feed_id)
    console.print(f"Deleted {count} feed items.")


@app.command()
def search(
    query: str,
    category: str | None = typer.Option(None, "--category"),
    language: str | None = typer.Option(None, "--language"),
) -> None:
    """Search items."""
    config = load_config()
    with get_session(_ensure_database(config.storage.database)) as session:
        items = search_items(session, query, category=category, language=language)
    if not items:
        console.print(translate("no_items", load_config().app.language))
        return
    table = Table("ID", "Title", "Link")
    for item in items:
        table.add_row(str(item.id), item.title, item.link)
    console.print(table)


@import_app.command("opml")
def import_opml_command(path: Path) -> None:
    """Import feeds from OPML."""
    feeds = import_opml(path)
    config = load_config()
    imported = 0
    skipped = 0
    with get_session(_ensure_database(config.storage.database)) as session:
        for feed_data in feeds:
            try:
                create_feed(session, **feed_data)
                imported += 1
            except IntegrityError:
                session.rollback()
                skipped += 1
    console.print(f"Imported {imported} feeds, skipped {skipped}.")


@export_app.command("opml")
def export_opml_command(
    output: Annotated[Path, typer.Option("--output", "-o")],
) -> None:
    """Export feeds to OPML."""
    config = load_config()
    with get_session(_ensure_database(config.storage.database)) as session:
        feeds = [feed.model_dump(mode="json") for feed in list_feeds(session)]
    path = export_opml(feeds, output)
    console.print(f"Exported OPML to {path}")


@import_app.command("json")
def import_json_command(path: Path) -> None:
    """Import FeedCopilot JSON data."""
    config = load_config()
    with get_session(_ensure_database(config.storage.database)) as session:
        feed_count, item_count = import_json(session, path)
    console.print(f"Imported {feed_count} feeds and {item_count} items.")


@export_app.command("json")
def export_json_command(
    output: Annotated[Path, typer.Option("--output", "-o")],
) -> None:
    """Export FeedCopilot data as JSON."""
    config = load_config()
    with get_session(_ensure_database(config.storage.database)) as session:
        path = export_json(session, output)
    console.print(f"Exported JSON to {path}")


@ai_app.command("run")
def ai_run(since: str = typer.Option("24h", "--since")) -> None:
    """Run configured external AI command with digest input."""
    config = load_config()
    if not config.ai.enabled:
        raise typer.BadParameter("AI is disabled. Set ai.enabled true first.")
    content = _build_digest_content(since=since)
    output = run_external_command(config.ai.command, content)
    console.print(output, markup=False)


@backup_app.command("create")
def backup_create(output: Annotated[Path | None, typer.Option("--output", "-o")] = None) -> None:
    """Create a backup package."""
    path = create_backup(output)
    console.print(f"Backup created: {path}")


@backup_app.command("restore")
def backup_restore(
    path: str,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Restore from a backup package."""
    if not yes and not typer.confirm("Restore will overwrite local data. Continue?"):
        raise typer.Abort()
    restore_path = restore_backup(path)
    console.print(f"Restored backup into {restore_path}")


@schedule_app.command("daily")
def schedule_daily(
    time: str = typer.Option("08:00", "--time"),
    fetch: bool = typer.Option(True, "--fetch/--no-fetch"),
    digest: bool = typer.Option(False, "--digest/--no-digest"),
    ai: bool = typer.Option(False, "--ai/--no-ai"),
    install: bool = typer.Option(False, "--install", help="Install the OS-level schedule."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip install confirmation."),
) -> None:
    """Create or update a daily scheduled task using an interactive wizard."""
    path = create_daily_schedule(time=time, fetch=fetch, digest=digest, ai=ai)
    console.print(f"Schedule saved: {path}")
    if install:
        if not yes and not typer.confirm("Install this schedule into the operating system?"):
            console.print("OS-level schedule not installed.")
            return
        console.print(install_schedule())


@schedule_app.command("status")
def schedule_status() -> None:
    """Show schedule status."""
    content = read_schedule()
    console.print(content or "No schedule configured.", markup=False)


@schedule_app.command("remove")
def schedule_remove(
    uninstall: bool = typer.Option(True, "--uninstall/--keep-os-task"),
) -> None:
    """Remove schedule metadata and the OS-level task when possible."""
    if uninstall:
        try:
            console.print(uninstall_schedule())
        except RuntimeError as exc:
            console.print(f"OS-level schedule removal skipped: {exc}")
    removed = remove_schedule()
    console.print("Schedule removed." if removed else "No schedule configured.")


def _ensure_database(database_name: str) -> Path:
    db_path = get_data_dir() / database_name
    if not db_path.exists():
        init_db(db_path)
    return db_path


def _build_digest_content(
    since: str = "24h",
    category: str | None = None,
    language: str | None = None,
    unread: bool = False,
    starred: bool = False,
) -> str:
    config = load_config()
    since_dt = _parse_since(since)
    with get_session(_ensure_database(config.storage.database)) as session:
        rows = list_digest_items(
            session,
            since=since_dt,
            unread=unread,
            starred=starred,
            category=category,
            language=language,
        )
    items = [
        {
            "title": item.title,
            "link": item.link,
            "summary": item.summary,
            "category": feed.category,
            "published_at": item.published_at,
            "interest_score": item.interest_score,
        }
        for item, feed in rows
    ]
    return render_digest(items)


def _parse_since(value: str) -> object:
    from feedcopilot.db.models import utc_now

    number = int(value[:-1]) if value[:-1].isdigit() else 24
    unit = value[-1].lower()
    if unit == "h":
        return utc_now() - timedelta(hours=number)
    if unit == "d":
        return utc_now() - timedelta(days=number)
    return None


def _set_feed_enabled(feed_id: int, enabled: bool) -> None:
    config = load_config()
    with get_session(_ensure_database(config.storage.database)) as session:
        feed = update_feed(session, feed_id, enabled=enabled)
    if feed is None:
        console.print("Feed not found.")
        return
    console.print(f"Feed {'enabled' if enabled else 'disabled'}.")


def _set_item_read(item_id: int, is_read: bool) -> None:
    config = load_config()
    with get_session(_ensure_database(config.storage.database)) as session:
        item = mark_read(session, item_id, is_read)
    if item is None:
        console.print("Item not found.")
        return
    console.print(f"Item marked {'read' if is_read else 'unread'}.")


def _set_item_star(item_id: int, is_starred: bool) -> None:
    config = load_config()
    with get_session(_ensure_database(config.storage.database)) as session:
        item = toggle_star(session, item_id, is_starred)
    if item is None:
        console.print("Item not found.")
        return
    console.print(f"Item {'starred' if is_starred else 'unstarred'}.")


if __name__ == "__main__":
    main()
