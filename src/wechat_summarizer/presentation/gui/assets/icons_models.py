"""Icon model definitions."""

from __future__ import annotations

from enum import Enum


class IconSize(Enum):
    """图标尺寸标准"""

    TINY = 12
    SMALL = 16
    MEDIUM = 24
    LARGE = 32
    XLARGE = 48
    XXLARGE = 64


class IconStyle(Enum):
    """图标样式"""

    OUTLINED = "outlined"
    FILLED = "filled"
    ROUNDED = "rounded"
    SHARP = "sharp"


__all__ = [
    "IconSize",
    "IconStyle",
]
