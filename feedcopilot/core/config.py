"""Configuration loading and saving."""

import tomllib
from pathlib import Path
from typing import Literal

import tomli_w
from platformdirs import user_config_dir, user_data_dir
from pydantic import BaseModel, Field

APP_NAME = "FeedCopilot"


class AppConfig(BaseModel):
    language: Literal["en", "zh"] = "en"
    theme: str = "default"


class StorageConfig(BaseModel):
    database: str = "feedcopilot.db"
    markdown_dir: str = "summaries"
    backup_dir: str = "backups"
    export_dir: str = "exports"


class FetchConfig(BaseModel):
    timeout: int = 20
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )
    full_text: bool = False
    max_concurrent: int = 5
    proxy: str = ""  # HTTP/HTTPS proxy URL, e.g. "http://127.0.0.1:8080". Empty = no proxy.
    verify_ssl: bool = True  # Verify TLS certs. False skips cert checks (e.g. CNKI).
    no_proxy: str = ""  # Comma-separated hostnames that bypass `proxy` (curl_cffi NO_PROXY).


class DigestConfig(BaseModel):
    default_since: str = "24h"
    format: Literal["markdown"] = "markdown"
    group_by: Literal["category", "feed", "language"] = "category"
    include_read: bool = False
    include_starred: bool = True


class AIConfig(BaseModel):
    enabled: bool = False
    command: str = ""
    input_mode: Literal["stdin", "file"] = "stdin"
    output_mode: Literal["stdout", "file"] = "stdout"


class InterestsConfig(BaseModel):
    keywords: list[str] = Field(default_factory=list)


class TUIConfig(BaseModel):
    layout: Literal["three_column"] = "three_column"
    show_health_status: bool = True
    preview_width: int = 40
    icon_set: Literal["ascii", "nerd", "none"] = "ascii"


class FeedCopilotConfig(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    fetch: FetchConfig = Field(default_factory=FetchConfig)
    digest: DigestConfig = Field(default_factory=DigestConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    interests: InterestsConfig = Field(default_factory=InterestsConfig)
    tui: TUIConfig = Field(default_factory=TUIConfig)


def get_config_dir() -> Path:
    return Path(user_config_dir(APP_NAME, appauthor=False))


def get_data_dir() -> Path:
    return Path(user_data_dir(APP_NAME, appauthor=False))


def get_config_path() -> Path:
    return get_config_dir() / "config.toml"


def create_default_config() -> FeedCopilotConfig:
    return FeedCopilotConfig()


def load_config(path: Path | None = None) -> FeedCopilotConfig:
    config_path = path or get_config_path()
    if not config_path.exists():
        return create_default_config()
    with config_path.open("rb") as file:
        data = tomllib.load(file)
    return FeedCopilotConfig.model_validate(data)


def save_config(config: FeedCopilotConfig, path: Path | None = None) -> Path:
    config_path = path or get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data = config.model_dump(mode="json")
    config_path.write_text(tomli_w.dumps(data), encoding="utf-8")
    return config_path


def ensure_config(path: Path | None = None) -> Path:
    config_path = path or get_config_path()
    if not config_path.exists():
        save_config(create_default_config(), config_path)
    return config_path


def set_config_value(config: FeedCopilotConfig, key: str, value: str) -> FeedCopilotConfig:
    parts = key.split(".")
    if len(parts) != 2:
        raise ValueError("Config key must use SECTION.KEY format.")

    section_name, field_name = parts
    if not hasattr(config, section_name):
        raise ValueError(f"Unknown config section: {section_name}")

    section = getattr(config, section_name)
    section_fields = section.__class__.model_fields
    if field_name not in section_fields:
        raise ValueError(f"Unknown config key: {key}")

    field = section_fields[field_name]
    converted = _convert_value(value, field.annotation)
    updated = config.model_copy(deep=True)
    setattr(getattr(updated, section_name), field_name, converted)
    return FeedCopilotConfig.model_validate(updated.model_dump())


def _convert_value(value: str, annotation: object) -> object:
    if annotation is bool:
        lowered = value.lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
        raise ValueError(f"Invalid boolean value: {value}")
    if annotation is int:
        return int(value)
    if str(annotation).startswith("list[str]"):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value
