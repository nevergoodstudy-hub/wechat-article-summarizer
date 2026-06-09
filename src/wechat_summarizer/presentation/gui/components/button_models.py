"""Button models, color themes, and sizing helpers."""

from __future__ import annotations

from enum import Enum
from typing import Any

from ..styles.colors import ModernColors
from ..styles.typography import TextStyles, get_text_style


class ButtonVariant(Enum):
    """按钮变体"""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    GHOST = "ghost"
    DANGER = "danger"
    TEXT = "text"


class ButtonSize(Enum):
    """按钮尺寸"""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


def get_button_colors(theme: str, variant: ButtonVariant) -> dict[str, str]:
    """Return a Tk-compatible color scheme for a button variant."""
    if theme == "dark":
        if variant == ButtonVariant.PRIMARY:
            return {
                "bg": ModernColors.DARK_ACCENT,
                "hover": ModernColors.DARK_ACCENT_HOVER,
                "text": "#FFFFFF",
            }
        if variant == ButtonVariant.SECONDARY:
            return {
                "bg": ModernColors.DARK_CARD,
                "hover": ModernColors.DARK_CARD_HOVER,
                "text": ModernColors.DARK_TEXT,
            }
        if variant == ButtonVariant.GHOST:
            return {
                "bg": "transparent",
                "hover": ModernColors.DARK_CARD_HOVER,
                "text": ModernColors.DARK_TEXT,
                "border": ModernColors.DARK_BORDER,
            }
        if variant == ButtonVariant.DANGER:
            return {
                "bg": ModernColors.ERROR,
                "hover": "#dc2626",
                "text": "#FFFFFF",
            }
        return {
            "bg": "transparent",
            "hover": ModernColors.DARK_CARD_HOVER,
            "text": ModernColors.DARK_TEXT,
        }

    if variant == ButtonVariant.PRIMARY:
        return {
            "bg": ModernColors.LIGHT_ACCENT,
            "hover": ModernColors.LIGHT_ACCENT_HOVER,
            "text": "#FFFFFF",
        }
    if variant == ButtonVariant.SECONDARY:
        return {
            "bg": ModernColors.LIGHT_CARD,
            "hover": ModernColors.LIGHT_CARD_HOVER,
            "text": ModernColors.LIGHT_TEXT,
        }
    if variant == ButtonVariant.GHOST:
        return {
            "bg": "transparent",
            "hover": ModernColors.LIGHT_CARD_HOVER,
            "text": ModernColors.LIGHT_TEXT,
            "border": ModernColors.LIGHT_BORDER,
        }
    if variant == ButtonVariant.DANGER:
        return {
            "bg": ModernColors.ERROR,
            "hover": "#dc2626",
            "text": "#FFFFFF",
        }
    return {
        "bg": "transparent",
        "hover": ModernColors.LIGHT_CARD_HOVER,
        "text": ModernColors.LIGHT_TEXT,
    }


def get_button_size_config(size: ButtonSize) -> dict[str, int]:
    """Return button height and padding for a size token."""
    if size == ButtonSize.SMALL:
        return {"height": 28, "padding_x": 12, "padding_y": 4}
    if size == ButtonSize.LARGE:
        return {"height": 44, "padding_x": 24, "padding_y": 12}
    return {"height": 36, "padding_x": 16, "padding_y": 8}


def get_button_font(size: ButtonSize) -> Any:
    """Return the configured typography token for a button size."""
    if size == ButtonSize.SMALL:
        return get_text_style(TextStyles.BUTTON_SMALL)
    if size == ButtonSize.LARGE:
        return get_text_style(TextStyles.BUTTON_LARGE)
    return get_text_style(TextStyles.BUTTON)


def get_icon_button_size(size: ButtonSize) -> int:
    """Return square icon button dimensions for a size token."""
    if size == ButtonSize.SMALL:
        return 32
    if size == ButtonSize.LARGE:
        return 48
    return 40


__all__ = [
    "ButtonSize",
    "ButtonVariant",
    "get_button_colors",
    "get_button_font",
    "get_button_size_config",
    "get_icon_button_size",
]
