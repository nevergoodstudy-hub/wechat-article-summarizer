"""Theme color helpers for progress components."""

from __future__ import annotations

from dataclasses import dataclass

from ..styles.colors import ModernColors


@dataclass(frozen=True)
class ProgressColors:
    """Resolved colors for progress widgets."""

    background: str
    foreground: str
    track: str
    inactive: str
    text: str
    text_inactive: str


def progress_colors_for_theme(theme: str) -> ProgressColors:
    """Resolve progress colors for the requested theme."""
    if theme == "dark":
        return ProgressColors(
            background=ModernColors.DARK_BG,
            foreground=ModernColors.DARK_ACCENT,
            track=ModernColors.DARK_CARD,
            inactive=ModernColors.DARK_BORDER,
            text=ModernColors.DARK_TEXT,
            text_inactive=ModernColors.DARK_TEXT_SECONDARY,
        )
    return ProgressColors(
        background=ModernColors.LIGHT_BG,
        foreground=ModernColors.LIGHT_ACCENT,
        track=ModernColors.LIGHT_CARD,
        inactive=ModernColors.LIGHT_BORDER,
        text=ModernColors.LIGHT_TEXT,
        text_inactive=ModernColors.LIGHT_TEXT_SECONDARY,
    )


__all__ = [
    "ProgressColors",
    "progress_colors_for_theme",
]
