"""Compatibility entrypoint for GUI animation utilities."""

from __future__ import annotations

from .animation_easing import Easing
from .animation_engine import AnimationEngine
from .animation_facade import animate
from .animation_models import EasingType, Tween

__all__ = [
    "AnimationEngine",
    "Easing",
    "EasingType",
    "Tween",
    "animate",
]


if __name__ == "__main__":
    from .animation_demo import run_animation_demo

    run_animation_demo()
