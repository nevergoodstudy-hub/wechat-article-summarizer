"""Ripple animation support for button components."""

from __future__ import annotations

import contextlib
import tkinter as tk
from typing import Any


class RippleEffect:
    """水波纹动画效果"""

    MAX_CONCURRENT_RIPPLES = 3

    def __init__(self, canvas: tk.Canvas, color: str = "#FFFFFF", duration: int = 400):
        self._canvas = canvas
        self._color = color
        self._duration = max(100, min(duration, 1000))
        self._ripples: list[dict[str, Any]] = []
        self._animation_ids: list[str] = []

    def trigger(self, x: int, y: int, max_radius: int | None = None) -> None:
        """Trigger a ripple at a button-local position."""
        if len(self._ripples) >= self.MAX_CONCURRENT_RIPPLES:
            self._cleanup_oldest()

        if max_radius is None:
            canvas_width = self._canvas.winfo_width()
            canvas_height = self._canvas.winfo_height()
            max_radius = int(((canvas_width**2 + canvas_height**2) ** 0.5) / 2) + 10

        ripple_id = f"ripple_{len(self._ripples)}_{id(self)}"
        ripple: dict[str, Any] = {
            "id": ripple_id,
            "x": x,
            "y": y,
            "radius": 0,
            "max_radius": max_radius,
            "alpha": 0.4,
            "step": 0,
            "total_steps": max(1, self._duration // 16),
        }
        self._ripples.append(ripple)
        self._animate_ripple(ripple)

    def _animate_ripple(self, ripple: dict[str, Any]) -> None:
        if ripple["step"] >= ripple["total_steps"]:
            self._cleanup_ripple(ripple)
            return

        progress = ripple["step"] / ripple["total_steps"]
        eased = 1 - (1 - progress) ** 3
        radius = eased * ripple["max_radius"]
        alpha = ripple["alpha"] * (1 - progress)
        fill_color = self._color_with_alpha(self._color, alpha)

        self._canvas.delete(ripple["id"])
        x, y = ripple["x"], ripple["y"]
        self._canvas.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            fill=fill_color,
            outline="",
            tags=ripple["id"],
        )

        ripple["step"] += 1
        anim_id = self._canvas.after(16, lambda: self._animate_ripple(ripple))
        self._animation_ids.append(anim_id)

    def _color_with_alpha(self, hex_color: str, alpha: float) -> str:
        try:
            color = hex_color.lstrip("#")
            red = int(color[0:2], 16)
            green = int(color[2:4], 16)
            blue = int(color[4:6], 16)
            return f"#{int(red * alpha):02x}{int(green * alpha):02x}{int(blue * alpha):02x}"
        except Exception:
            return hex_color

    def _cleanup_ripple(self, ripple: dict[str, Any]) -> None:
        self._canvas.delete(ripple["id"])
        if ripple in self._ripples:
            self._ripples.remove(ripple)

    def _cleanup_oldest(self) -> None:
        if self._ripples:
            self._cleanup_ripple(self._ripples[0])

    def cleanup_all(self) -> None:
        """Cancel scheduled frames and remove active ripples."""
        for ripple in self._ripples.copy():
            self._canvas.delete(ripple["id"])
        self._ripples.clear()

        for anim_id in self._animation_ids:
            with contextlib.suppress(Exception):
                self._canvas.after_cancel(anim_id)
        self._animation_ids.clear()


__all__ = ["RippleEffect"]
