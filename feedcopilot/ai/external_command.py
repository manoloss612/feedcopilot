"""External AI command runner."""

import subprocess


def run_external_command(command: str, input_text: str) -> str:
    if not command.strip():
        raise ValueError("AI command is empty.")
    completed = subprocess.run(
        command,
        input=input_text,
        text=True,
        capture_output=True,
        shell=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "External AI command failed.")
    return completed.stdout
