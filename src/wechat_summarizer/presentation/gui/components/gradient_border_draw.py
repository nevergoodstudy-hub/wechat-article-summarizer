"""Drawing mixin for gradient border canvases."""

from __future__ import annotations

from typing import Any

from .border_utils import (
    GlowIntensity,
    GradientDirection,
    hex_to_rgb,
    interpolate_color,
    rgb_to_hex,
)


class GradientBorderDrawingMixin:
    """Canvas drawing operations for a gradient border."""

    def _draw_border(self: Any) -> None:
        self.delete("border")
        self.delete("glow")

        if self._glow_intensity != GlowIntensity.NONE:
            self._draw_glow()

        steps = max(10, self._width + self._height)
        steps = min(steps, 200)

        if self._direction == GradientDirection.HORIZONTAL:
            self._draw_horizontal_gradient(steps)
        elif self._direction == GradientDirection.VERTICAL:
            self._draw_vertical_gradient(steps)
        elif self._direction == GradientDirection.DIAGONAL:
            self._draw_diagonal_gradient(steps)
        else:
            self._draw_radial_gradient()

    def _draw_glow(self: Any) -> None:
        spread = self._glow_spread
        if spread <= 0:
            return

        layers = spread
        base_rgb = hex_to_rgb(self._glow_color)
        bg_rgb = hex_to_rgb(self._bg_color)

        for i in range(layers, 0, -1):
            alpha = (layers - i) / layers * 0.3
            blended = (
                int(base_rgb[0] * alpha + bg_rgb[0] * (1 - alpha)),
                int(base_rgb[1] * alpha + bg_rgb[1] * (1 - alpha)),
                int(base_rgb[2] * alpha + bg_rgb[2] * (1 - alpha)),
            )
            color = rgb_to_hex(blended)
            offset = spread - i
            self._draw_rounded_rect(
                offset,
                offset,
                self._width + spread * 2 - offset * 2,
                self._height + spread * 2 - offset * 2,
                self._corner_radius + i,
                color,
                "glow",
            )

    def _draw_horizontal_gradient(self: Any, steps: int) -> None:
        for i in range(steps):
            t = (i + self._animation_offset) % steps / steps
            color = self._get_gradient_color(t)
            x = self._glow_spread + i * self._width / steps
            self.create_line(
                x,
                self._glow_spread,
                x + self._width / steps + 1,
                self._glow_spread,
                fill=color,
                width=self._border_width,
                tags="border",
            )
            self.create_line(
                x,
                self._glow_spread + self._height,
                x + self._width / steps + 1,
                self._glow_spread + self._height,
                fill=color,
                width=self._border_width,
                tags="border",
            )

        left_color = self._get_gradient_color(self._animation_offset / steps if steps > 0 else 0)
        right_color = self._get_gradient_color(
            (self._animation_offset + steps - 1) % steps / steps if steps > 0 else 1
        )
        self.create_line(
            self._glow_spread,
            self._glow_spread,
            self._glow_spread,
            self._glow_spread + self._height,
            fill=left_color,
            width=self._border_width,
            tags="border",
        )
        self.create_line(
            self._glow_spread + self._width,
            self._glow_spread,
            self._glow_spread + self._width,
            self._glow_spread + self._height,
            fill=right_color,
            width=self._border_width,
            tags="border",
        )

    def _draw_vertical_gradient(self: Any, steps: int) -> None:
        for i in range(steps):
            t = (i + self._animation_offset) % steps / steps
            color = self._get_gradient_color(t)
            y = self._glow_spread + i * self._height / steps
            self.create_line(
                self._glow_spread,
                y,
                self._glow_spread,
                y + self._height / steps + 1,
                fill=color,
                width=self._border_width,
                tags="border",
            )
            self.create_line(
                self._glow_spread + self._width,
                y,
                self._glow_spread + self._width,
                y + self._height / steps + 1,
                fill=color,
                width=self._border_width,
                tags="border",
            )

        top_color = self._get_gradient_color(self._animation_offset / steps if steps > 0 else 0)
        bottom_color = self._get_gradient_color(
            (self._animation_offset + steps - 1) % steps / steps if steps > 0 else 1
        )
        self.create_line(
            self._glow_spread,
            self._glow_spread,
            self._glow_spread + self._width,
            self._glow_spread,
            fill=top_color,
            width=self._border_width,
            tags="border",
        )
        self.create_line(
            self._glow_spread,
            self._glow_spread + self._height,
            self._glow_spread + self._width,
            self._glow_spread + self._height,
            fill=bottom_color,
            width=self._border_width,
            tags="border",
        )

    def _draw_diagonal_gradient(self: Any, steps: int) -> None:
        half_bw = self._border_width / 2
        current = 0
        current = self._draw_diagonal_top(steps, current, half_bw)
        current = self._draw_diagonal_right(steps, current, half_bw)
        current = self._draw_diagonal_bottom(steps, current, half_bw)
        self._draw_diagonal_left(steps, current, half_bw)

    def _draw_diagonal_top(self: Any, steps: int, current: float, half_bw: float) -> float:
        for i in range(int(self._width)):
            t = ((current + i + self._animation_offset) % steps) / steps
            x = self._glow_spread + i
            self.create_line(
                x,
                self._glow_spread + half_bw,
                x + 1,
                self._glow_spread + half_bw,
                fill=self._get_gradient_color(t),
                width=self._border_width,
                tags="border",
            )
        return float(current + self._width)

    def _draw_diagonal_right(self: Any, steps: int, current: float, half_bw: float) -> float:
        for i in range(int(self._height)):
            t = ((current + i + self._animation_offset) % steps) / steps
            y = self._glow_spread + i
            self.create_line(
                self._glow_spread + self._width - half_bw,
                y,
                self._glow_spread + self._width - half_bw,
                y + 1,
                fill=self._get_gradient_color(t),
                width=self._border_width,
                tags="border",
            )
        return float(current + self._height)

    def _draw_diagonal_bottom(self: Any, steps: int, current: float, half_bw: float) -> float:
        for i in range(int(self._width)):
            t = ((current + i + self._animation_offset) % steps) / steps
            x = self._glow_spread + self._width - i
            self.create_line(
                x,
                self._glow_spread + self._height - half_bw,
                x - 1,
                self._glow_spread + self._height - half_bw,
                fill=self._get_gradient_color(t),
                width=self._border_width,
                tags="border",
            )
        return float(current + self._width)

    def _draw_diagonal_left(self: Any, steps: int, current: float, half_bw: float) -> None:
        for i in range(int(self._height)):
            t = ((current + i + self._animation_offset) % steps) / steps
            y = self._glow_spread + self._height - i
            self.create_line(
                self._glow_spread + half_bw,
                y,
                self._glow_spread + half_bw,
                y - 1,
                fill=self._get_gradient_color(t),
                width=self._border_width,
                tags="border",
            )

    def _draw_radial_gradient(self: Any) -> None:
        self._draw_rounded_rect(
            self._glow_spread,
            self._glow_spread,
            self._width,
            self._height,
            self._corner_radius,
            self._colors[0],
            "border",
            outline_only=True,
        )

    def _draw_rounded_rect(
        self: Any,
        x: float,
        y: float,
        width: float,
        height: float,
        radius: float,
        color: str,
        tags: str,
        outline_only: bool = False,
    ) -> None:
        radius = min(radius, width / 2, height / 2)
        points = [
            x + radius,
            y,
            x + width - radius,
            y,
            x + width,
            y,
            x + width,
            y + radius,
            x + width,
            y + height - radius,
            x + width,
            y + height,
            x + width - radius,
            y + height,
            x + radius,
            y + height,
            x,
            y + height,
            x,
            y + height - radius,
            x,
            y + radius,
            x,
            y,
            x + radius,
            y,
        ]
        if outline_only:
            self.create_polygon(
                points, outline=color, fill="", width=self._border_width, smooth=True, tags=tags
            )
        else:
            self.create_polygon(points, fill=color, outline="", smooth=True, tags=tags)

    def _get_gradient_color(self: Any, t: float) -> str:
        if len(self._colors) == 1:
            return str(self._colors[0])
        n = len(self._colors) - 1
        segment = t * n
        idx = min(int(segment), n - 1)
        local_t = segment - idx
        return str(interpolate_color(self._colors[idx], self._colors[idx + 1], local_t))
