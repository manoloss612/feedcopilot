from feedcopilot.core.config import (
    create_default_config,
    load_config,
    save_config,
    set_config_value,
)


def test_save_and_load_config(tmp_path):
    path = tmp_path / "config.toml"
    config = create_default_config()
    config.app.language = "zh"

    save_config(config, path)
    loaded = load_config(path)

    assert loaded.app.language == "zh"
    assert loaded.storage.database == "feedcopilot.db"


def test_set_config_value_converts_types():
    config = create_default_config()

    updated = set_config_value(config, "fetch.timeout", "30")
    updated = set_config_value(updated, "fetch.full_text", "true")
    updated = set_config_value(updated, "app.language", "zh")

    assert updated.fetch.timeout == 30
    assert updated.fetch.full_text is True
    assert updated.app.language == "zh"
