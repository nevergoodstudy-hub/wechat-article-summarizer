"""Core context menu window behavior."""

from __future__ import annotations

import contextlib
import logging
import tkinter as tk
from typing import Any

from .contextmenu_models import (
    DEFAULT_CONTEXT_MENU_COLORS,
    MAX_CONTEXT_MENU_ITEMS,
    MAX_CONTEXT_MENU_LABEL_LENGTH,
    MenuItem,
)
from .contextmenu_render import ContextMenuRenderMixin

logger = logging.getLogger(__name__)


class ContextMenu(ContextMenuRenderMixin):
    """上下文菜单"""

    MAX_ITEMS = MAX_CONTEXT_MENU_ITEMS
    MAX_LABEL_LENGTH = MAX_CONTEXT_MENU_LABEL_LENGTH

    def __init__(
        self, parent: tk.Widget, items: list[MenuItem], min_width: int = 180, **kwargs: Any
    ):
        self.parent = parent
        self.items = items[: self.MAX_ITEMS]
        self.min_width = min_width

        self._window: tk.Toplevel | None = None
        self._item_frames: list[dict[str, Any]] = []
        self._selected_index = -1
        self._is_open = False
        self._submenu: ContextMenu | None = None

        self.colors = dict(DEFAULT_CONTEXT_MENU_COLORS)

    def show(self, x: int, y: int) -> None:
        """在指定位置显示菜单"""
        if self._is_open:
            self.close()

        self._is_open = True

        self._window = tk.Toplevel(self.parent)
        self._window.wm_overrideredirect(True)
        self._window.configure(bg=self.colors["border"])

        container = tk.Frame(self._window, bg=self.colors["bg"], padx=1, pady=1)
        container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self._render_items(container)

        self._window.update_idletasks()
        x, y = self._adjust_position(x, y)
        self._window.geometry(f"+{x}+{y}")

        self._window.bind("<Escape>", lambda _event: self.close())
        self._window.bind("<Up>", self._on_key_up)
        self._window.bind("<Down>", self._on_key_down)
        self._window.bind("<Return>", self._on_key_enter)
        self._window.bind("<FocusOut>", self._on_focus_out)

        self.parent.bind("<Button-1>", self._on_global_click, add="+")
        self._window.focus_set()

    def _execute_item(self, item: MenuItem) -> None:
        """执行菜单项"""
        self.close()

        if item.on_click:
            try:
                item.on_click()
            except Exception as e:
                logger.error(f"菜单项执行失败: {e}")

    def _show_submenu(self, parent_frame: tk.Frame, item: MenuItem) -> None:
        """显示子菜单"""
        if self._submenu:
            self._submenu.close()

        if not item.children:
            return

        frame_x = parent_frame.winfo_rootx() + parent_frame.winfo_width()
        frame_y = parent_frame.winfo_rooty()

        self._submenu = ContextMenu(self.parent, item.children, min_width=self.min_width)
        self._submenu.colors = self.colors
        self._submenu.show(frame_x, frame_y)

    def _adjust_position(self, x: int, y: int) -> tuple[int, int]:
        """调整位置避免超出屏幕"""
        window = self._window
        if window is None:
            return x, y

        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        menu_width = window.winfo_reqwidth()
        menu_height = window.winfo_reqheight()

        if x + menu_width > screen_width:
            x = screen_width - menu_width - 10

        if y + menu_height > screen_height:
            y = screen_height - menu_height - 10

        return max(0, x), max(0, y)

    def _on_key_up(self, event: tk.Event) -> None:
        """向上导航"""
        if not self._item_frames:
            return

        new_idx = self._selected_index - 1
        while new_idx >= 0:
            for item_data in self._item_frames:
                if item_data["index"] == new_idx and not item_data["item"].disabled:
                    self._highlight_item(new_idx)
                    return
            new_idx -= 1

    def _on_key_down(self, event: tk.Event) -> None:
        """向下导航"""
        if not self._item_frames:
            return

        new_idx = self._selected_index + 1
        max_idx = max(d["index"] for d in self._item_frames)

        while new_idx <= max_idx:
            for item_data in self._item_frames:
                if item_data["index"] == new_idx and not item_data["item"].disabled:
                    self._highlight_item(new_idx)
                    return
            new_idx += 1

    def _on_key_enter(self, event: tk.Event) -> None:
        """回车确认"""
        if self._selected_index < 0:
            return

        for item_data in self._item_frames:
            if item_data["index"] == self._selected_index:
                item = item_data["item"]
                if item.children:
                    self._show_submenu(item_data["frame"], item)
                else:
                    self._execute_item(item)
                break

    def _on_focus_out(self, event: tk.Event) -> None:
        """失去焦点"""
        self.parent.after(100, self._check_close)

    def _check_close(self) -> None:
        """检查是否需要关闭"""
        if self._window and self._window.winfo_exists():
            try:
                focus = self._window.focus_get()
                if (focus is None or focus.winfo_toplevel() != self._window) and not (
                    self._submenu and self._submenu._is_open
                ):
                    self.close()
            except tk.TclError:
                self.close()

    def _on_global_click(self, event: tk.Event) -> None:
        """全局点击"""
        if self._window and self._window.winfo_exists():
            try:
                click_x = event.x_root
                click_y = event.y_root

                menu_x = self._window.winfo_x()
                menu_y = self._window.winfo_y()
                menu_w = self._window.winfo_width()
                menu_h = self._window.winfo_height()

                if not (
                    menu_x <= click_x <= menu_x + menu_w and menu_y <= click_y <= menu_y + menu_h
                ):
                    self.close()
            except tk.TclError:
                self.close()

    def close(self) -> None:
        """关闭菜单"""
        if self._submenu:
            self._submenu.close()
            self._submenu = None

        if self._window:
            with contextlib.suppress(tk.TclError):
                self._window.destroy()
            self._window = None

        self._is_open = False
        self._selected_index = -1
        self._item_frames.clear()

        with contextlib.suppress(tk.TclError):
            self.parent.unbind("<Button-1>")

    def is_open(self) -> bool:
        """是否打开状态"""
        return self._is_open


__all__ = ["ContextMenu"]
