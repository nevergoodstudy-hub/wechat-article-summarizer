"""Loading microinteractions for GUI widgets."""

from __future__ import annotations

import contextlib
import tkinter as tk


class SkeletonLoader(tk.Frame):
    """骨架屏加载动画"""

    def __init__(
        self,
        parent: tk.Misc,
        width: int = 200,
        height: int = 20,
        bg_color: str = "#2a2a2a",
        highlight_color: str = "#3a3a3a",
        **kwargs,
    ):
        super().__init__(parent, width=width, height=height, **kwargs)

        self.bg_color = bg_color
        self.highlight_color = highlight_color
        self._width = width
        self._height = height
        self._is_animating = True
        self._animation_id: str | None = None

        self.configure(bg=bg_color)
        self.pack_propagate(False)

        self.canvas = tk.Canvas(self, width=width, height=height, bg=bg_color, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._highlight = self.canvas.create_rectangle(
            -50,
            0,
            0,
            height,
            fill=highlight_color,
            outline="",
        )

        self._animate()

    def _animate(self) -> None:
        if not self._is_animating:
            return

        self.canvas.move(self._highlight, 5, 0)
        coords = self.canvas.coords(self._highlight)
        if coords[0] > self._width:
            self.canvas.coords(self._highlight, -50, 0, 0, self._height)

        self._animation_id = self.after(30, self._animate)

    def stop(self) -> None:
        self._is_animating = False
        if self._animation_id:
            with contextlib.suppress(tk.TclError):
                self.after_cancel(self._animation_id)
            self._animation_id = None

    def destroy(self) -> None:
        self.stop()
        super().destroy()


class Spinner(tk.Canvas):
    """旋转加载指示器"""

    def __init__(
        self,
        parent: tk.Misc,
        size: int = 32,
        color: str = "#3b82f6",
        thickness: int = 3,
        **kwargs,
    ):
        super().__init__(parent, width=size, height=size, highlightthickness=0, **kwargs)
        self._size = size
        self.color = color
        self.thickness = thickness
        self._angle = 0
        self._arc_length = 90
        self._is_animating = True
        self._animation_id: str | None = None

        self._draw()
        self._animate()

    def _draw(self) -> None:
        self.delete("arc")

        padding = self.thickness + 2
        self.create_arc(
            padding,
            padding,
            self._size - padding,
            self._size - padding,
            start=self._angle,
            extent=self._arc_length,
            style=tk.ARC,
            outline=self.color,
            width=self.thickness,
            tags="arc",
        )

    def _animate(self) -> None:
        if not self._is_animating:
            return

        self._angle = (self._angle + 10) % 360
        self._draw()
        self._animation_id = self.after(30, self._animate)

    def stop(self) -> None:
        self._is_animating = False
        if self._animation_id:
            with contextlib.suppress(tk.TclError):
                self.after_cancel(self._animation_id)
            self._animation_id = None

    def start(self) -> None:
        if not self._is_animating:
            self._is_animating = True
            self._animate()

    def destroy(self) -> None:
        self.stop()
        super().destroy()


__all__ = [
    "SkeletonLoader",
    "Spinner",
]
