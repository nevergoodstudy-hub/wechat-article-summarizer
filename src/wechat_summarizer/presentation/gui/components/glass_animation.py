"""Animation mixin for liquid glass components."""

from __future__ import annotations

import math

from ..utils.gradient import GradientAnimator
from .glass_compat import CTK_AVAILABLE
from .glass_models import clamp_opacity


class GlassAnimationMixin:
    """Opacity animation behavior shared by glass frames."""

    _animated: bool
    _animation_frame: int
    _animation_id: int | None
    _base_color: str
    _blur_radius: int
    _opacity: float

    def _apply_opacity(self, color: str, opacity: float) -> str:
        """Apply opacity to a color while preserving current compatibility behavior."""
        _ = opacity
        return color

    def _start_breathing_animation(self) -> None:
        """Start a simple breathing opacity animation."""
        if not self._animated:
            return

        animator = GradientAnimator(fps=60)
        self._animation_id = animator.create_breathing_animation(
            base_color=self._base_color,
            intensity=0.1,
            duration=3.0,
        )
        self._animation_frame = 0
        self._update_breathing_opacity()

    def _update_breathing_opacity(self) -> None:
        if self._animation_id is None:
            return

        base_opacity = 0.85
        wave = math.sin(self._animation_frame * 0.05) * 0.1
        new_opacity = max(0.75, min(0.95, base_opacity + wave))

        if CTK_AVAILABLE and hasattr(self, "configure"):
            _ = self._apply_opacity(self._base_color, new_opacity)

        self._animation_frame += 1
        self.after(33, self._update_breathing_opacity)  # type: ignore[attr-defined]

    def stop_animation(self) -> None:
        """Stop the opacity animation."""
        self._animated = False
        self._animation_id = None

    def set_opacity(self, opacity: float) -> None:
        """Set the glass opacity."""
        self._opacity = clamp_opacity(opacity)

        if CTK_AVAILABLE and hasattr(self, "configure"):
            self.configure(fg_color=self._apply_opacity(self._base_color, self._opacity))

    def set_blur(self, blur_radius: int) -> None:
        """Set the blur radius value."""
        from .glass_models import clamp_blur_radius

        self._blur_radius = clamp_blur_radius(blur_radius)


__all__ = ["GlassAnimationMixin"]
