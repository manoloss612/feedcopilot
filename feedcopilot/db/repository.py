"""Repository functions for FeedCopilot data."""

from datetime import datetime

from sqlmodel import Session, col, or_, select

from feedcopilot.db.models import AppMeta, Feed, FetchLog, Item, utc_now


def create_feed(
    session: Session,
    url: str,
    title: str | None = None,
    site_url: str | None = None,
    category: str = "General",
    language: str = "en",
) -> Feed:
    feed = Feed(
        title=title or url,
        url=url,
        site_url=site_url,
        category=category,
        language=language,
    )
    session.add(feed)
    session.commit()
    session.refresh(feed)
    return feed


def list_feeds(
    session: Session,
    category: str | None = None,
    include_disabled: bool = True,
) -> list[Feed]:
    statement = select(Feed)
    if category:
        statement = statement.where(Feed.category == category)
    if not include_disabled:
        statement = statement.where(Feed.enabled == True)  # noqa: E712
    statement = statement.order_by(Feed.category, Feed.title)
    return list(session.exec(statement).all())


def get_feed(session: Session, feed_id: int) -> Feed | None:
    return session.get(Feed, feed_id)


def update_feed(session: Session, feed_id: int, **changes: object) -> Feed | None:
    feed = get_feed(session, feed_id)
    if feed is None:
        return None
    for key, value in changes.items():
        if hasattr(feed, key):
            setattr(feed, key, value)
    feed.updated_at = utc_now()
    session.add(feed)
    session.commit()
    session.refresh(feed)
    return feed


def delete_feed(session: Session, feed_id: int, delete_items: bool = False) -> bool:
    feed = get_feed(session, feed_id)
    if feed is None:
        return False
    if delete_items:
        for item in session.exec(select(Item).where(Item.feed_id == feed_id)).all():
            session.delete(item)
    session.delete(feed)
    session.commit()
    return True


def create_item_if_new(session: Session, item: Item) -> tuple[Item, bool]:
    existing = _find_duplicate_item(session, item)
    if existing is not None:
        return existing, False
    session.add(item)
    session.commit()
    session.refresh(item)
    return item, True


def list_items(
    session: Session,
    feed_id: int | None = None,
    unread: bool = False,
    starred: bool = False,
    category: str | None = None,
    language: str | None = None,
    limit: int = 50,
) -> list[Item]:
    statement = select(Item)
    if category or language:
        statement = statement.join(Feed, Feed.id == Item.feed_id)
    if feed_id is not None:
        statement = statement.where(Item.feed_id == feed_id)
    if unread:
        statement = statement.where(Item.is_read == False)  # noqa: E712
    if starred:
        statement = statement.where(Item.is_starred == True)  # noqa: E712
    if category:
        statement = statement.where(Feed.category == category)
    if language:
        statement = statement.where(Feed.language == language)
    statement = statement.order_by(col(Item.published_at).desc(), Item.id.desc()).limit(limit)
    return list(session.exec(statement).all())


def list_digest_items(
    session: Session,
    since: datetime | None = None,
    unread: bool = False,
    starred: bool = False,
    category: str | None = None,
    language: str | None = None,
    limit: int = 200,
) -> list[tuple[Item, Feed]]:
    statement = select(Item, Feed).join(Feed, Feed.id == Item.feed_id)
    if since is not None:
        statement = statement.where(
            or_(
                Item.published_at >= since,
                Item.published_at == None,  # noqa: E711
            )
        )
    if unread:
        statement = statement.where(Item.is_read == False)  # noqa: E712
    if starred:
        statement = statement.where(Item.is_starred == True)  # noqa: E712
    if category:
        statement = statement.where(Feed.category == category)
    if language:
        statement = statement.where(Feed.language == language)
    statement = statement.order_by(
        col(Item.interest_score).desc(),
        col(Item.published_at).desc(),
        Item.id.desc(),
    ).limit(limit)
    return list(session.exec(statement).all())


def search_items(
    session: Session,
    query: str,
    category: str | None = None,
    language: str | None = None,
    limit: int = 50,
) -> list[Item]:
    pattern = f"%{query}%"
    statement = (
        select(Item)
        .join(Feed, Feed.id == Item.feed_id)
        .where(
            or_(
                Item.title.ilike(pattern),
                Item.summary.ilike(pattern),
                Feed.title.ilike(pattern),
                Feed.category.ilike(pattern),
            )
        )
    )
    if category:
        statement = statement.where(Feed.category == category)
    if language:
        statement = statement.where(Feed.language == language)
    statement = statement.order_by(col(Item.published_at).desc(), Item.id.desc()).limit(limit)
    return list(session.exec(statement).all())


def mark_read(session: Session, item_id: int, is_read: bool = True) -> Item | None:
    item = session.get(Item, item_id)
    if item is None:
        return None
    item.is_read = is_read
    item.updated_at = utc_now()
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def toggle_star(session: Session, item_id: int, is_starred: bool | None = None) -> Item | None:
    item = session.get(Item, item_id)
    if item is None:
        return None
    item.is_starred = not item.is_starred if is_starred is None else is_starred
    item.updated_at = utc_now()
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def delete_item(session: Session, item_id: int) -> bool:
    item = session.get(Item, item_id)
    if item is None:
        return False
    session.delete(item)
    session.commit()
    return True


def clear_read_items(session: Session) -> int:
    items = session.exec(select(Item).where(Item.is_read == True)).all()  # noqa: E712
    count = len(items)
    for item in items:
        session.delete(item)
    session.commit()
    return count


def clear_feed_items(session: Session, feed_id: int) -> int:
    items = session.exec(select(Item).where(Item.feed_id == feed_id)).all()
    count = len(items)
    for item in items:
        session.delete(item)
    session.commit()
    return count


def create_fetch_log(
    session: Session,
    feed_id: int,
    status: str,
    started_at: datetime,
    ended_at: datetime,
    message: str | None = None,
    item_count: int = 0,
    new_item_count: int = 0,
) -> FetchLog:
    log = FetchLog(
        feed_id=feed_id,
        status=status,
        message=message,
        started_at=started_at,
        ended_at=ended_at,
        item_count=item_count,
        new_item_count=new_item_count,
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def set_app_meta(session: Session, key: str, value: str) -> AppMeta:
    meta = session.get(AppMeta, key) or AppMeta(key=key, value=value)
    meta.value = value
    session.add(meta)
    session.commit()
    session.refresh(meta)
    return meta


def _find_duplicate_item(session: Session, item: Item) -> Item | None:
    if item.guid:
        existing = session.exec(
            select(Item).where(Item.feed_id == item.feed_id, Item.guid == item.guid)
        ).first()
        if existing:
            return existing

    existing = session.exec(select(Item).where(Item.link == item.link)).first()
    if existing:
        return existing

    if item.published_at is not None:
        existing = session.exec(
            select(Item).where(
                Item.feed_id == item.feed_id,
                Item.title == item.title,
                Item.published_at == item.published_at,
            )
        ).first()
        if existing:
            return existing

    return session.exec(select(Item).where(Item.content_hash == item.content_hash)).first()
