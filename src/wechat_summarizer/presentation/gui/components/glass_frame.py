"""Liquid glass frame component."""

from __future__ import annotations

from .glass_animation import GlassAnimationMixin
from .glass_compat import CTK_AVAILABLE, ctk, tk
from .glass_models import (
    MAX_GLASS_BLUR,
    MAX_GLASS_OPACITY,
    MIN_GLASS_BLUR,
    MIN_GLASS_OPACITY,
    clamp_blur_radius,
    clamp_opacity,
    resolve_glass_theme,
)


class LiquidGlassFrame(  # type: ignore[misc]
    GlassAnimationMixin,
    ctk.CTkFrame if CTK_AVAILABLE else tk.Frame,  # type: ignore[misc, valid-type]
):
    """Liquid glass visual frame component."""

    MIN_OPACITY = MIN_GLASS_OPACITY
    MAX_OPACITY = MAX_GLASS_OPACITY
    MIN_BLUR = MIN_GLASS_BLUR
    MAX_BLUR = MAX_GLASS_BLUR

    def __init__(
        self,
        master,
        width: int = 200,
        height: int = 200,
        opacity: float = 0.85,
        blur_radius: int = 15,
        border_glow: bool = True,
        theme: str = "dark",
        corner_radius: int = 16,
        animated: bool = False,
        **kwargs,
    ) -> None:
        self._opacity = clamp_opacity(opacity)
        self._blur_radius = clamp_blur_radius(blur_radius)
        self._border_glow = border_glow
        self._theme = theme
        self._animated = animated
        self._animation_id: int | None = None
        self._animation_frame = 0

        colors = resolve_glass_theme(theme)
        self._base_color = colors.base

        if CTK_AVAILABLE:
            super().__init__(
                master,
                width=width,
                height=height,
                corner_radius=corner_radius,
                fg_color=self._apply_opacity(self._base_color, self._opacity),
                border_width=1,
                border_color=colors.border,
                **kwargs,
            )
        else:
            super().__init__(
                master,
                width=width,
                height=height,
                bg=self._base_color,
                highlightthickness=1,
                highlightbackground=colors.border,
                **kwargs,
            )

        if self._animated:
            self._start_breathing_animation()


__all__ = ["LiquidGlassFrame"]
