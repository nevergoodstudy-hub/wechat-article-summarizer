"""Circular progress widget."""

from __future__ import annotations

from typing import Any

from .progress_colors import progress_colors_for_theme
from .progress_runtime import tk


class CircularProgress:
    """Canvas-based circular progress indicator."""

    def __init__(
        self,
        master: Any,
        size: int = 100,
        width: int = 8,
        indeterminate: bool = False,
        theme: str = "dark",
    ) -> None:
        self._size = size
        self._width = width
        self._indeterminate = indeterminate
        self._theme = theme
        self._progress = 0.0
        self._animation_angle = 0

        colors = progress_colors_for_theme(theme)
        self._canvas = tk.Canvas(
            master,
            width=size,
            height=size,
            bg=colors.background,
            highlightthickness=0,
        )

        padding = width
        self._canvas.create_oval(
            padding,
            padding,
            size - padding,
            size - padding,
            outline=colors.track,
            width=width,
        )
        self._progress_arc = self._canvas.create_arc(
            padding,
            padding,
            size - padding,
            size - padding,
            start=90,
            extent=0,
            outline=colors.foreground,
            width=width,
            style=tk.ARC,
        )

        if indeterminate:
            self._animate()

    def set(self, value: float) -> None:
        """Set progress value between 0.0 and 1.0."""
        value = max(0.0, min(1.0, value))
        self._progress = value
        self._canvas.itemconfig(self._progress_arc, extent=-360 * value)

    def get(self) -> float:
        """Return current progress value."""
        return self._progress

    def _animate(self) -> None:
        """Animate indeterminate state."""
        if not self._indeterminate:
            return
        self._animation_angle = (self._animation_angle + 5) % 360
        self._canvas.itemconfig(self._progress_arc, start=self._animation_angle, extent=-90)
        self._canvas.after(16, self._animate)

    def pack(self, **kwargs: Any) -> None:
        """Pack the canvas."""
        self._canvas.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """Grid the canvas."""
        self._canvas.grid(**kwargs)


__all__ = ["CircularProgress"]
