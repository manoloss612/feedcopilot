from feedcopilot.ai.external_command import run_external_command
from feedcopilot.core.i18n import translate
from feedcopilot.scheduler import manager
from feedcopilot.scheduler.manager import ScheduleSpec


def test_external_command_runs():
    output = run_external_command("python -c \"import sys; print(sys.stdin.read().upper())\"", "hi")

    assert "HI" in output


def test_i18n_translate():
    assert translate("initialized", "zh") == "FeedCopilot 已初始化。"
    assert translate("initialized", "en") == "FeedCopilot initialized."


def test_schedule_manager(monkeypatch, tmp_path):
    monkeypatch.setattr(manager, "get_config_dir", lambda: tmp_path)

    path = manager.create_daily_schedule(time="10:00", fetch=True, digest=True, ai=False)
    content = manager.read_schedule()
    removed = manager.remove_schedule()

    assert path.exists() is False
    assert "10:00" in content
    assert removed is True


def test_schedule_generates_linux_cron(monkeypatch, tmp_path):
    monkeypatch.setattr(manager, "get_config_dir", lambda: tmp_path)
    monkeypatch.setattr(manager, "get_data_dir", lambda: tmp_path / "data")
    monkeypatch.setattr(manager, "current_platform", lambda: "linux")

    path = manager.create_daily_schedule(time="06:15", fetch=True, digest=True, ai=False)
    cron = (tmp_path / "scheduler" / "feedcopilot.cron").read_text(encoding="utf-8")
    runner = (tmp_path / "scheduler" / "feedcopilot-daily.sh").read_text(encoding="utf-8")

    assert path.exists()
    assert "15 6 * * *" in cron
    assert "fetch" in runner
    assert "digest --since 24h" in runner


def test_schedule_generates_launchd_plist(monkeypatch, tmp_path):
    monkeypatch.setattr(manager, "get_config_dir", lambda: tmp_path)
    monkeypatch.setattr(manager, "current_platform", lambda: "macos")

    manager.create_daily_schedule(time="07:05")
    plist = (tmp_path / "scheduler" / "com.feedcopilot.daily.plist").read_text(
        encoding="utf-8"
    )

    assert "<key>Hour</key>" in plist
    assert "<integer>7</integer>" in plist
    assert "<integer>5</integer>" in plist


def test_schedule_generates_windows_runner(monkeypatch, tmp_path):
    monkeypatch.setattr(manager, "get_config_dir", lambda: tmp_path)
    monkeypatch.setattr(manager, "current_platform", lambda: "windows")

    manager.create_daily_schedule(time="08:30", fetch=True, digest=False, ai=True)
    runner = (tmp_path / "scheduler" / "feedcopilot-daily.cmd").read_text(encoding="utf-8")

    assert "@echo off" in runner
    assert "fetch" in runner
    assert "ai run --since 24h" in runner


def test_windows_install_uses_schtasks(monkeypatch, tmp_path):
    calls = []

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(args, **kwargs):
        calls.append(args)
        return Completed()

    monkeypatch.setattr(manager, "get_config_dir", lambda: tmp_path)
    monkeypatch.setattr(manager, "current_platform", lambda: "windows")
    monkeypatch.setattr(manager.subprocess, "run", fake_run)
    manager.create_daily_schedule(time="08:30")

    result = manager.install_schedule()

    assert "Windows Task Scheduler" in result
    assert calls[0][0] == "schtasks"
    assert "/Create" in calls[0]


def test_cron_block_removal():
    content = "\n".join(
        [
            "A",
            "# BEGIN FeedCopilot daily schedule",
            "* * * * * test",
            "# END FeedCopilot daily schedule",
            "B",
        ]
    )

    assert manager._remove_cron_block(content) == "A\nB"


def test_schedule_spec_time_parts():
    spec = ScheduleSpec(time="09:45")

    assert spec.hour == 9
    assert spec.minute == 45
