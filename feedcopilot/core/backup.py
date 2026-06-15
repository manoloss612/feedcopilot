"""Backup and restore helpers."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from feedcopilot.core.config import get_config_path, get_data_dir, load_config
from feedcopilot.db.repository import list_feeds
from feedcopilot.db.session import get_session
from feedcopilot.exporters.opml import export_opml


def create_backup(output: str | Path | None = None) -> Path:
    config = load_config()
    data_dir = get_data_dir()
    backup_dir = data_dir / config.storage.backup_dir
    backup_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(output) if output else backup_dir / "feedcopilot-backup.zip"

    db_path = data_dir / config.storage.database
    opml_path = backup_dir / "feeds.opml"
    if db_path.exists():
        with get_session(db_path) as session:
            feeds = [feed.model_dump(mode="json") for feed in list_feeds(session)]
        export_opml(feeds, opml_path)

    with ZipFile(output_path, "w", ZIP_DEFLATED) as archive:
        config_path = get_config_path()
        if config_path.exists():
            archive.write(config_path, "config.toml")
        if db_path.exists():
            archive.write(db_path, "feedcopilot.db")
        if opml_path.exists():
            archive.write(opml_path, "feeds.opml")
        summaries_dir = data_dir / config.storage.markdown_dir
        if summaries_dir.exists():
            for path in summaries_dir.rglob("*"):
                if path.is_file():
                    archive.write(path, Path("summaries") / path.relative_to(summaries_dir))
    return output_path


def restore_backup(path: str | Path) -> Path:
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    with ZipFile(path) as archive:
        for member in archive.namelist():
            if member == "config.toml":
                get_config_path().parent.mkdir(parents=True, exist_ok=True)
                get_config_path().write_bytes(archive.read(member))
            elif member == "feedcopilot.db" or member.startswith("summaries/"):
                archive.extract(member, data_dir)
    return data_dir
