"""Responsive style helpers."""

from __future__ import annotations

import contextlib
import tkinter as tk
from typing import Any

from .responsive_breakpoints import BreakpointManager
from .responsive_models import Breakpoint


class ResponsiveLayout:
    """响应式布局助手"""

    def __init__(self, breakpoint_manager: BreakpointManager):
        self.bp_manager = breakpoint_manager

    def apply_responsive_styles(
        self, widget: tk.Misc, styles: dict[Breakpoint, dict[str, Any]]
    ) -> None:
        """应用响应式样式"""

        def on_change(bp: Breakpoint, width: int, height: int) -> None:
            if bp in styles:
                for key, value in styles[bp].items():
                    with contextlib.suppress(tk.TclError):
                        widget.configure(**{key: value})

        self.bp_manager.on_breakpoint_change(on_change)

        current_bp = self.bp_manager.get_current_breakpoint()
        if current_bp in styles:
            for key, value in styles[current_bp].items():
                with contextlib.suppress(tk.TclError):
                    widget.configure(**{key: value})

    def responsive_padding(
        self, xs: int = 8, sm: int = 12, md: int = 16, lg: int = 20, xl: int = 24
    ) -> int:
        """获取响应式padding值"""
        breakpoint = self.bp_manager.get_current_breakpoint()
        mapping = {
            Breakpoint.XS: xs,
            Breakpoint.SM: sm,
            Breakpoint.MD: md,
            Breakpoint.LG: lg,
            Breakpoint.XL: xl,
        }
        return mapping.get(breakpoint, md)

    def responsive_font_size(
        self, xs: int = 12, sm: int = 13, md: int = 14, lg: int = 15, xl: int = 16
    ) -> int:
        """获取响应式字体大小"""
        breakpoint = self.bp_manager.get_current_breakpoint()
        mapping = {
            Breakpoint.XS: xs,
            Breakpoint.SM: sm,
            Breakpoint.MD: md,
            Breakpoint.LG: lg,
            Breakpoint.XL: xl,
        }
        return mapping.get(breakpoint, md)


__all__ = ["ResponsiveLayout"]
