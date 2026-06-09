"""Theme and accessibility data models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AppearanceMode(Enum):
    """外观模式"""

    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class ContrastMode(Enum):
    """对比度模式"""

    NORMAL = "normal"
    HIGH = "high"
    HIGHER = "higher"


@dataclass
class AccessibilitySettings:
    """可访问性设置"""

    font_scale: float = 1.0
    contrast_mode: str = "normal"
    reduce_motion: bool = False
    reduce_transparency: bool = False

    MIN_FONT_SCALE = 0.8
    MAX_FONT_SCALE = 2.0

    def __post_init__(self) -> None:
        self.font_scale = max(self.MIN_FONT_SCALE, min(self.MAX_FONT_SCALE, self.font_scale))


ThemePalette = dict[str, str]
ThemeMap = dict[str, ThemePalette]


__all__ = [
    "AccessibilitySettings",
    "AppearanceMode",
    "ContrastMode",
    "ThemeMap",
    "ThemePalette",
]
