"""Binding manager for context menus."""

from __future__ import annotations

import contextlib
import tkinter as tk
from typing import Literal

from .contextmenu_core import ContextMenu
from .contextmenu_models import MenuItem


class ContextMenuManager:
    """上下文菜单管理器"""

    _menus: dict[int, ContextMenu] = {}

    @classmethod
    def bind(
        cls, widget: tk.Widget, items: list[MenuItem], button: Literal[1, 2, 3] = 3
    ) -> ContextMenu:
        """为 widget 绑定上下文菜单。"""
        menu = ContextMenu(widget, items)

        def show_menu(event: tk.Event) -> None:
            menu.show(event.x_root, event.y_root)

        widget.bind(f"<Button-{button}>", show_menu)

        cls._menus[id(widget)] = menu
        return menu

    @classmethod
    def unbind(cls, widget: tk.Widget) -> None:
        """解绑上下文菜单"""
        widget_id = id(widget)
        if widget_id in cls._menus:
            cls._menus[widget_id].close()
            del cls._menus[widget_id]

        with contextlib.suppress(tk.TclError):
            widget.unbind("<Button-3>")

    @classmethod
    def close_all(cls) -> None:
        """关闭所有菜单"""
        for menu in cls._menus.values():
            menu.close()


__all__ = ["ContextMenuManager"]
