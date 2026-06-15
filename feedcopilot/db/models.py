"""Database models."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Feed(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    url: str = Field(index=True, unique=True)
    site_url: str | None = None
    category: str = Field(default="General", index=True)
    language: str = Field(default="en", index=True)
    enabled: bool = True

    last_fetched_at: datetime | None = None
    last_success_at: datetime | None = None
    last_error: str | None = None
    failure_count: int = 0

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    feed_id: int = Field(foreign_key="feed.id", index=True)

    title: str
    link: str = Field(index=True)
    guid: str | None = Field(default=None, index=True)
    author: str | None = None
    published_at: datetime | None = Field(default=None, index=True)
    summary: str | None = None
    content: str | None = None
    content_hash: str = Field(index=True)

    is_read: bool = Field(default=False, index=True)
    is_starred: bool = Field(default=False, index=True)
    interest_score: int = Field(default=0, index=True)

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class FetchLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    feed_id: int = Field(foreign_key="feed.id", index=True)
    status: str = Field(index=True)
    message: str | None = None
    started_at: datetime
    ended_at: datetime
    item_count: int = 0
    new_item_count: int = 0


class AppMeta(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str
