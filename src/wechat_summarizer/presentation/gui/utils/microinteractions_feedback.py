"""Click and hover feedback effects for GUI widgets."""

from __future__ import annotations

import contextlib
import math
import tkinter as tk
from typing import Any, cast


class RippleEffect:
    """水波纹点击效果"""

    def __init__(
        self,
        widget: tk.Widget,
        color: str = "#ffffff",
        duration: int = 400,
        max_radius: int = 100,
    ):
        self.widget = widget
        self.color = color
        self.duration = duration
        self.max_radius = max_radius

        self._canvas: tk.Canvas | None = None
        self._ripple_id: int | None = None
        self._animation_id: str | None = None
        self._is_animating = False

        self.widget.bind("<Button-1>", self._on_click, add="+")

    def _on_click(self, event: Any) -> None:
        if self._is_animating:
            return

        self._is_animating = True
        widget_width = self.widget.winfo_width()
        widget_height = self.widget.winfo_height()

        self._canvas = tk.Canvas(
            self.widget,
            width=widget_width,
            height=widget_height,
            highlightthickness=0,
            bg="",
        )
        self._canvas.place(x=0, y=0)

        click_x = int(event.x)
        click_y = int(event.y)
        corners = [(0, 0), (widget_width, 0), (0, widget_height), (widget_width, widget_height)]
        max_dist = max(math.sqrt((click_x - cx) ** 2 + (click_y - cy) ** 2) for cx, cy in corners)
        self.max_radius = int(max_dist)

        self._ripple_id = self._canvas.create_oval(
            click_x,
            click_y,
            click_x,
            click_y,
            fill=self.color,
            outline="",
        )
        self._animate_ripple(click_x, click_y, 0)

    def _animate_ripple(self, cx: int, cy: int, step: int) -> None:
        total_steps = max(1, self.duration // 16)

        if step > total_steps:
            self._cleanup()
            return

        progress = step / total_steps
        radius = int(self.max_radius * self._ease_out(progress))
        canvas = self._canvas
        ripple_id = self._ripple_id
        if canvas is None or ripple_id is None:
            self._cleanup()
            return

        canvas.coords(ripple_id, cx - radius, cy - radius, cx + radius, cy + radius)
        with contextlib.suppress(tk.TclError):
            gray_val = min(255, 200 + int(55 * progress))
            canvas.itemconfig(ripple_id, fill=f"#{gray_val:02x}{gray_val:02x}{gray_val:02x}")

        self._animation_id = self.widget.after(16, lambda: self._animate_ripple(cx, cy, step + 1))

    def _ease_out(self, value: float) -> float:
        return 1 - (1 - value) ** 3

    def _cleanup(self) -> None:
        self._is_animating = False
        if self._canvas:
            self._canvas.destroy()
            self._canvas = None
        self._ripple_id = None

    def destroy(self) -> None:
        if self._animation_id:
            with contextlib.suppress(tk.TclError):
                self.widget.after_cancel(self._animation_id)
        self._cleanup()
        with contextlib.suppress(tk.TclError):
            self.widget.unbind("<Button-1>")


class ScaleEffect:
    """点击缩放效果"""

    def __init__(self, widget: tk.Widget, scale_down: float = 0.95, duration: int = 100):
        self.widget = widget
        self.scale_down = scale_down
        self.duration = duration

        self._original_width = 0
        self._original_height = 0
        self._animation_id: str | None = None
        self._is_animating = False

        self.widget.bind("<ButtonPress-1>", self._on_press, add="+")
        self.widget.bind("<ButtonRelease-1>", self._on_release, add="+")

    def _on_press(self, _event: Any) -> None:
        if self._is_animating:
            return

        self._original_width = self.widget.winfo_width()
        self._original_height = self.widget.winfo_height()
        self._animate_scale(1.0, self.scale_down)

    def _on_release(self, _event: Any) -> None:
        self._animate_scale(self.scale_down, 1.0)

    def _animate_scale(self, from_scale: float, to_scale: float) -> None:
        self._is_animating = True
        steps = max(1, self.duration // 16)

        def animate(step: int) -> None:
            if step > steps:
                self._is_animating = False
                self._animation_id = None
                return

            progress = step / steps
            current_scale = from_scale + (to_scale - from_scale) * self._ease_out(progress)
            padding = int((1 - current_scale) * 5)
            with contextlib.suppress(tk.TclError):
                cast(Any, self.widget).configure(padx=padding, pady=padding)

            self._animation_id = self.widget.after(16, lambda: animate(step + 1))

        animate(1)

    def _ease_out(self, value: float) -> float:
        return 1 - (1 - value) ** 2

    def destroy(self) -> None:
        if self._animation_id:
            with contextlib.suppress(tk.TclError):
                self.widget.after_cancel(self._animation_id)
        with contextlib.suppress(tk.TclError):
            self.widget.unbind("<ButtonPress-1>")
            self.widget.unbind("<ButtonRelease-1>")


class HoverEffect:
    """悬停效果"""

    def __init__(
        self,
        widget: tk.Widget,
        hover_bg: str | None = None,
        normal_bg: str | None = None,
        lift_pixels: int = 2,
        duration: int = 150,
    ):
        self.widget = widget
        self.hover_bg = hover_bg
        self.normal_bg = normal_bg or str(widget.cget("bg"))
        self.lift_pixels = lift_pixels
        self.duration = duration

        self._original_y = 0
        self._is_hovered = False

        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event: Any) -> None:
        if self._is_hovered:
            return

        self._is_hovered = True

        if self.hover_bg:
            with contextlib.suppress(tk.TclError):
                cast(Any, self.widget).configure(bg=self.hover_bg)
                for child in self.widget.winfo_children():
                    with contextlib.suppress(tk.TclError):
                        cast(Any, child).configure(bg=self.hover_bg)

        if self.lift_pixels > 0:
            with contextlib.suppress(tk.TclError, ValueError):
                info = self.widget.place_info()
                if info:
                    current_y = int(info.get("y", 0))
                    self._original_y = current_y
                    self.widget.place(y=current_y - self.lift_pixels)

    def _on_leave(self, _event: Any) -> None:
        if not self._is_hovered:
            return

        self._is_hovered = False

        with contextlib.suppress(tk.TclError):
            cast(Any, self.widget).configure(bg=self.normal_bg)
            for child in self.widget.winfo_children():
                with contextlib.suppress(tk.TclError):
                    cast(Any, child).configure(bg=self.normal_bg)

        if self.lift_pixels > 0:
            with contextlib.suppress(tk.TclError):
                self.widget.place(y=self._original_y)

    def destroy(self) -> None:
        with contextlib.suppress(tk.TclError):
            self.widget.unbind("<Enter>")
            self.widget.unbind("<Leave>")


__all__ = [
    "HoverEffect",
    "RippleEffect",
    "ScaleEffect",
]
