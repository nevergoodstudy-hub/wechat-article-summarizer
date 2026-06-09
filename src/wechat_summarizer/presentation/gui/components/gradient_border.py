"""Gradient border component."""

from __future__ import annotations

import tkinter as tk
from typing import Any

try:
    import customtkinter as ctk

    _CTK_AVAILABLE = True
except ImportError:
    _CTK_AVAILABLE = False
    ctk = None

from ..styles.colors import ModernColors
from .border_utils import (
    GlowIntensity,
    GradientDirection,
    ensure_tkinter_color,
    validate_hex_color,
)
from .gradient_border_draw import GradientBorderDrawingMixin


class GradientBorder(GradientBorderDrawingMixin, tk.Canvas):
    """Gradient border canvas with optional glow and animation."""

    MAX_BORDER_WIDTH = 20
    MAX_GLOW_SPREAD = 30
    MAX_ANIMATION_DURATION = 10000

    def __init__(
        self,
        master,
        width: int = 200,
        height: int = 100,
        border_width: int = 2,
        colors: list[str] | None = None,
        direction: GradientDirection = GradientDirection.HORIZONTAL,
        corner_radius: int = 8,
        glow_intensity: GlowIntensity = GlowIntensity.NONE,
        glow_color: str | None = None,
        animated: bool = False,
        animation_speed: int = 50,
        bg_color: str | None = None,
        theme: str = "dark",
        **kwargs,
    ):
        border_width = max(1, min(border_width, self.MAX_BORDER_WIDTH))
        animation_speed = max(16, min(animation_speed, 1000))

        self._width = width
        self._height = height
        self._border_width = border_width
        self._corner_radius = max(0, min(corner_radius, min(width, height) // 2))
        self._direction = direction
        self._glow_intensity = glow_intensity
        self._animated = animated
        self._animation_speed = animation_speed
        self._animation_offset = 0
        self._animation_id: str | None = None
        self._theme = theme

        if colors is None:
            colors = [ModernColors.DARK_ACCENT, ModernColors.DARK_ACCENT_LIGHT]
        self._colors = [ensure_tkinter_color(c) for c in colors[:10] if validate_hex_color(c)]
        if not self._colors:
            self._colors = ["#8b5cf6", "#a78bfa"]

        self._glow_color = (
            ensure_tkinter_color(glow_color)
            if glow_color and validate_hex_color(glow_color)
            else self._colors[0]
        )
        self._bg_color = (
            ensure_tkinter_color(bg_color)
            if bg_color and validate_hex_color(bg_color)
            else (ModernColors.DARK_BG if theme == "dark" else ModernColors.LIGHT_BG)
        )

        glow_spread = min(glow_intensity.value * 5, self.MAX_GLOW_SPREAD)
        self._glow_spread = glow_spread
        canvas_width = width + glow_spread * 2
        canvas_height = height + glow_spread * 2

        super().__init__(
            master,
            width=canvas_width,
            height=canvas_height,
            highlightthickness=0,
            bg=self._bg_color,
            **kwargs,
        )
        self._content_frame: tk.Widget | Any | None = None
        self._create_content_frame()
        self._draw_border()

        if animated:
            self._start_animation()

    def _create_content_frame(self) -> None:
        if _CTK_AVAILABLE:
            self._content_frame = ctk.CTkFrame(
                self,
                fg_color=self._bg_color,
                corner_radius=max(0, self._corner_radius - self._border_width),
            )
        else:
            self._content_frame = tk.Frame(self, bg=self._bg_color)

        x = self._glow_spread + self._border_width
        y = self._glow_spread + self._border_width
        inner_width = self._width - self._border_width * 2
        inner_height = self._height - self._border_width * 2
        assert self._content_frame is not None
        self.create_window(
            x, y, window=self._content_frame, anchor="nw", width=inner_width, height=inner_height
        )

    def _start_animation(self) -> None:
        if self._animation_id:
            return
        self._animate()

    def _animate(self) -> None:
        self._animation_offset = (self._animation_offset + 1) % 100
        self._draw_border()
        self._animation_id = self.after(self._animation_speed, self._animate)

    def stop_animation(self) -> None:
        if self._animation_id:
            self.after_cancel(self._animation_id)
            self._animation_id = None

    def get_content_frame(self):
        """Return the inner content frame."""
        return self._content_frame

    def set_colors(self, colors: list[str]) -> None:
        validated = [ensure_tkinter_color(c) for c in colors[:10] if validate_hex_color(c)]
        if validated:
            self._colors = validated
            self._draw_border()

    def set_glow_intensity(self, intensity: GlowIntensity) -> None:
        self._glow_intensity = intensity
        self._draw_border()

    def destroy(self) -> None:
        self.stop_animation()
        super().destroy()


def create_gradient_border(
    master,
    width: int = 200,
    height: int = 100,
    colors: list[str] | None = None,
    glow: bool = False,
    animated: bool = False,
    theme: str = "dark",
) -> GradientBorder:
    """Create a gradient border with common defaults."""
    return GradientBorder(
        master,
        width=width,
        height=height,
        colors=colors,
        glow_intensity=GlowIntensity.NORMAL if glow else GlowIntensity.NONE,
        animated=animated,
        theme=theme,
    )
