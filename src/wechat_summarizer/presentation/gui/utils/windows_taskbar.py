"""Windows taskbar progress integration."""

from __future__ import annotations

from typing import Any

from loguru import logger

from .windows_platform import get_current_window_handle, is_windows


class WindowsTaskbarProgress:
    """Adapter for the Windows ITaskbarList3 progress API."""

    _CLSID_TASKBAR_LIST = "{56FDF344-FD6D-11d0-958A-006097C9A090}"

    def __init__(self) -> None:
        self.taskbar_list: Any | None = None

    def set_progress(self, progress: float, hwnd: int | None = None) -> None:
        """Set taskbar progress; pass a negative value to clear it."""
        if not is_windows():
            return

        try:
            resolved_hwnd = hwnd if hwnd is not None else get_current_window_handle()
            if not resolved_hwnd:
                return

            try:
                import comtypes.client as cc
            except ImportError:
                return

            if self.taskbar_list is None:
                self.taskbar_list = cc.CreateObject(
                    self._CLSID_TASKBAR_LIST,
                    interface=None,
                )

            if progress < 0:
                self.taskbar_list.SetProgressState(resolved_hwnd, 0)
                return

            self.taskbar_list.SetProgressState(resolved_hwnd, 2)
            self.taskbar_list.SetProgressValue(resolved_hwnd, int(progress * 100), 100)
        except Exception as exc:
            logger.debug(f"Failed to set taskbar progress: {exc}")

    def clear(self, hwnd: int | None = None) -> None:
        """Clear taskbar progress for the given window."""
        self.set_progress(-1, hwnd)


__all__ = ["WindowsTaskbarProgress"]
