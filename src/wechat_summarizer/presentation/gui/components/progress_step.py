"""Step progress widget."""

from __future__ import annotations

from typing import Any

from .progress_colors import progress_colors_for_theme
from .progress_runtime import CTK_AVAILABLE, ctk, tk


class StepProgress:
    """Progress indicator for multi-step flows."""

    def __init__(self, master: Any, steps: list[str], theme: str = "dark") -> None:
        self._steps = steps
        self._current_step = 0
        self._theme = theme

        if CTK_AVAILABLE and ctk is not None:
            self._container = ctk.CTkFrame(master, fg_color="transparent")
        else:
            self._container = tk.Frame(master)

        colors = progress_colors_for_theme(theme)
        self._colors = {
            "active": colors.foreground,
            "inactive": colors.inactive,
            "text": colors.text,
            "text_inactive": colors.text_inactive,
        }
        self._step_widgets: list[tuple[Any, Any]] = []
        self._create_steps()

    def _create_steps(self) -> None:
        """Create step indicators."""
        for index, step_name in enumerate(self._steps):
            if CTK_AVAILABLE and ctk is not None:
                step_frame = ctk.CTkFrame(self._container, fg_color="transparent")
            else:
                step_frame = tk.Frame(self._container)
            step_frame.pack(side="left", padx=10)

            is_active = index == self._current_step
            color = self._colors["active"] if is_active else self._colors["inactive"]
            indicator = tk.Canvas(
                step_frame,
                width=32,
                height=32,
                bg=self._colors["active"] if index < self._current_step else "transparent",
                highlightthickness=0,
            )
            indicator.pack()
            self._draw_indicator(indicator, index, color)

            text_color = self._colors["text"] if is_active else self._colors["text_inactive"]
            if CTK_AVAILABLE and ctk is not None:
                label = ctk.CTkLabel(
                    step_frame,
                    text=step_name,
                    text_color=text_color,
                    font=("Arial", 12),
                )
            else:
                label = tk.Label(step_frame, text=step_name, fg=text_color, font=("Arial", 12))
            label.pack(pady=(5, 0))
            self._step_widgets.append((indicator, label))

    def _draw_indicator(self, indicator: Any, index: int, color: str) -> None:
        """Draw one step marker."""
        if index < self._current_step:
            indicator.create_oval(4, 4, 28, 28, fill=color, outline="")
            indicator.create_line(10, 16, 14, 20, fill="white", width=2)
            indicator.create_line(14, 20, 22, 10, fill="white", width=2)
        elif index == self._current_step:
            indicator.create_oval(4, 4, 28, 28, fill=color, outline="")
        else:
            indicator.create_oval(4, 4, 28, 28, outline=color, width=2)

    def set_step(self, step: int) -> None:
        """Set current step by zero-based index."""
        if 0 <= step < len(self._steps):
            self._current_step = step

    def next_step(self) -> None:
        """Move to next step."""
        if self._current_step < len(self._steps) - 1:
            self.set_step(self._current_step + 1)

    def prev_step(self) -> None:
        """Move to previous step."""
        if self._current_step > 0:
            self.set_step(self._current_step - 1)

    def pack(self, **kwargs: Any) -> None:
        """Pack the container."""
        self._container.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """Grid the container."""
        self._container.grid(**kwargs)


__all__ = ["StepProgress"]
