"""Linear progress widget."""

from __future__ import annotations

from typing import Any, cast

from .progress_colors import progress_colors_for_theme
from .progress_runtime import CTK_AVAILABLE, LinearProgressBase


class LinearProgress(LinearProgressBase):  # type: ignore[misc]
    """Linear progress bar supporting determinate and indeterminate states."""

    def __init__(
        self,
        master: Any,
        width: int = 300,
        height: int = 4,
        indeterminate: bool = False,
        theme: str = "dark",
        corner_radius: int | None = None,
        **kwargs: Any,
    ) -> None:
        self._width = width
        self._height = height
        self._indeterminate = indeterminate
        self._theme = theme
        self._progress = 0.0
        self._progress_rect: int | None = None

        if corner_radius is None:
            corner_radius = height // 2

        colors = progress_colors_for_theme(theme)
        if CTK_AVAILABLE:
            super().__init__(
                master,
                width=width,
                height=height,
                fg_color=colors.track,
                progress_color=colors.foreground,
                corner_radius=corner_radius,
                **kwargs,
            )
            if indeterminate:
                self.configure(mode="indeterminate")
                self.start()
            else:
                self.set(0)
        else:
            super().__init__(
                master,
                width=width,
                height=height,
                bg=colors.track,
                highlightthickness=0,
                **kwargs,
            )
            self.create_rectangle(0, 0, width, height, fill=colors.track, outline="")
            self._progress_rect = self.create_rectangle(
                0, 0, 0, height, fill=colors.foreground, outline=""
            )

    def update_theme(self, mode: str) -> None:
        """Switch widget colors to a new theme."""
        self._theme = mode
        colors = progress_colors_for_theme(mode)
        if CTK_AVAILABLE:
            self.configure(fg_color=colors.track, progress_color=colors.foreground)

    def set(self, value: float) -> None:
        """Set progress value between 0.0 and 1.0."""
        value = max(0.0, min(1.0, value))
        self._progress = value
        if CTK_AVAILABLE:
            super().set(value)
            return
        if self._progress_rect is not None:
            progress_width = int(self._width * value)
            self.coords(self._progress_rect, 0, 0, progress_width, self._height)

    def get(self) -> float:
        """Return current progress value."""
        if CTK_AVAILABLE:
            return float(cast(Any, super()).get())
        return self._progress


__all__ = ["LinearProgress"]
