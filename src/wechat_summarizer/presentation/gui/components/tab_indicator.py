"""Animated active-tab indicator."""

from __future__ import annotations

import contextlib
import tkinter as tk
from typing import Any


class TabIndicator:
    """滑动指示器动画组件"""

    def __init__(
        self,
        canvas: tk.Canvas,
        color: str,
        height: int = 3,
        animation_duration: int = 200,
    ):
        self._canvas = canvas
        self._color = color
        self._height = max(1, min(height, 10))
        self._duration = max(50, min(animation_duration, 500))
        self._animation_id: Any | None = None
        self._x = 0.0
        self._width = 0.0
        self._target_x = 0
        self._target_width = 0
        self._y = 0

        self._indicator_id = self._canvas.create_rectangle(
            0,
            0,
            0,
            0,
            fill=color,
            outline="",
            tags="indicator",
        )

    def move_to(self, x: int, width: int, y: int) -> None:
        """Move the indicator to the target bounds."""
        self._target_x = max(0, x)
        self._target_width = max(0, width)
        self._y = y
        self._animate()

    def _animate(self) -> None:
        if self._animation_id:
            with contextlib.suppress(Exception):
                self._canvas.after_cancel(self._animation_id)

        steps = max(1, self._duration // 16)
        start_x = self._x
        start_width = self._width
        delta_x = self._target_x - start_x
        delta_width = self._target_width - start_width
        current_step = [0]

        def animate_step() -> None:
            if current_step[0] >= steps:
                self._x = self._target_x
                self._width = self._target_width
                self._update_rect()
                return

            progress = current_step[0] / steps
            eased = progress * progress * (3 - 2 * progress)
            self._x = start_x + delta_x * eased
            self._width = start_width + delta_width * eased
            self._update_rect()

            current_step[0] += 1
            self._animation_id = self._canvas.after(16, animate_step)

        animate_step()

    def _update_rect(self) -> None:
        self._canvas.coords(
            self._indicator_id,
            self._x,
            self._y,
            self._x + self._width,
            self._y + self._height,
        )

    def set_color(self, color: str) -> None:
        """Set the indicator fill color."""
        self._color = color
        self._canvas.itemconfig(self._indicator_id, fill=color)

    def destroy(self) -> None:
        """Destroy scheduled animation and canvas item."""
        if self._animation_id:
            with contextlib.suppress(Exception):
                self._canvas.after_cancel(self._animation_id)
        self._canvas.delete(self._indicator_id)


__all__ = ["TabIndicator"]
