"""Compatibility facade for Windows GUI integration."""

from __future__ import annotations

from pathlib import Path

from .windows_notifications import show_notification as show_windows_notification
from .windows_paths import get_desktop_folder as get_windows_desktop_folder
from .windows_paths import get_documents_folder as get_windows_documents_folder
from .windows_platform import get_windows_version, is_windows
from .windows_shell import create_shortcut as create_windows_shortcut
from .windows_shell import open_file as open_windows_file
from .windows_shell import open_folder as open_windows_folder
from .windows_style import Windows11StyleHelper
from .windows_taskbar import WindowsTaskbarProgress


class WindowsIntegration:
    """Windows system integration facade.

    The public API remains compatible with the former monolithic module while
    platform-specific responsibilities live in smaller adapters.
    """

    _instance: WindowsIntegration | None = None
    _initialized: bool

    def __new__(cls) -> WindowsIntegration:
        """Return the singleton integration facade."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._is_windows = is_windows()
        self._hwnd = None
        self._taskbar_progress = WindowsTaskbarProgress()
        self._taskbar_list = None

    def set_taskbar_progress(self, progress: float, hwnd: int | None = None) -> None:
        """Set taskbar progress, or clear it when progress is negative."""
        self._taskbar_progress.set_progress(progress, hwnd)
        self._taskbar_list = self._taskbar_progress.taskbar_list

    def clear_taskbar_progress(self, hwnd: int | None = None) -> None:
        """Clear taskbar progress."""
        self.set_taskbar_progress(-1, hwnd)

    def show_notification(
        self,
        title: str,
        message: str,
        icon: str = "info",
        duration: int = 5000,
    ) -> None:
        """Show a system notification."""
        show_windows_notification(title, message, icon, duration)

    def open_folder(self, path: str | Path) -> bool:
        """Open a folder, or reveal a file in Explorer."""
        return open_windows_folder(path)

    def open_file(self, path: str | Path) -> bool:
        """Open a file with the default application."""
        return open_windows_file(path)

    def create_shortcut(
        self,
        target: str | Path,
        shortcut_path: str | Path,
        description: str = "",
        icon: str | Path | None = None,
        working_dir: str | Path | None = None,
    ) -> bool:
        """Create a Windows shortcut."""
        return create_windows_shortcut(
            target,
            shortcut_path,
            description,
            icon,
            working_dir,
        )

    def get_documents_folder(self) -> Path:
        """Return the user documents folder."""
        return get_windows_documents_folder()

    def get_desktop_folder(self) -> Path:
        """Return the user desktop folder."""
        return get_windows_desktop_folder()

    @staticmethod
    def is_windows() -> bool:
        """Return whether the current runtime is Windows."""
        return is_windows()

    @staticmethod
    def get_windows_version() -> tuple[int, int, int] | None:
        """Return the Windows version tuple, or None outside Windows."""
        return get_windows_version()


windows = WindowsIntegration()


__all__ = ["Windows11StyleHelper", "WindowsIntegration", "windows"]
