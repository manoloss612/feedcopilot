"""Cross-platform schedule helpers."""

import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import tomli_w

from feedcopilot.core.config import get_config_dir, get_data_dir

TASK_NAME = "FeedCopilotDaily"
LAUNCHD_LABEL = "com.feedcopilot.daily"
CRON_BEGIN = "# BEGIN FeedCopilot daily schedule"
CRON_END = "# END FeedCopilot daily schedule"


@dataclass(frozen=True)
class ScheduleSpec:
    time: str = "08:00"
    fetch: bool = True
    digest: bool = False
    ai: bool = False

    @property
    def hour(self) -> int:
        return int(self.time.split(":", 1)[0])

    @property
    def minute(self) -> int:
        return int(self.time.split(":", 1)[1])


def schedule_path() -> Path:
    return get_config_dir() / "schedule.toml"


def scripts_dir() -> Path:
    return get_config_dir() / "scheduler"


def create_daily_schedule(
    time: str = "08:00",
    fetch: bool = True,
    digest: bool = False,
    ai: bool = False,
) -> Path:
    spec = ScheduleSpec(time=time, fetch=fetch, digest=digest, ai=ai)
    script_path = write_runner_script(spec)
    task_file = write_platform_task_file(spec, script_path)
    path = schedule_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        tomli_w.dumps(
            {
                "schedule": {
                    "type": "daily",
                    "time": spec.time,
                    "fetch": spec.fetch,
                    "digest": spec.digest,
                    "ai": spec.ai,
                    "platform": current_platform(),
                    "runner": str(script_path),
                    "task_file": str(task_file) if task_file else "",
                    "installed": False,
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def read_schedule() -> str | None:
    path = schedule_path()
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def remove_schedule() -> bool:
    path = schedule_path()
    if not path.exists():
        return False
    path.unlink()
    return True


def current_platform() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    if system == "linux":
        return "linux"
    return system


def write_runner_script(spec: ScheduleSpec) -> Path:
    directory = scripts_dir()
    directory.mkdir(parents=True, exist_ok=True)
    if current_platform() == "windows":
        path = directory / "feedcopilot-daily.cmd"
        path.write_text(_windows_runner(spec), encoding="utf-8")
    else:
        path = directory / "feedcopilot-daily.sh"
        path.write_text(_posix_runner(spec), encoding="utf-8")
        path.chmod(0o755)
    return path


def write_platform_task_file(spec: ScheduleSpec, runner_path: Path) -> Path | None:
    platform_name = current_platform()
    if platform_name == "macos":
        path = scripts_dir() / f"{LAUNCHD_LABEL}.plist"
        path.write_text(_launchd_plist(spec, runner_path), encoding="utf-8")
        return path
    if platform_name == "linux":
        path = scripts_dir() / "feedcopilot.cron"
        path.write_text(_cron_block(spec, runner_path), encoding="utf-8")
        return path
    return None


def install_schedule() -> str:
    platform_name = current_platform()
    if platform_name == "macos":
        result = _install_launchd()
    elif platform_name == "linux":
        result = _install_cron()
    elif platform_name == "windows":
        result = _install_windows_task()
    else:
        raise RuntimeError(f"Unsupported scheduler platform: {platform_name}")
    _set_installed(True)
    return result


def uninstall_schedule() -> str:
    platform_name = current_platform()
    if platform_name == "macos":
        result = _uninstall_launchd()
    elif platform_name == "linux":
        result = _uninstall_cron()
    elif platform_name == "windows":
        result = _uninstall_windows_task()
    else:
        raise RuntimeError(f"Unsupported scheduler platform: {platform_name}")
    _set_installed(False)
    return result


def _windows_runner(spec: ScheduleSpec) -> str:
    commands = _feedcopilot_commands(spec)
    lines = ["@echo off"]
    lines.extend(f'"{sys.executable}" -m feedcopilot.cli.app {command}' for command in commands)
    lines.append("")
    return "\n".join(lines)


def _posix_runner(spec: ScheduleSpec) -> str:
    commands = _feedcopilot_commands(spec)
    lines = ["#!/bin/sh", "set -eu"]
    lines.extend(f'"{sys.executable}" -m feedcopilot.cli.app {command}' for command in commands)
    lines.append("")
    return "\n".join(lines)


def _feedcopilot_commands(spec: ScheduleSpec) -> list[str]:
    commands: list[str] = []
    if spec.fetch:
        commands.append("fetch")
    if spec.digest:
        digest_path = get_data_dir() / "summaries" / "daily.md"
        commands.append(f'digest --since 24h --output "{digest_path}"')
    if spec.ai:
        commands.append("ai run --since 24h")
    return commands or ["fetch"]


def _launchd_plist(spec: ScheduleSpec, runner_path: Path) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" \
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{LAUNCHD_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{runner_path}</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>{spec.hour}</integer>
    <key>Minute</key>
    <integer>{spec.minute}</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>{scripts_dir() / "feedcopilot.out.log"}</string>
  <key>StandardErrorPath</key>
  <string>{scripts_dir() / "feedcopilot.err.log"}</string>
</dict>
</plist>
"""


def _cron_block(spec: ScheduleSpec, runner_path: Path) -> str:
    return (
        f"{CRON_BEGIN}\n"
        f"{spec.minute} {spec.hour} * * * /bin/sh \"{runner_path}\"\n"
        f"{CRON_END}\n"
    )


def _install_launchd() -> str:
    task_file = scripts_dir() / f"{LAUNCHD_LABEL}.plist"
    if not task_file.exists():
        raise RuntimeError("launchd plist not found. Run schedule daily first.")
    launch_agents = Path.home() / "Library" / "LaunchAgents"
    launch_agents.mkdir(parents=True, exist_ok=True)
    target = launch_agents / task_file.name
    target.write_text(task_file.read_text(encoding="utf-8"), encoding="utf-8")
    subprocess.run(["launchctl", "unload", str(target)], check=False, capture_output=True)
    completed = subprocess.run(
        ["launchctl", "load", str(target)],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "launchctl load failed.")
    return f"Installed launchd job: {target}"


def _uninstall_launchd() -> str:
    target = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
    subprocess.run(["launchctl", "unload", str(target)], check=False, capture_output=True)
    if target.exists():
        target.unlink()
    return f"Removed launchd job: {target}"


def _install_cron() -> str:
    task_file = scripts_dir() / "feedcopilot.cron"
    if not task_file.exists():
        raise RuntimeError("cron file not found. Run schedule daily first.")
    existing = subprocess.run(["crontab", "-l"], text=True, capture_output=True, check=False)
    current = existing.stdout if existing.returncode == 0 else ""
    cleaned = _remove_cron_block(current)
    new_crontab = cleaned.rstrip() + "\n\n" + task_file.read_text(encoding="utf-8")
    completed = subprocess.run(
        ["crontab", "-"],
        input=new_crontab,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "crontab install failed.")
    return "Installed cron job."


def _uninstall_cron() -> str:
    existing = subprocess.run(["crontab", "-l"], text=True, capture_output=True, check=False)
    if existing.returncode != 0:
        return "No crontab found."
    cleaned = _remove_cron_block(existing.stdout).strip() + "\n"
    completed = subprocess.run(
        ["crontab", "-"],
        input=cleaned,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "crontab removal failed.")
    return "Removed cron job."


def _install_windows_task() -> str:
    runner = scripts_dir() / "feedcopilot-daily.cmd"
    if not runner.exists():
        raise RuntimeError("Windows runner not found. Run schedule daily first.")
    spec = _read_schedule_spec()
    completed = subprocess.run(
        [
            "schtasks",
            "/Create",
            "/TN",
            TASK_NAME,
            "/SC",
            "DAILY",
            "/ST",
            spec.time,
            "/TR",
            f'"{runner}"',
            "/F",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return f"Installed Windows Task Scheduler task: {TASK_NAME}"


def _uninstall_windows_task() -> str:
    completed = subprocess.run(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
        text=True,
        capture_output=True,
        check=False,
    )
    output = f"{completed.stdout}\n{completed.stderr}".lower()
    if completed.returncode != 0 and "cannot find" not in output:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return f"Removed Windows Task Scheduler task: {TASK_NAME}"


def _remove_cron_block(content: str) -> str:
    lines = content.splitlines()
    result: list[str] = []
    skipping = False
    for line in lines:
        if line.strip() == CRON_BEGIN:
            skipping = True
            continue
        if line.strip() == CRON_END:
            skipping = False
            continue
        if not skipping:
            result.append(line)
    return "\n".join(result)


def _read_schedule_spec() -> ScheduleSpec:
    import tomllib

    path = schedule_path()
    if not path.exists():
        raise RuntimeError("No schedule configured.")
    data = tomllib.loads(path.read_text(encoding="utf-8"))["schedule"]
    return ScheduleSpec(
        time=data.get("time", "08:00"),
        fetch=data.get("fetch", True),
        digest=data.get("digest", False),
        ai=data.get("ai", False),
    )


def _set_installed(installed: bool) -> None:
    import tomllib

    path = schedule_path()
    if not path.exists():
        return
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    data.setdefault("schedule", {})["installed"] = installed
    path.write_text(tomli_w.dumps(data), encoding="utf-8")
