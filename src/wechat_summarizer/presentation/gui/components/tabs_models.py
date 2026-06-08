"""Models and theme helpers for tab components."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypedDict

from ..styles.colors import ModernColors


class TabPosition(Enum):
    """标签位置"""

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class TabItem:
    """标签项数据"""

    id: str
    label: str
    closable: bool = True
    icon: Any | None = None
    content: tk.Widget | None = None
    disabled: bool = False


class TabButtonWidgets(TypedDict):
    frame: tk.Frame
    label: Any
    close: Any | None


class DragData(TypedDict):
    tab_id: str | None
    start_x: int
    start_index: int


def tab_theme_colors(theme: str) -> dict[str, str]:
    """Return Tk-compatible tab colors for the requested theme."""
    if theme == "dark":
        return {
            "bg": ModernColors.DARK_BG,
            "tab_bar_bg": ModernColors.DARK_CARD,
            "tab_bg": ModernColors.DARK_CARD,
            "tab_active_bg": ModernColors.DARK_BG_SECONDARY,
            "tab_hover_bg": ModernColors.DARK_CARD_HOVER,
            "text": ModernColors.DARK_TEXT,
            "text_secondary": ModernColors.DARK_TEXT_SECONDARY,
            "text_disabled": ModernColors.DARK_TEXT_DISABLED,
            "indicator": ModernColors.DARK_ACCENT,
            "close_hover": ModernColors.ERROR,
            "border": ModernColors.DARK_BORDER,
        }
    return {
        "bg": ModernColors.LIGHT_BG,
        "tab_bar_bg": ModernColors.LIGHT_CARD,
        "tab_bg": ModernColors.LIGHT_CARD,
        "tab_active_bg": ModernColors.LIGHT_BG_SECONDARY,
        "tab_hover_bg": ModernColors.LIGHT_CARD_HOVER,
        "text": ModernColors.LIGHT_TEXT,
        "text_secondary": ModernColors.LIGHT_TEXT_SECONDARY,
        "text_disabled": ModernColors.LIGHT_TEXT_DISABLED,
        "indicator": ModernColors.LIGHT_ACCENT,
        "close_hover": ModernColors.ERROR,
        "border": ModernColors.LIGHT_BORDER,
    }


__all__ = [
    "DragData",
    "TabButtonWidgets",
    "TabItem",
    "TabPosition",
    "tab_theme_colors",
]
