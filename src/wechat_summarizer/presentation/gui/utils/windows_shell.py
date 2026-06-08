"""Windows shell helpers for opening files and creating shortcuts."""

from __future__ import annotations

import subprocess
from pathlib import Path

from loguru import logger

from .windows_platform import is_windows, powershell_quote


def open_folder(path: str | Path) -> bool:
    """Open a folder or reveal a file in Windows Explorer."""
    if not is_windows():
        return False

    try:
        resolved_path = Path(path)
        if resolved_path.is_file():
            subprocess.run(["explorer", "/select,", str(resolved_path)], check=True)
        elif resolved_path.is_dir():
            subprocess.run(["explorer", str(resolved_path)], check=True)
        else:
            return False
        return True
    except Exception as exc:
        logger.debug(f"Failed to open folder: {exc}")
        return False


def open_file(path: str | Path) -> bool:
    """Open a file with the configured Windows default application."""
    if not is_windows():
        return False

    try:
        import os

        os.startfile(str(path))
        return True
    except Exception as exc:
        logger.debug(f"Failed to open file: {exc}")
        return False


def create_shortcut(
    target: str | Path,
    shortcut_path: str | Path,
    description: str = "",
    icon: str | Path | None = None,
    working_dir: str | Path | None = None,
) -> bool:
    """Create a .lnk shortcut through COM, with a PowerShell fallback."""
    if not is_windows():
        return False

    try:
        import win32com.client

        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.Targetpath = str(target)
        shortcut.Description = description

        if icon:
            shortcut.IconLocation = str(icon)
        if working_dir:
            shortcut.WorkingDirectory = str(working_dir)

        shortcut.save()
        return True
    except ImportError:
        return _create_shortcut_with_powershell(
            target,
            shortcut_path,
            description,
            icon,
            working_dir,
        )
    except Exception as exc:
        logger.debug(f"Failed to create shortcut: {exc}")
        return False


def _create_shortcut_with_powershell(
    target: str | Path,
    shortcut_path: str | Path,
    description: str,
    icon: str | Path | None,
    working_dir: str | Path | None,
) -> bool:
    try:
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                build_shortcut_script(target, shortcut_path, description, icon, working_dir),
            ],
            capture_output=True,
            check=True,
        )
        return True
    except Exception as exc:
        logger.debug(f"Failed to create shortcut via PowerShell: {exc}")
        return False


def build_shortcut_script(
    target: str | Path,
    shortcut_path: str | Path,
    description: str = "",
    icon: str | Path | None = None,
    working_dir: str | Path | None = None,
) -> str:
    """Build a PowerShell script for shortcut creation."""
    lines = [
        "$WshShell = New-Object -ComObject WScript.Shell",
        f"$Shortcut = $WshShell.CreateShortcut({powershell_quote(shortcut_path)})",
        f"$Shortcut.TargetPath = {powershell_quote(target)}",
        f"$Shortcut.Description = {powershell_quote(description)}",
    ]
    if icon:
        lines.append(f"$Shortcut.IconLocation = {powershell_quote(icon)}")
    if working_dir:
        lines.append(f"$Shortcut.WorkingDirectory = {powershell_quote(working_dir)}")
    lines.append("$Shortcut.Save()")
    return "\n".join(lines)


__all__ = [
    "build_shortcut_script",
    "create_shortcut",
    "open_file",
    "open_folder",
]
