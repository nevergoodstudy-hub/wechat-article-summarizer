"""Small Windows platform helpers for GUI integration."""

from __future__ import annotations

import platform
import sys
from pathlib import Path


def is_windows() -> bool:
    """Return whether the current runtime is Windows."""
    return sys.platform == "win32"


def get_windows_version() -> tuple[int, int, int] | None:
    """Return the Windows version tuple, or None outside Windows."""
    if not is_windows():
        return None

    try:
        parts = platform.version().split(".")
        return int(parts[0]), int(parts[1]), int(parts[2])
    except Exception:
        return None


def get_current_window_handle() -> int | None:
    """Resolve a console or foreground window handle for taskbar APIs."""
    if not is_windows():
        return None

    try:
        import ctypes

        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if not hwnd:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
        return int(hwnd) if hwnd else None
    except Exception:
        return None


def powershell_quote(value: str | Path) -> str:
    """Quote a value as a PowerShell single-quoted literal."""
    return "'" + str(value).replace("'", "''") + "'"


__all__ = [
    "get_current_window_handle",
    "get_windows_version",
    "is_windows",
    "powershell_quote",
]
