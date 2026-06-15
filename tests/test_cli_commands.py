from pathlib import Path

from typer.testing import CliRunner

from feedcopilot.cli import app as cli_module
from feedcopilot.cli.app import app
from feedcopilot.core import config as config_module


def isolate_app_dirs(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    config_path = config_dir / "config.toml"
    monkeypatch.setattr(config_module, "get_config_dir", lambda: config_dir)
    monkeypatch.setattr(config_module, "get_data_dir", lambda: data_dir)
    monkeypatch.setattr(config_module, "get_config_path", lambda: config_path)
    monkeypatch.setattr(cli_module, "get_data_dir", lambda: data_dir)
    monkeypatch.setattr(cli_module, "get_config_path", lambda: config_path)
    return config_path, data_dir


def test_cli_feed_item_search_digest(monkeypatch, tmp_path):
    isolate_app_dirs(monkeypatch, tmp_path)
    runner = CliRunner()

    assert runner.invoke(app, ["init"]).exit_code == 0
    assert runner.invoke(
        app,
        ["feed", "add", "https://example.com/rss.xml", "--category", "News"],
    ).exit_code == 0
    assert runner.invoke(app, ["feed", "list"]).exit_code == 0
    assert runner.invoke(app, ["feed", "disable", "1"]).exit_code == 0
    assert runner.invoke(app, ["feed", "enable", "1"]).exit_code == 0
    assert runner.invoke(app, ["feed", "health"]).exit_code == 0

    from feedcopilot.db.models import Item
    from feedcopilot.db.repository import create_item_if_new
    from feedcopilot.db.session import get_session

    with get_session(tmp_path / "data" / "feedcopilot.db") as session:
        create_item_if_new(
            session,
            Item(
                feed_id=1,
                title="Python News",
                link="https://example.com/python",
                summary="RSS summary",
                content_hash="hash",
            ),
        )

    assert runner.invoke(app, ["item", "list", "--unread"]).exit_code == 0
    assert runner.invoke(app, ["search", "Python"]).exit_code == 0
    assert runner.invoke(app, ["item", "mark-read", "1"]).exit_code == 0
    assert runner.invoke(app, ["item", "mark-unread", "1"]).exit_code == 0
    assert runner.invoke(app, ["item", "star", "1"]).exit_code == 0
    assert runner.invoke(app, ["item", "unstar", "1"]).exit_code == 0
    digest = runner.invoke(app, ["digest", "--since", "7d"])
    assert digest.exit_code == 0
    assert "FeedCopilot Digest" in digest.output


def test_cli_schedule_commands(monkeypatch, tmp_path):
    isolate_app_dirs(monkeypatch, tmp_path)
    runner = CliRunner()

    assert runner.invoke(app, ["schedule", "daily", "--time", "09:30"]).exit_code == 0
    status = runner.invoke(app, ["schedule", "status"])
    assert status.exit_code == 0
    assert "09:30" in status.output
    assert runner.invoke(app, ["schedule", "remove"]).exit_code == 0


def test_cli_export_import_commands(monkeypatch, tmp_path):
    isolate_app_dirs(monkeypatch, tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["init"])
    runner.invoke(app, ["feed", "add", "https://example.com/rss.xml"])

    opml_path = tmp_path / "feeds.opml"
    json_path = tmp_path / "data.json"

    assert runner.invoke(app, ["export", "opml", "--output", str(opml_path)]).exit_code == 0
    assert runner.invoke(app, ["export", "json", "--output", str(json_path)]).exit_code == 0
    assert opml_path.exists()
    assert json_path.exists()

    imported_opml = runner.invoke(app, ["import", "opml", str(opml_path)])
    assert imported_opml.exit_code == 0


def test_cli_backup_create(monkeypatch, tmp_path):
    isolate_app_dirs(monkeypatch, tmp_path)
    monkeypatch.setattr("feedcopilot.core.backup.get_data_dir", lambda: tmp_path / "data")
    monkeypatch.setattr(
        "feedcopilot.core.backup.get_config_path",
        lambda: tmp_path / "config" / "config.toml",
    )
    runner = CliRunner()
    runner.invoke(app, ["init"])
    output = tmp_path / "backup.zip"

    result = runner.invoke(app, ["backup", "create", "--output", str(output)])

    assert result.exit_code == 0
    assert output.exists()


def test_cli_tui_command_invokes_app(monkeypatch):
    called = False

    def fake_run(self):
        nonlocal called
        called = True

    monkeypatch.setattr("feedcopilot.cli.app.FeedCopilotTUI.run", fake_run)

    result = CliRunner().invoke(app, ["tui"])

    assert result.exit_code == 0
    assert called is True


def test_path_helper_type():
    assert isinstance(Path("."), Path)
