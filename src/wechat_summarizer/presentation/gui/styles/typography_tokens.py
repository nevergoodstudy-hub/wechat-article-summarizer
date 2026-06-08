"""Typography scale and weight tokens."""

from __future__ import annotations

from enum import Enum


class FontWeight(Enum):
    """Font weight tokens."""

    THIN = 100
    EXTRA_LIGHT = 200
    LIGHT = 300
    REGULAR = 400
    MEDIUM = 500
    SEMI_BOLD = 600
    BOLD = 700
    EXTRA_BOLD = 800
    BLACK = 900


class FontSize(Enum):
    """Font size tokens."""

    XS = 10
    SM = 12
    BASE = 14
    MD = 16
    LG = 18
    XL = 20
    XXL = 24
    XXXL = 32
    HUGE = 48


class LineHeight(Enum):
    """Line-height tokens."""

    TIGHT = 1.2
    NORMAL = 1.5
    RELAXED = 1.8
    LOOSE = 2.0


class LetterSpacing(Enum):
    """Letter-spacing tokens."""

    TIGHTER = -0.05
    TIGHT = -0.025
    NORMAL = 0
    WIDE = 0.025
    WIDER = 0.05
    WIDEST = 0.1


TK_WEIGHT_MAP = {
    FontWeight.THIN: "normal",
    FontWeight.EXTRA_LIGHT: "normal",
    FontWeight.LIGHT: "normal",
    FontWeight.REGULAR: "normal",
    FontWeight.MEDIUM: "normal",
    FontWeight.SEMI_BOLD: "bold",
    FontWeight.BOLD: "bold",
    FontWeight.EXTRA_BOLD: "bold",
    FontWeight.BLACK: "bold",
}


__all__ = [
    "TK_WEIGHT_MAP",
    "FontSize",
    "FontWeight",
    "LetterSpacing",
    "LineHeight",
]
