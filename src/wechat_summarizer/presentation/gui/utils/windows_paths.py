"""Windows known-folder helpers with portable fallbacks."""

from __future__ import annotations

from pathlib import Path

from .windows_platform import is_windows


def get_documents_folder() -> Path:
    """Return the user's documents folder."""
    return _get_shell_folder(0x0005, Path.home() / "Documents")


def get_desktop_folder() -> Path:
    """Return the user's desktop folder."""
    return _get_shell_folder(0x0010, Path.home() / "Desktop")


def _get_shell_folder(csidl: int, fallback: Path) -> Path:
    if is_windows():
        try:
            import ctypes
            from ctypes import wintypes

            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buf)
            if buf.value:
                return Path(buf.value)
        except Exception:
            pass

    return fallback


__all__ = ["get_desktop_folder", "get_documents_folder"]
