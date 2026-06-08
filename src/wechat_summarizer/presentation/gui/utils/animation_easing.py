"""Easing functions for GUI animation utilities."""

from __future__ import annotations

import math
from collections.abc import Callable

from .animation_models import EasingType


class Easing:
    """缓动函数库"""

    @staticmethod
    def linear(t: float) -> float:
        return t

    @staticmethod
    def ease_in_quad(t: float) -> float:
        return t * t

    @staticmethod
    def ease_out_quad(t: float) -> float:
        return 1 - (1 - t) * (1 - t)

    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2

    @staticmethod
    def ease_in_cubic(t: float) -> float:
        return t * t * t

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        return 1 - pow(1 - t, 3)

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

    @staticmethod
    def ease_in_expo(t: float) -> float:
        return 0 if t == 0 else pow(2, 10 * t - 10)

    @staticmethod
    def ease_out_expo(t: float) -> float:
        return 1 if t == 1 else 1 - pow(2, -10 * t)

    @staticmethod
    def ease_in_out_expo(t: float) -> float:
        if t == 0:
            return 0
        if t == 1:
            return 1
        if t < 0.5:
            return pow(2, 20 * t - 10) / 2
        return (2 - pow(2, -20 * t + 10)) / 2

    @staticmethod
    def ease_in_elastic(t: float) -> float:
        c4 = (2 * math.pi) / 3
        if t == 0:
            return 0
        if t == 1:
            return 1
        return -pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * c4)

    @staticmethod
    def ease_out_elastic(t: float) -> float:
        c4 = (2 * math.pi) / 3
        if t == 0:
            return 0
        if t == 1:
            return 1
        return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

    @staticmethod
    def ease_in_back(t: float) -> float:
        c1 = 1.70158
        c3 = c1 + 1
        return c3 * t * t * t - c1 * t * t

    @staticmethod
    def ease_out_back(t: float) -> float:
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

    @staticmethod
    def ease_out_bounce(t: float) -> float:
        n1, d1 = 7.5625, 2.75
        if t < 1 / d1:
            return n1 * t * t
        if t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        if t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        t -= 2.625 / d1
        return n1 * t * t + 0.984375

    @classmethod
    def get(cls, easing_type: EasingType) -> Callable[[float], float]:
        """获取缓动函数"""
        mapping = {
            EasingType.LINEAR: cls.linear,
            EasingType.EASE_IN_QUAD: cls.ease_in_quad,
            EasingType.EASE_OUT_QUAD: cls.ease_out_quad,
            EasingType.EASE_IN_OUT_QUAD: cls.ease_in_out_quad,
            EasingType.EASE_IN_CUBIC: cls.ease_in_cubic,
            EasingType.EASE_OUT_CUBIC: cls.ease_out_cubic,
            EasingType.EASE_IN_OUT_CUBIC: cls.ease_in_out_cubic,
            EasingType.EASE_IN_EXPO: cls.ease_in_expo,
            EasingType.EASE_OUT_EXPO: cls.ease_out_expo,
            EasingType.EASE_IN_OUT_EXPO: cls.ease_in_out_expo,
            EasingType.EASE_IN_ELASTIC: cls.ease_in_elastic,
            EasingType.EASE_OUT_ELASTIC: cls.ease_out_elastic,
            EasingType.EASE_IN_BACK: cls.ease_in_back,
            EasingType.EASE_OUT_BACK: cls.ease_out_back,
            EasingType.EASE_OUT_BOUNCE: cls.ease_out_bounce,
        }
        return mapping.get(easing_type, cls.ease_out_cubic)

    @staticmethod
    def cubic_bezier(p1x: float, p1y: float, p2x: float, p2y: float) -> Callable[[float], float]:
        """自定义三次贝塞尔曲线"""

        def bezier(t: float) -> float:
            cx = 3 * p1x
            bx = 3 * (p2x - p1x) - cx
            ax = 1 - cx - bx
            cy = 3 * p1y
            by = 3 * (p2y - p1y) - cy
            ay = 1 - cy - by

            def sample_curve_x(time_value: float) -> float:
                return ((ax * time_value + bx) * time_value + cx) * time_value

            def sample_curve_y(time_value: float) -> float:
                return ((ay * time_value + by) * time_value + cy) * time_value

            x = t
            for _ in range(8):
                z = sample_curve_x(x) - t
                if abs(z) < 1e-6:
                    break
                d = (3 * ax * x + 2 * bx) * x + cx
                if abs(d) < 1e-6:
                    break
                x = x - z / d

            return float(sample_curve_y(x))

        return bezier


__all__ = ["Easing"]
