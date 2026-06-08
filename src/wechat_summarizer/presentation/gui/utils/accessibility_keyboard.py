"""Keyboard navigation mixins for GUI accessibility helpers."""

from __future__ import annotations

import tkinter as tk
from typing import Any, cast


class KeyboardNavigable:
    """键盘导航混入类"""

    def enable_arrow_navigation(self, widgets: list[tk.Misc], wrap: bool = True) -> None:
        """启用方向键导航"""
        for index, widget in enumerate(widgets):
            widget_any = cast(Any, widget)
            widget_any._nav_index = index
            widget_any._nav_widgets = widgets
            widget_any._nav_wrap = wrap
            widget.bind("<Up>", self._on_arrow_up)
            widget.bind("<Down>", self._on_arrow_down)
            widget.bind("<Left>", self._on_arrow_left)
            widget.bind("<Right>", self._on_arrow_right)

    def _on_arrow_up(self, event: Any) -> str:
        self._navigate_arrow(event.widget, -1)
        return "break"

    def _on_arrow_down(self, event: Any) -> str:
        self._navigate_arrow(event.widget, 1)
        return "break"

    def _on_arrow_left(self, event: Any) -> str:
        self._navigate_arrow(event.widget, -1)
        return "break"

    def _on_arrow_right(self, event: Any) -> str:
        self._navigate_arrow(event.widget, 1)
        return "break"

    def _navigate_arrow(self, widget: tk.Misc, direction: int) -> None:
        """方向键导航"""
        if not hasattr(widget, "_nav_widgets"):
            return

        widgets = cast(list[tk.Misc] | None, getattr(widget, "_nav_widgets", None))
        if not widgets:
            return

        current_index = int(getattr(widget, "_nav_index", 0))
        wrap = bool(getattr(widget, "_nav_wrap", True))
        new_index = current_index + direction
        if wrap:
            new_index = new_index % len(widgets)
        else:
            new_index = max(0, min(new_index, len(widgets) - 1))

        if 0 <= new_index < len(widgets):
            widgets[new_index].focus_set()


__all__ = ["KeyboardNavigable"]
