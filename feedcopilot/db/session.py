"""Database engine/session helpers."""

from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine


def create_db_engine(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_db(db_path: Path) -> None:
    engine = create_db_engine(db_path)
    SQLModel.metadata.create_all(engine)


def get_session(db_path: Path) -> Session:
    engine = create_db_engine(db_path)
    return Session(engine)
