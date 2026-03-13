from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from . import APP_VERSION


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_update_status() -> dict:
    payload = {
        "currentVersion": APP_VERSION,
        "updateAvailable": False,
        "currentCommit": None,
        "remoteCommit": None,
        "branch": "main",
        "remoteName": "origin",
        "updateCommand": platform_update_command(),
        "checked": False,
        "note": "",
    }

    if shutil.which("git") is None:
        payload["note"] = "git not found"
        return payload

    if not (PROJECT_ROOT / ".git").exists():
        payload["note"] = "repository metadata not found"
        return payload

    branch = git_output(["rev-parse", "--abbrev-ref", "HEAD"])
    if branch:
        payload["branch"] = branch

    current_commit = git_output(["rev-parse", "HEAD"])
    if current_commit:
        payload["currentCommit"] = current_commit

    remote_name = first_remote_name()
    if not remote_name:
        payload["note"] = "git remote not configured"
        return payload
    payload["remoteName"] = remote_name

    remote_commit = git_output(["ls-remote", remote_name, f"refs/heads/{payload['branch']}"], allow_failure=True)
    if not remote_commit:
        payload["note"] = "unable to reach remote release source"
        return payload

    payload["checked"] = True
    payload["remoteCommit"] = remote_commit.split()[0]
    payload["updateAvailable"] = bool(
        payload["currentCommit"]
        and payload["remoteCommit"]
        and payload["currentCommit"] != payload["remoteCommit"]
    )
    payload["note"] = (
        "update available" if payload["updateAvailable"] else "already up to date"
    )
    return payload


def first_remote_name() -> str | None:
    output = git_output(["remote"])
    if not output:
        return None
    names = [item.strip() for item in output.splitlines() if item.strip()]
    return names[0] if names else None


def git_output(args: list[str], allow_failure: bool = False) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=8,
            check=not allow_failure,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if completed.returncode != 0:
        return None

    stdout = completed.stdout.strip()
    return stdout or None


def platform_update_command() -> str:
    if sys.platform.startswith("win"):
        return ".\\scripts\\update-windows.ps1"
    if sys.platform == "darwin":
        return "bash ./scripts/update-macos.sh"
    return "bash ./scripts/update-ubuntu.sh"
