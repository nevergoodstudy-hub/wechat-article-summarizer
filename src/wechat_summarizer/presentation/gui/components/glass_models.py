"""Theme helpers and limits for glass components."""

from __future__ import annotations

from dataclasses import dataclass

from ..styles.colors import ModernColors

MIN_GLASS_OPACITY = 0.3
MAX_GLASS_OPACITY = 1.0
MIN_GLASS_BLUR = 0
MAX_GLASS_BLUR = 30


@dataclass(frozen=True)
class GlassThemeColors:
    """Resolved colors for a glass component theme."""

    base: str
    border: str
    accent: str
    accent_hover: str
    text: str


def clamp_opacity(opacity: float) -> float:
    """Clamp opacity to the supported range."""
    return max(MIN_GLASS_OPACITY, min(MAX_GLASS_OPACITY, opacity))


def clamp_blur_radius(blur_radius: int) -> int:
    """Clamp blur radius to the supported range."""
    return max(MIN_GLASS_BLUR, min(MAX_GLASS_BLUR, blur_radius))


def resolve_glass_theme(theme: str) -> GlassThemeColors:
    """Resolve material colors for a dark or light glass theme."""
    if theme == "dark":
        return GlassThemeColors(
            base="#1e1e1e",
            border=ModernColors.DARK_GLASS_BORDER_SOLID,
            accent=ModernColors.DARK_ACCENT,
            accent_hover=ModernColors.DARK_ACCENT_HOVER,
            text=ModernColors.DARK_TEXT,
        )

    return GlassThemeColors(
        base="#ffffff",
        border=ModernColors.LIGHT_GLASS_BORDER_SOLID,
        accent=ModernColors.LIGHT_ACCENT,
        accent_hover=ModernColors.LIGHT_ACCENT_HOVER,
        text=ModernColors.LIGHT_TEXT,
    )


__all__ = [
    "MAX_GLASS_BLUR",
    "MAX_GLASS_OPACITY",
    "MIN_GLASS_BLUR",
    "MIN_GLASS_OPACITY",
    "GlassThemeColors",
    "clamp_blur_radius",
    "clamp_opacity",
    "resolve_glass_theme",
]
