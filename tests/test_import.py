def test_import_feedcopilot():
    import feedcopilot

    assert feedcopilot.__version__


def test_import_cli_app():
    from feedcopilot.cli.app import app

    assert app is not None


def test_cli_help_smoke():
    from typer.testing import CliRunner

    from feedcopilot.cli.app import app

    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "FeedCopilot" in result.output
