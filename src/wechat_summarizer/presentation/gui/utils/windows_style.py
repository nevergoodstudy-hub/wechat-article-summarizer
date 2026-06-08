"""Windows 11 native titlebar styling helpers."""

from __future__ import annotations

import sys
from typing import Any

from loguru import logger


class Windows11StyleHelper:
    """Apply Windows 11 native titlebar and border styling when available."""

    _pywinstyles: Any | None = None
    _checked: bool = False

    @classmethod
    def _ensure_pywinstyles(cls) -> None:
        """Import pywinstyles lazily."""
        if cls._checked:
            return

        cls._checked = True
        try:
            import pywinstyles

            cls._pywinstyles = pywinstyles
        except ImportError:
            cls._pywinstyles = None

    @classmethod
    def is_windows_11(cls) -> bool:
        """Return whether pywinstyles can style this Windows 11 session."""
        cls._ensure_pywinstyles()
        if cls._pywinstyles is None:
            return False

        try:
            version = sys.getwindowsversion()
            return version.major == 10 and version.build >= 22000
        except Exception:
            return False

    @classmethod
    def apply_window_style(cls, root, appearance_mode: str = "dark") -> None:
        """Apply the native titlebar colors for the current appearance mode."""
        if not cls.is_windows_11():
            logger.debug("当前系统不是 Windows 11, 跳过样式应用")
            return

        try:
            cls._change_window_colors(root, appearance_mode)
            logger.info("✨ 已应用 Windows 11 窗口样式")
        except Exception as exc:
            logger.debug(f"Windows 11 样式应用失败: {exc}")

    @classmethod
    def update_titlebar_color(cls, root, appearance_mode: str) -> None:
        """Update native titlebar colors after a theme change."""
        if not cls.is_windows_11():
            return

        try:
            cls._change_window_colors(root, appearance_mode)
            logger.debug(f"标题栏颜色已更新: {appearance_mode}")
        except Exception as exc:
            logger.debug(f"标题栏颜色更新失败: {exc}")

    @classmethod
    def _change_window_colors(cls, root, appearance_mode: str) -> None:
        from ..styles.colors import ModernColors

        pw = cls._pywinstyles
        if pw is None:
            return

        if appearance_mode == "dark":
            pw.change_header_color(root, ModernColors.DARK_BG)
            pw.change_border_color(root, ModernColors.DARK_BORDER)
        else:
            pw.change_header_color(root, ModernColors.LIGHT_BG)
            pw.change_border_color(root, ModernColors.LIGHT_BORDER)


__all__ = ["Windows11StyleHelper"]
