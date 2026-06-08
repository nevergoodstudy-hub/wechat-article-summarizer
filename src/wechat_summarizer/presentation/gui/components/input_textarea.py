"""Multi-line modern text input widget."""

from __future__ import annotations

import tkinter as tk
from typing import Any

from ..styles.typography import TextStyles, get_text_style
from .input_compat import CTK_AVAILABLE, TextAreaBase, create_transparent_frame
from .input_state import ValidationState, input_colors, secondary_text_color


class ModernTextArea(TextAreaBase):  # type: ignore[misc]
    """Modern multi-line text box with optional label and length limit."""

    def __init__(
        self,
        master: Any,
        label: str | None = None,
        placeholder: str = "",
        height: int = 120,
        max_length: int | None = None,
        theme: str = "dark",
        **kwargs: Any,
    ):
        self._label = label
        self._placeholder = placeholder
        self._max_length = max_length
        self._theme = theme
        self._container = create_transparent_frame(master)

        if label:
            self._create_label()

        colors = input_colors(theme, ValidationState.DEFAULT)

        if CTK_AVAILABLE:
            super().__init__(
                self._container,
                fg_color=colors["bg"],
                text_color=colors["text"],
                border_color=colors["border"],
                border_width=2,
                corner_radius=8,
                height=height,
                font=get_text_style(TextStyles.BODY),
                **kwargs,
            )
        else:
            super().__init__(
                self._container,
                bg=colors["bg"],
                fg=colors["text"],
                insertbackground=colors["text"],
                relief="solid",
                bd=2,
                height=height // 20,
                **kwargs,
            )

        TextAreaBase.pack(self, fill="both", expand=True)

        if max_length:
            self.bind("<KeyRelease>", self._check_length)

    def _create_label(self) -> None:
        text_color = secondary_text_color(self._theme)

        if CTK_AVAILABLE:
            from .input_compat import ctk

            label = ctk.CTkLabel(
                self._container,
                text=self._label or "",
                font=get_text_style(TextStyles.LABEL_SMALL),
                text_color=text_color,
                anchor="w",
            )
        else:
            label = tk.Label(
                self._container,
                text=self._label or "",
                font=get_text_style(TextStyles.LABEL_SMALL),
                fg=text_color,
                anchor="w",
            )
        label.pack(fill="x", pady=(0, 5))

    def _check_length(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        if self._max_length:
            current = self.get("1.0", tk.END)
            if len(current) - 1 > self._max_length:
                self.delete(f"1.{self._max_length}", tk.END)

    def clear(self) -> None:
        self.delete("1.0", tk.END)

    def pack(self, **kwargs: Any) -> None:
        self._container.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        self._container.grid(**kwargs)
