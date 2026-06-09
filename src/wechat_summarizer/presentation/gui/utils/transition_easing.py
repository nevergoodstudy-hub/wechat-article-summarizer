"""Easing functions for page transitions."""

from __future__ import annotations

from collections.abc import Callable

from .transition_models import EasingFunction


class Easing:
    """缓动函数库"""

    @staticmethod
    def linear(t: float) -> float:
        return t

    @staticmethod
    def ease_in(t: float) -> float:
        return t * t

    @staticmethod
    def ease_out(t: float) -> float:
        return 1 - (1 - t) * (1 - t)

    @staticmethod
    def ease_in_out(t: float) -> float:
        if t < 0.5:
            return 2 * t * t
        return 1 - pow(-2 * t + 2, 2) / 2

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        return 1 - pow(1 - t, 3)

    @staticmethod
    def ease_out_expo(t: float) -> float:
        return 1 if t == 1 else 1 - pow(2, -10 * t)

    @staticmethod
    def spring(t: float) -> float:
        """弹簧效果"""
        c4 = (2 * 3.14159) / 3
        if t == 0:
            return 0
        if t == 1:
            return 1
        return pow(2, -10 * t) * ((t * 10 - 0.75) * c4) + 1

    @classmethod
    def get(cls, easing_type: EasingFunction) -> Callable[[float], float]:
        """获取缓动函数"""
        mapping = {
            EasingFunction.LINEAR: cls.linear,
            EasingFunction.EASE_IN: cls.ease_in,
            EasingFunction.EASE_OUT: cls.ease_out,
            EasingFunction.EASE_IN_OUT: cls.ease_in_out,
            EasingFunction.EASE_OUT_CUBIC: cls.ease_out_cubic,
            EasingFunction.EASE_OUT_EXPO: cls.ease_out_expo,
            EasingFunction.SPRING: cls.spring,
        }
        return mapping.get(easing_type, cls.ease_out_cubic)


__all__ = ["Easing"]
