"""Validation state and color helpers for input components."""

from __future__ import annotations

from enum import Enum

from ..styles.colors import ModernColors


class ValidationState(Enum):
    """Input validation state."""

    DEFAULT = "default"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


def input_colors(theme: str, state: ValidationState) -> dict[str, str]:
    """Return entry colors for the current theme and validation state."""
    if theme == "dark":
        bg = ModernColors.DARK_CARD
        text = ModernColors.DARK_TEXT
        default_border = ModernColors.DARK_BORDER
    else:
        bg = ModernColors.LIGHT_CARD
        text = ModernColors.LIGHT_TEXT
        default_border = ModernColors.LIGHT_BORDER

    if state == ValidationState.SUCCESS:
        border = ModernColors.SUCCESS
    elif state == ValidationState.ERROR:
        border = ModernColors.ERROR
    elif state == ValidationState.WARNING:
        border = ModernColors.WARNING
    else:
        border = default_border

    return {"bg": bg, "text": text, "border": border}


def validation_color(theme: str, state: ValidationState) -> str:
    """Return validation message color for the current state."""
    if state == ValidationState.SUCCESS:
        return ModernColors.SUCCESS
    if state == ValidationState.ERROR:
        return ModernColors.ERROR
    if state == ValidationState.WARNING:
        return ModernColors.WARNING
    return secondary_text_color(theme)


def secondary_text_color(theme: str) -> str:
    """Return secondary text color for the current theme."""
    return (
        ModernColors.DARK_TEXT_SECONDARY if theme == "dark" else ModernColors.LIGHT_TEXT_SECONDARY
    )


def muted_text_color(theme: str) -> str:
    """Return muted text color for the current theme."""
    return ModernColors.DARK_TEXT_MUTED if theme == "dark" else ModernColors.LIGHT_TEXT_MUTED


def primary_text_color(theme: str) -> str:
    """Return primary text color for the current theme."""
    return ModernColors.DARK_TEXT if theme == "dark" else ModernColors.LIGHT_TEXT


def accent_color(theme: str) -> str:
    """Return accent color for the current theme."""
    return ModernColors.DARK_ACCENT if theme == "dark" else ModernColors.LIGHT_ACCENT
