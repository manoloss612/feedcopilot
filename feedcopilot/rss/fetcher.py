"""RSS fetching and parsing."""

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime

import feedparser
import httpx
from dateutil import parser as date_parser
from sqlmodel import Session

from feedcopilot.db.models import Item, utc_now
from feedcopilot.db.repository import create_fetch_log, create_item_if_new, list_feeds, update_feed


@dataclass
class ParsedItem:
    title: str
    link: str
    guid: str | None
    author: str | None
    published_at: datetime | None
    summary: str | None
    content: str | None
    content_hash: str


def compute_hash(*parts: str | None) -> str:
    raw = "\n".join(p or "" for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _resolve_proxy(proxy: str | None) -> str:
    """Resolve effective proxy URL.

    Priority: explicit argument > HTTPS_PROXY > HTTP_PROXY > "".
    Returning "" means "no proxy" (httpx.Client uses a default transport).
    """
    if proxy:
        return proxy
    return os.environ.get("FEEDCOPILOT_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or ""


def fetch_feed(
    url: str,
    timeout: int = 20,
    user_agent: str = "FeedCopilot/0.1",
    proxy: str | None = None,
):
    headers = {"User-Agent": user_agent}
    proxy_url = _resolve_proxy(proxy)
    client_kwargs: dict = {"timeout": timeout, "follow_redirects": True, "headers": headers}
    if proxy_url:
        client_kwargs["transport"] = httpx.HTTPTransport(proxy=proxy_url)
    with httpx.Client(**client_kwargs) as client:
        response = client.get(url)
        response.raise_for_status()
    return feedparser.parse(response.content)


def parse_feed_content(content: bytes | str):
    return feedparser.parse(content)


def normalize_items(parsed_feed) -> list[ParsedItem]:
    items: list[ParsedItem] = []
    for entry in parsed_feed.entries:
        title = _get(entry, "title") or "Untitled"
        link = _get(entry, "link") or ""
        guid = _get(entry, "id") or _get(entry, "guid")
        author = _get(entry, "author")
        published_at = _parse_datetime(
            _get(entry, "published")
            or _get(entry, "updated")
            or _get(entry, "created")
        )
        summary = _get(entry, "summary") or _get(entry, "description")
        content = _entry_content(entry)
        content_hash = compute_hash(title, link, guid, summary, content)
        items.append(
            ParsedItem(
                title=title,
                link=link,
                guid=guid,
                author=author,
                published_at=published_at,
                summary=summary,
                content=content,
                content_hash=content_hash,
            )
        )
    return items


def fetch_enabled_feeds(
    session: Session,
    timeout: int = 20,
    user_agent: str = "FeedCopilot/0.1",
    feed_id: int | None = None,
    category: str | None = None,
    proxy: str | None = None,
) -> tuple[int, int]:
    total_items = 0
    total_new_items = 0
    feeds = list_feeds(session, category=category, include_disabled=False)
    if feed_id is not None:
        feeds = [feed for feed in feeds if feed.id == feed_id]

    for feed in feeds:
        if feed.id is None:
            continue
        started_at = utc_now()
        try:
            parsed = fetch_feed(feed.url, timeout=timeout, user_agent=user_agent, proxy=proxy)
            parsed_items = normalize_items(parsed)
            new_count = 0
            for parsed_item in parsed_items:
                _, created = create_item_if_new(
                    session,
                    Item(feed_id=feed.id, **parsed_item.__dict__),
                )
                if created:
                    new_count += 1
            now = utc_now()
            update_feed(
                session,
                feed.id,
                title=_get(parsed.feed, "title") or feed.title,
                site_url=_get(parsed.feed, "link") or feed.site_url,
                last_fetched_at=now,
                last_success_at=now,
                last_error=None,
                failure_count=0,
            )
            create_fetch_log(
                session,
                feed.id,
                "success",
                started_at,
                now,
                item_count=len(parsed_items),
                new_item_count=new_count,
            )
            total_items += len(parsed_items)
            total_new_items += new_count
        except Exception as exc:  # noqa: BLE001
            now = utc_now()
            update_feed(
                session,
                feed.id,
                last_fetched_at=now,
                last_error=str(exc),
                failure_count=feed.failure_count + 1,
            )
            create_fetch_log(session, feed.id, "failure", started_at, now, message=str(exc))
    return total_items, total_new_items


def _get(obj, key: str):
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _entry_content(entry) -> str | None:
    content = _get(entry, "content")
    if isinstance(content, list) and content:
        value = _get(content[0], "value")
        if value:
            return value
    return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = date_parser.parse(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed.tzinfo is not None:
        return parsed.replace(tzinfo=None)
    return parsed
