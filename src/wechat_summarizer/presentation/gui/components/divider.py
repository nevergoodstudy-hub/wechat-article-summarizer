"""Divider component."""

from __future__ import annotations

import tkinter as tk

from ..styles.colors import ModernColors
from .border_utils import interpolate_color, validate_hex_color


class Divider(tk.Canvas):
    """Solid, faded, or gradient divider."""

    def __init__(
        self,
        master,
        orientation: str = "horizontal",
        length: int = 200,
        thickness: int = 1,
        color: str | None = None,
        gradient_colors: list[str] | None = None,
        fade_edges: bool = False,
        theme: str = "dark",
        **kwargs,
    ):
        self._orientation = orientation
        self._length = length
        self._thickness = max(1, min(thickness, 10))
        self._fade_edges = fade_edges
        self._theme = theme

        if color and validate_hex_color(color):
            self._color = color
        else:
            self._color = (
                ModernColors.DARK_DIVIDER if theme == "dark" else ModernColors.LIGHT_DIVIDER
            )

        self._gradient_colors: list[str] | None = None
        if gradient_colors:
            validated = [c for c in gradient_colors[:5] if validate_hex_color(c)]
            if validated:
                self._gradient_colors = validated

        if orientation == "horizontal":
            width = length
            height = thickness
        else:
            width = thickness
            height = length

        bg_color = ModernColors.DARK_BG if theme == "dark" else ModernColors.LIGHT_BG
        super().__init__(
            master, width=width, height=height, highlightthickness=0, bg=bg_color, **kwargs
        )
        self._draw_divider()

    def _draw_divider(self) -> None:
        self.delete("all")
        if self._gradient_colors:
            self._draw_gradient_line()
        elif self._fade_edges:
            self._draw_faded_line()
        else:
            self._draw_solid_line()

    def _draw_solid_line(self) -> None:
        if self._orientation == "horizontal":
            self.create_line(
                0,
                self._thickness / 2,
                self._length,
                self._thickness / 2,
                fill=self._color,
                width=self._thickness,
            )
        else:
            self.create_line(
                self._thickness / 2,
                0,
                self._thickness / 2,
                self._length,
                fill=self._color,
                width=self._thickness,
            )

    def _draw_faded_line(self) -> None:
        steps = 20
        fade_length = self._length // 4
        bg_color = ModernColors.DARK_BG if self._theme == "dark" else ModernColors.LIGHT_BG

        for i in range(steps):
            t = i / steps
            start_color = interpolate_color(bg_color, self._color, t)
            start_pos = t * fade_length
            end_color = interpolate_color(self._color, bg_color, t)
            end_pos = self._length - fade_length + t * fade_length
            self._draw_fade_segment(start_pos, start_color, fade_length, steps)
            self._draw_fade_segment(end_pos, end_color, fade_length, steps)

        if self._orientation == "horizontal":
            self.create_line(
                fade_length,
                self._thickness / 2,
                self._length - fade_length,
                self._thickness / 2,
                fill=self._color,
                width=self._thickness,
            )
        else:
            self.create_line(
                self._thickness / 2,
                fade_length,
                self._thickness / 2,
                self._length - fade_length,
                fill=self._color,
                width=self._thickness,
            )

    def _draw_fade_segment(
        self,
        pos: float,
        color: str,
        fade_length: int,
        steps: int,
    ) -> None:
        if self._orientation == "horizontal":
            self.create_line(
                pos,
                self._thickness / 2,
                pos + fade_length / steps + 1,
                self._thickness / 2,
                fill=color,
                width=self._thickness,
            )
        else:
            self.create_line(
                self._thickness / 2,
                pos,
                self._thickness / 2,
                pos + fade_length / steps + 1,
                fill=color,
                width=self._thickness,
            )

    def _draw_gradient_line(self) -> None:
        steps = min(self._length, 100)
        for i in range(steps):
            color = self._gradient_color_at(i / steps)
            pos = i * self._length / steps
            if self._orientation == "horizontal":
                self.create_line(
                    pos,
                    self._thickness / 2,
                    pos + self._length / steps + 1,
                    self._thickness / 2,
                    fill=color,
                    width=self._thickness,
                )
            else:
                self.create_line(
                    self._thickness / 2,
                    pos,
                    self._thickness / 2,
                    pos + self._length / steps + 1,
                    fill=color,
                    width=self._thickness,
                )

    def _gradient_color_at(self, t: float) -> str:
        if self._gradient_colors is None:
            return self._color
        n = len(self._gradient_colors) - 1
        if n <= 0:
            return self._gradient_colors[0]
        segment = t * n
        idx = min(int(segment), n - 1)
        local_t = segment - idx
        return interpolate_color(
            self._gradient_colors[idx], self._gradient_colors[idx + 1], local_t
        )


def create_divider(
    master,
    orientation: str = "horizontal",
    length: int = 200,
    gradient: bool = False,
    fade: bool = False,
    theme: str = "dark",
) -> Divider:
    """Create a divider with common defaults."""
    gradient_colors = None
    if gradient:
        if theme == "dark":
            gradient_colors = [ModernColors.DARK_ACCENT, ModernColors.DARK_ACCENT_LIGHT]
        else:
            gradient_colors = [ModernColors.LIGHT_ACCENT, ModernColors.LIGHT_ACCENT_LIGHT]

    return Divider(
        master,
        orientation=orientation,
        length=length,
        gradient_colors=gradient_colors,
        fade_edges=fade,
        theme=theme,
    )
