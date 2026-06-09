"""Models for GUI animation utilities."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EasingType(Enum):
    """缓动类型"""

    LINEAR = "linear"
    EASE_IN_QUAD = "ease_in_quad"
    EASE_OUT_QUAD = "ease_out_quad"
    EASE_IN_OUT_QUAD = "ease_in_out_quad"
    EASE_IN_CUBIC = "ease_in_cubic"
    EASE_OUT_CUBIC = "ease_out_cubic"
    EASE_IN_OUT_CUBIC = "ease_in_out_cubic"
    EASE_IN_EXPO = "ease_in_expo"
    EASE_OUT_EXPO = "ease_out_expo"
    EASE_IN_OUT_EXPO = "ease_in_out_expo"
    EASE_IN_ELASTIC = "ease_in_elastic"
    EASE_OUT_ELASTIC = "ease_out_elastic"
    EASE_IN_BACK = "ease_in_back"
    EASE_OUT_BACK = "ease_out_back"
    EASE_OUT_BOUNCE = "ease_out_bounce"


@dataclass
class Tween:
    """补间动画"""

    target: Any
    property_name: str
    start_value: float
    end_value: float
    duration: int
    easing: EasingType = EasingType.EASE_OUT_CUBIC
    delay: int = 0
    on_update: Callable[[float], None] | None = None
    on_complete: Callable[[], None] | None = None
    _id: str = field(default_factory=lambda: f"tween_{time.time_ns()}")
    _start_time: float = 0
    _is_running: bool = False
    _is_complete: bool = False


__all__ = [
    "EasingType",
    "Tween",
]
