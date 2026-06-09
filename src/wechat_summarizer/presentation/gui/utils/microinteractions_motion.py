"""Pulse and expand/collapse microinteractions."""

from __future__ import annotations

import contextlib
import math
import tkinter as tk
from collections.abc import Callable
from typing import Any, cast


class PulseEffect:
    """脉冲效果（元素闪烁）"""

    def __init__(
        self,
        widget: tk.Widget,
        color1: str = "#3b82f6",
        color2: str = "#60a5fa",
        duration: int = 1000,
    ):
        self.widget = widget
        self.color1 = color1
        self.color2 = color2
        self.duration = duration
        self._is_animating = False
        self._animation_id: str | None = None
        self._step = 0

    def start(self) -> None:
        if self._is_animating:
            return

        self._is_animating = True
        self._animate()

    def stop(self) -> None:
        self._is_animating = False
        if self._animation_id:
            with contextlib.suppress(tk.TclError):
                self.widget.after_cancel(self._animation_id)
            self._animation_id = None

    def _animate(self) -> None:
        if not self._is_animating:
            return

        progress = (math.sin(self._step * 0.1) + 1) / 2
        r1, g1, b1 = self._hex_to_rgb(self.color1)
        r2, g2, b2 = self._hex_to_rgb(self.color2)

        r = int(r1 + (r2 - r1) * progress)
        g = int(g1 + (g2 - g1) * progress)
        b = int(b1 + (b2 - b1) * progress)

        with contextlib.suppress(tk.TclError):
            cast(Any, self.widget).configure(bg=f"#{r:02x}{g:02x}{b:02x}")

        self._step += 1
        self._animation_id = self.widget.after(50, self._animate)

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return cast(
            tuple[int, int, int],
            tuple(int(hex_color[index : index + 2], 16) for index in (0, 2, 4)),
        )

    def destroy(self) -> None:
        self.stop()


class CollapseExpand:
    """展开/收起动画"""

    def __init__(
        self,
        widget: tk.Widget,
        expanded_height: int,
        collapsed_height: int = 0,
        duration: int = 300,
    ):
        self.widget = widget
        self.expanded_height = expanded_height
        self.collapsed_height = collapsed_height
        self.duration = duration
        self._is_expanded = True
        self._is_animating = False
        self._animation_id: str | None = None

    def toggle(self, on_complete: Callable[[], None] | None = None) -> None:
        if self._is_animating:
            return

        if self._is_expanded:
            self.collapse(on_complete)
        else:
            self.expand(on_complete)

    def expand(self, on_complete: Callable[[], None] | None = None) -> None:
        if self._is_expanded or self._is_animating:
            return

        self._animate(
            self.collapsed_height,
            self.expanded_height,
            lambda: self._on_expand_complete(on_complete),
        )

    def collapse(self, on_complete: Callable[[], None] | None = None) -> None:
        if not self._is_expanded or self._is_animating:
            return

        self._animate(
            self.expanded_height,
            self.collapsed_height,
            lambda: self._on_collapse_complete(on_complete),
        )

    def _animate(self, from_height: int, to_height: int, on_complete: Callable[[], None]) -> None:
        self._is_animating = True
        steps = max(1, self.duration // 16)

        def animate(step: int) -> None:
            if step > steps:
                self._is_animating = False
                self._animation_id = None
                on_complete()
                return

            progress = self._ease_out(step / steps)
            current_height = int(from_height + (to_height - from_height) * progress)

            with contextlib.suppress(tk.TclError):
                cast(Any, self.widget).configure(height=max(1, current_height))

            self._animation_id = self.widget.after(16, lambda: animate(step + 1))

        animate(1)

    def _on_expand_complete(self, callback: Callable[[], None] | None) -> None:
        self._is_expanded = True
        if callback:
            callback()

    def _on_collapse_complete(self, callback: Callable[[], None] | None) -> None:
        self._is_expanded = False
        if callback:
            callback()

    def _ease_out(self, value: float) -> float:
        return 1 - (1 - value) ** 3

    def is_expanded(self) -> bool:
        return self._is_expanded

    def destroy(self) -> None:
        if self._animation_id:
            with contextlib.suppress(tk.TclError):
                self.widget.after_cancel(self._animation_id)


__all__ = [
    "CollapseExpand",
    "PulseEffect",
]
