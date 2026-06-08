"""Models and theme values for modern select widgets."""

from __future__ import annotations

from enum import Enum
from typing import Any

from ..styles.colors import ModernColors


class SelectMode(Enum):
    """选择模式"""

    SINGLE = "single"
    MULTIPLE = "multiple"


class SelectOption:
    """选项数据类"""

    def __init__(self, value: Any, label: str, disabled: bool = False):
        self.value = value
        self.label = label
        self.disabled = disabled


def select_theme_colors(theme: str) -> dict[str, str]:
    """Return theme colors used by ModernSelect."""
    if theme == "dark":
        return {
            "bg": ModernColors.DARK_CARD,
            "bg_hover": ModernColors.DARK_CARD_HOVER,
            "text": ModernColors.DARK_TEXT,
            "text_secondary": ModernColors.DARK_TEXT_SECONDARY,
            "border": ModernColors.DARK_BORDER,
            "accent": ModernColors.DARK_ACCENT,
            "dropdown_bg": ModernColors.DARK_SURFACE,
        }

    return {
        "bg": ModernColors.LIGHT_CARD,
        "bg_hover": ModernColors.LIGHT_CARD_HOVER,
        "text": ModernColors.LIGHT_TEXT,
        "text_secondary": ModernColors.LIGHT_TEXT_SECONDARY,
        "border": ModernColors.LIGHT_BORDER,
        "accent": ModernColors.LIGHT_ACCENT,
        "dropdown_bg": ModernColors.LIGHT_SURFACE,
    }


__all__ = ["SelectMode", "SelectOption", "select_theme_colors"]
