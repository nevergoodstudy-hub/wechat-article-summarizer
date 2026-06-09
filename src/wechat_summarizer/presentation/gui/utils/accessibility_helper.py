"""General accessibility helpers for Tk widgets."""

from __future__ import annotations

import contextlib
import tkinter as tk
from collections.abc import Callable
from typing import Any, cast


class AccessibilityHelper:
    """可访问性辅助工具"""

    @staticmethod
    def make_focusable(widget: tk.Misc, tab_index: int = 0) -> None:
        """使组件可聚焦"""
        widget["takefocus"] = True

        def on_focus_in(event: Any) -> None:
            with contextlib.suppress(tk.TclError):
                widget["highlightthickness"] = 2
                widget["highlightcolor"] = "#3b82f6"

        def on_focus_out(event: Any) -> None:
            with contextlib.suppress(tk.TclError):
                widget["highlightthickness"] = 0

        widget.bind("<FocusIn>", on_focus_in, add="+")
        widget.bind("<FocusOut>", on_focus_out, add="+")

    @staticmethod
    def add_keyboard_activation(widget: tk.Misc, callback: Callable[[], None]) -> None:
        """添加键盘激活支持（Enter/Space）"""

        def on_key(event: Any) -> str:
            callback()
            return "break"

        widget.bind("<Return>", on_key)
        widget.bind("<space>", on_key)

    @staticmethod
    def set_accessible_name(widget: tk.Misc, name: str) -> None:
        """设置可访问名称（用于屏幕阅读器）"""
        widget_any = cast(Any, widget)
        widget_any._accessible_name = name

    @staticmethod
    def set_accessible_description(widget: tk.Misc, description: str) -> None:
        """设置可访问描述"""
        widget_any = cast(Any, widget)
        widget_any._accessible_description = description

    @staticmethod
    def create_focus_order(widgets: list[tk.Misc]) -> None:
        """创建焦点顺序"""
        for index, widget in enumerate(widgets):
            if index > 0:
                prev_widget = cast(Any, widgets[index - 1])
                prev_widget.tk_focusNext = lambda w=widget: w
            if index < len(widgets) - 1:
                next_widget = cast(Any, widgets[index + 1])
                next_widget.tk_focusPrev = lambda w=widget: w


__all__ = ["AccessibilityHelper"]
