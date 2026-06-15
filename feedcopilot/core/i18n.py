"""Lightweight i18n helpers."""

import tomllib
from importlib.resources import files


def load_messages(language: str = "en") -> dict[str, str]:
    lang = "zh" if language == "zh" else "en"
    resource = files("feedcopilot.i18n").joinpath(f"{lang}.toml")
    with resource.open("rb") as file:
        data = tomllib.load(file)
    return {str(key): str(value) for key, value in data.items()}


def translate(key: str, language: str = "en", **kwargs: object) -> str:
    messages = load_messages(language)
    text = messages.get(key, key)
    return text.format(**kwargs)
