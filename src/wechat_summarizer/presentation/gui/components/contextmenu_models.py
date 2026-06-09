"""Models and constants for context menus."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

MAX_CONTEXT_MENU_ITEMS = 50
MAX_CONTEXT_MENU_LABEL_LENGTH = 100

DEFAULT_CONTEXT_MENU_COLORS = {
    "bg": "#252525",
    "item_bg": "#252525",
    "item_hover": "#3a3a3a",
    "item_active": "#3b82f6",
    "text": "#e5e5e5",
    "text_disabled": "#666666",
    "shortcut": "#808080",
    "separator": "#404040",
    "border": "#404040",
}


@dataclass
class MenuItem:
    """菜单项定义"""

    id: str
    label: str
    icon: str = ""
    shortcut: str = ""
    disabled: bool = False
    separator: bool = False
    children: list[MenuItem] = field(default_factory=list)
    on_click: Callable[[], None] | None = None


__all__ = [
    "DEFAULT_CONTEXT_MENU_COLORS",
    "MAX_CONTEXT_MENU_ITEMS",
    "MAX_CONTEXT_MENU_LABEL_LENGTH",
    "MenuItem",
]
