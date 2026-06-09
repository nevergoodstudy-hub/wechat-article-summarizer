"""Models and safety limits for virtual list components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MAX_ITEMS = 100000
MAX_ITEM_HEIGHT = 500
MIN_ITEM_HEIGHT = 20
RENDER_TIMEOUT_MS = 100
SCROLL_THROTTLE_MS = 16


@dataclass
class VirtualItem:
    """虚拟列表项"""

    index: int
    data: Any
    height: int = 40
    y_offset: int = 0


__all__ = [
    "MAX_ITEMS",
    "MAX_ITEM_HEIGHT",
    "MIN_ITEM_HEIGHT",
    "RENDER_TIMEOUT_MS",
    "SCROLL_THROTTLE_MS",
    "VirtualItem",
]
