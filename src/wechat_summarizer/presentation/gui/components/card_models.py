"""Card component models."""

from __future__ import annotations

from enum import Enum


class ShadowDepth(Enum):
    """阴影深度枚举"""

    NONE = 0
    SHALLOW = 1
    MEDIUM = 2
    DEEP = 3
    ELEVATED = 4


class CornerRadius(Enum):
    """圆角半径枚举"""

    SMALL = 8
    MEDIUM = 16
    LARGE = 24
    XLARGE = 32


class CardStyle(Enum):
    """卡片样式"""

    SOLID = "solid"
    OUTLINED = "outlined"
    ELEVATED = "elevated"
    GLASS = "glass"


__all__ = ["CardStyle", "CornerRadius", "ShadowDepth"]
