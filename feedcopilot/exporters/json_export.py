"""JSON import/export helpers."""

import json
from datetime import datetime
from pathlib import Path

from sqlmodel import Session

from feedcopilot.db.models import Feed, Item, utc_now
from feedcopilot.db.repository import create_feed, create_item_if_new, list_feeds, list_items


def export_json(session: Session, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "feeds": [_model_dump(feed) for feed in list_feeds(session)],
        "items": [_model_dump(item) for item in list_items(session, limit=10_000)],
    }
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def import_json(session: Session, path: str | Path) -> tuple[int, int]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    feed_id_map: dict[int, int] = {}
    feed_count = 0
    item_count = 0

    for feed_data in data.get("feeds", []):
        old_id = feed_data.pop("id", None)
        feed_data.pop("created_at", None)
        feed_data.pop("updated_at", None)
        feed = create_feed(session, **_feed_kwargs(feed_data))
        feed_count += 1
        if old_id is not None and feed.id is not None:
            feed_id_map[int(old_id)] = feed.id

    for item_data in data.get("items", []):
        old_feed_id = item_data.get("feed_id")
        if old_feed_id in feed_id_map:
            item_data["feed_id"] = feed_id_map[old_feed_id]
        item_data.pop("id", None)
        item_data["published_at"] = _parse_datetime(item_data.get("published_at"))
        item_data["created_at"] = _parse_datetime(item_data.get("created_at")) or utc_now()
        item_data["updated_at"] = _parse_datetime(item_data.get("updated_at")) or utc_now()
        _, created = create_item_if_new(session, Item(**item_data))
        if created:
            item_count += 1

    return feed_count, item_count


def _model_dump(model: Feed | Item) -> dict:
    return model.model_dump(mode="json")


def _feed_kwargs(data: dict) -> dict:
    return {
        "url": data["url"],
        "title": data.get("title"),
        "site_url": data.get("site_url"),
        "category": data.get("category", "General"),
        "language": data.get("language", "en"),
    }


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)
