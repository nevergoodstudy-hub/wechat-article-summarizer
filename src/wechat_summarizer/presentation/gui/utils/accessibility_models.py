"""Models and style constants for GUI accessibility helpers."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from enum import Enum
from typing import TypedDict


class FocusDirection(Enum):
    """焦点移动方向"""

    NEXT = "next"
    PREVIOUS = "previous"
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class FocusableElement:
    """可聚焦元素"""

    widget: tk.Misc
    tab_index: int = 0
    group: str = "default"
    label: str = ""
    skip: bool = False


class FocusRingStyleDict(TypedDict):
    """焦点轮廓样式字典"""

    color: str
    width: int
    offset: int
    style: str


class FocusRingStyle:
    """焦点轮廓样式"""

    DEFAULT: FocusRingStyleDict = {
        "color": "#3b82f6",
        "width": 2,
        "offset": 2,
        "style": "solid",
    }

    HIGH_CONTRAST: FocusRingStyleDict = {
        "color": "#ffffff",
        "width": 3,
        "offset": 2,
        "style": "solid",
    }

    DASHED: FocusRingStyleDict = {
        "color": "#3b82f6",
        "width": 2,
        "offset": 2,
        "style": "dashed",
    }


__all__ = [
    "FocusDirection",
    "FocusRingStyle",
    "FocusRingStyleDict",
    "FocusableElement",
]
