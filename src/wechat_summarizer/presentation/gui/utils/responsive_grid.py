"""Responsive grid container."""

from __future__ import annotations

import tkinter as tk

from .responsive_breakpoints import BreakpointManager
from .responsive_models import Breakpoint


class ResponsiveGrid(tk.Frame):
    """响应式网格容器"""

    def __init__(
        self,
        parent: tk.Misc,
        breakpoint_manager: BreakpointManager,
        columns: dict[Breakpoint, int] | None = None,
        gap: int = 16,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self.bp_manager = breakpoint_manager
        self.gap = gap

        self.columns = columns or {
            Breakpoint.XS: 1,
            Breakpoint.SM: 2,
            Breakpoint.MD: 3,
            Breakpoint.LG: 4,
            Breakpoint.XL: 5,
        }

        self._items: list[tk.Widget] = []

        self.bp_manager.on_breakpoint_change(self._on_breakpoint_change)
        self.after(100, self._relayout)

    def _on_breakpoint_change(self, bp: Breakpoint, width: int, height: int) -> None:
        """断点变化时重新布局"""
        self._relayout()

    def _relayout(self) -> None:
        """重新计算布局"""
        if not self._items:
            return

        breakpoint = self.bp_manager.get_current_breakpoint()
        cols = self.columns.get(breakpoint, 3)

        container_width = self.winfo_width()
        if container_width <= 1:
            container_width = 800

        item_width = (container_width - (cols + 1) * self.gap) // cols

        for i, item in enumerate(self._items):
            row = i // cols
            col = i % cols

            x = self.gap + col * (item_width + self.gap)
            y = self.gap + row * (item_width + self.gap)

            item.place(x=x, y=y, width=item_width, height=item_width)

    def add_item(self, item: tk.Widget) -> None:
        """添加网格项"""
        self._items.append(item)
        self._relayout()

    def remove_item(self, item: tk.Widget) -> None:
        """移除网格项"""
        if item in self._items:
            self._items.remove(item)
            item.place_forget()
            self._relayout()

    def clear(self) -> None:
        """清空所有项"""
        for item in self._items:
            item.destroy()
        self._items.clear()

    def destroy(self) -> None:
        """清理资源"""
        self.bp_manager.off_breakpoint_change(self._on_breakpoint_change)
        self.clear()
        super().destroy()


__all__ = ["ResponsiveGrid"]
