"""Gradient color animation state machine."""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from typing import Any, cast

from ..styles.colors import hex_to_rgb
from .gradient_manager import GradientManager
from .gradient_models import EasingFunction


class GradientAnimator:
    """Create and query gradient animation colors."""

    MAX_DURATION = 60.0
    MAX_FPS = 144
    MIN_FPS = 10

    def __init__(self, fps: int = 60) -> None:
        self._fps = max(self.MIN_FPS, min(self.MAX_FPS, fps))
        self._running = False
        self._current_animation_id = 0
        self._animations: dict[int, dict[str, Any]] = {}

    @property
    def fps(self) -> int:
        return self._fps

    @fps.setter
    def fps(self, value: int) -> None:
        self._fps = max(self.MIN_FPS, min(self.MAX_FPS, value))

    @staticmethod
    def apply_easing(t: float, easing: EasingFunction) -> float:
        """Apply easing to normalized progress."""
        progress = max(0.0, min(1.0, t))

        if easing == EasingFunction.LINEAR:
            return progress
        if easing == EasingFunction.EASE_IN:
            return progress * progress
        if easing == EasingFunction.EASE_OUT:
            return 1 - (1 - progress) * (1 - progress)
        if easing == EasingFunction.EASE_IN_OUT:
            if progress < 0.5:
                return 2 * progress * progress
            return 1 - pow(-2 * progress + 2, 2) / 2
        return progress

    def create_breathing_animation(
        self,
        base_color: str,
        intensity: float = 0.2,
        duration: float = 2.0,
        callback: Callable[[str], None] | None = None,
    ) -> int:
        """Create a breathing color animation."""
        safe_intensity = max(0.0, min(1.0, intensity))
        safe_duration = max(0.5, min(self.MAX_DURATION, duration))
        r, g, b = hex_to_rgb(base_color)

        def get_frame_color(progress: float) -> str:
            wave = math.sin(progress * 2 * math.pi)
            factor = 1.0 + wave * safe_intensity * 0.3
            return GradientManager.rgb_to_hex(
                max(0, min(255, int(r * factor))),
                max(0, min(255, int(g * factor))),
                max(0, min(255, int(b * factor))),
            )

        return self._register_animation(
            {
                "type": "breathing",
                "duration": safe_duration,
                "get_color": get_frame_color,
                "callback": callback,
                "start_time": None,
                "running": False,
            }
        )

    def create_color_flow_animation(
        self,
        colors: list[str],
        duration: float = 3.0,
        loop: bool = True,
        easing: EasingFunction = EasingFunction.EASE_IN_OUT,
        callback: Callable[[str], None] | None = None,
    ) -> int:
        """Create an animation flowing through a list of colors."""
        animation_colors = colors
        if len(animation_colors) < 2:
            animation_colors = (
                animation_colors + animation_colors
                if animation_colors
                else [
                    "#000000",
                    "#000000",
                ]
            )

        safe_duration = max(0.5, min(self.MAX_DURATION, duration))
        manager = GradientManager()

        def get_frame_color(progress: float) -> str:
            eased_progress = self.apply_easing(progress, easing)
            total_segments = len(animation_colors) - 1
            segment_progress = eased_progress * total_segments
            segment_index = min(int(segment_progress), total_segments - 1)
            local_progress = segment_progress - segment_index
            return manager.interpolate_color(
                animation_colors[segment_index],
                animation_colors[segment_index + 1],
                local_progress,
            )

        return self._register_animation(
            {
                "type": "color_flow",
                "duration": safe_duration,
                "loop": loop,
                "get_color": get_frame_color,
                "callback": callback,
                "start_time": None,
                "running": False,
            }
        )

    def get_current_color(self, anim_id: int) -> str | None:
        """Return the current color for an animation."""
        if anim_id not in self._animations:
            return None

        animation = self._animations[anim_id]
        if animation["start_time"] is None:
            animation["start_time"] = time.time()

        elapsed = time.time() - animation["start_time"]
        duration = float(animation["duration"])
        if animation.get("loop", True):
            progress = (elapsed % duration) / duration
        else:
            progress = min(1.0, elapsed / duration)

        color_getter = cast(Callable[[float], str], animation["get_color"])
        return color_getter(progress)

    def stop_animation(self, anim_id: int) -> None:
        """Stop and remove one animation."""
        if anim_id in self._animations:
            self._animations[anim_id]["running"] = False
            del self._animations[anim_id]

    def stop_all_animations(self) -> None:
        """Stop all animations."""
        self._animations.clear()

    def _register_animation(self, animation: dict[str, Any]) -> int:
        self._current_animation_id += 1
        anim_id = self._current_animation_id
        self._animations[anim_id] = animation
        return anim_id


__all__ = ["GradientAnimator"]
