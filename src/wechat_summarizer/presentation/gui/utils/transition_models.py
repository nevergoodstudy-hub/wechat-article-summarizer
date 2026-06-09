"""Models for page transitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TransitionType(Enum):
    """过渡类型"""

    FADE = "fade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    SCALE = "scale"
    SCALE_FADE = "scale_fade"
    NONE = "none"


class EasingFunction(Enum):
    """缓动函数类型"""

    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    EASE_OUT_CUBIC = "ease_out_cubic"
    EASE_OUT_EXPO = "ease_out_expo"
    SPRING = "spring"


@dataclass
class TransitionConfig:
    """过渡配置"""

    type: TransitionType = TransitionType.FADE
    duration: int = 300
    easing: EasingFunction = EasingFunction.EASE_OUT_CUBIC
    delay: int = 0


__all__ = ["EasingFunction", "TransitionConfig", "TransitionType"]
