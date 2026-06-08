"""Facade helpers for GUI animation utilities."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .animation_engine import AnimationEngine
from .animation_models import EasingType


def animate(
    target: Any,
    property_name: str,
    end_value: float,
    duration: int = 300,
    easing: EasingType = EasingType.EASE_OUT_CUBIC,
    on_complete: Callable[[], None] | None = None,
) -> str:
    """快捷动画函数"""
    engine = AnimationEngine.get_instance()
    return engine.animate(
        target=target,
        property_name=property_name,
        end_value=end_value,
        duration=duration,
        easing=easing,
        on_complete=on_complete,
    )


__all__ = ["animate"]
