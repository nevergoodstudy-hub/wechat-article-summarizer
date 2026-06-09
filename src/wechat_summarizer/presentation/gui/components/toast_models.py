"""Models and color helpers for toast notifications."""

from __future__ import annotations

from enum import Enum

from ..styles.colors import ModernColors


class ToastType(Enum):
    """Toast notification type."""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


def toast_icon_for_type(toast_type: ToastType) -> str:
    """Return the compact icon text for a toast type."""
    icons = {
        ToastType.SUCCESS: "✓",
        ToastType.ERROR: "✕",
        ToastType.WARNING: "⚠",
        ToastType.INFO: "ℹ",
    }
    return icons[toast_type]


def toast_colors_for(theme: str, toast_type: ToastType) -> dict[str, str]:
    """Resolve colors for a toast type and theme."""
    type_colors = {
        ToastType.SUCCESS: {"icon": ModernColors.SUCCESS, "border": ModernColors.SUCCESS},
        ToastType.ERROR: {"icon": ModernColors.ERROR, "border": ModernColors.ERROR},
        ToastType.WARNING: {"icon": ModernColors.WARNING, "border": ModernColors.WARNING},
        ToastType.INFO: {"icon": ModernColors.INFO, "border": ModernColors.INFO},
    }
    if theme == "dark":
        base = {
            "bg": ModernColors.DARK_CARD,
            "text": ModernColors.DARK_TEXT,
            "hover": ModernColors.DARK_CARD_HOVER,
        }
    else:
        base = {
            "bg": ModernColors.LIGHT_CARD,
            "text": ModernColors.LIGHT_TEXT,
            "hover": ModernColors.LIGHT_CARD_HOVER,
        }
    return {**base, **type_colors[toast_type]}


__all__ = [
    "ToastType",
    "toast_colors_for",
    "toast_icon_for_type",
]
