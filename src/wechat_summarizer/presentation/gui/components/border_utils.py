"""Shared helpers for border components."""

from __future__ import annotations

import re
from enum import Enum

from ..styles.colors import to_tkinter_color


class GradientDirection(Enum):
    """Gradient direction."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    DIAGONAL = "diagonal"
    RADIAL = "radial"


class GlowIntensity(Enum):
    """Glow intensity."""

    NONE = 0
    SUBTLE = 1
    NORMAL = 2
    STRONG = 3
    INTENSE = 4


def validate_hex_color(color: str) -> bool:
    """Validate #RGB, #RRGGBB, and #RRGGBBAA colors."""
    if not isinstance(color, str):
        return False
    pattern = r"^#([A-Fa-f0-9]{3}|[A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})$"
    return bool(re.match(pattern, color))


def ensure_tkinter_color(color: str, bg_color: str = "#121212") -> str:
    """Return a Tk-compatible #RRGGBB color."""
    return to_tkinter_color(color, bg_color)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a hex color to RGB."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c * 2 for c in hex_color])
    elif len(hex_color) == 8:
        hex_color = hex_color[:6]
    if len(hex_color) < 6:
        return (0, 0, 0)
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """Convert RGB to a hex color."""
    return (
        f"#{max(0, min(255, rgb[0])):02x}"
        f"{max(0, min(255, rgb[1])):02x}"
        f"{max(0, min(255, rgb[2])):02x}"
    )


def interpolate_color(color1: str, color2: str, t: float) -> str:
    """Interpolate between two colors."""
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * t)
    g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * t)
    b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * t)
    return rgb_to_hex((r, g, b))


_validate_hex_color = validate_hex_color
_ensure_tkinter_color = ensure_tkinter_color
_hex_to_rgb = hex_to_rgb
_rgb_to_hex = rgb_to_hex
_interpolate_color = interpolate_color
