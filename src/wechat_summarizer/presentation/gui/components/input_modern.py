"""Single-line modern input widget."""

from __future__ import annotations

import tkinter as tk
from typing import Any

from ..styles.typography import TextStyles, get_text_style
from .input_adornments import ClearButton, FloatingLabel
from .input_compat import CTK_AVAILABLE, InputBase, create_transparent_frame
from .input_state import (
    ValidationState,
    accent_color,
    input_colors,
    muted_text_color,
    primary_text_color,
    secondary_text_color,
    validation_color,
)


class ModernInput(InputBase):  # type: ignore[misc]
    """Modern single-line input with floating label and validation state."""

    def __init__(
        self,
        master: Any,
        placeholder: str = "",
        label: str | None = None,
        validation_state: ValidationState = ValidationState.DEFAULT,
        validation_message: str | None = None,
        show_clear_button: bool = True,
        max_length: int | None = None,
        theme: str = "dark",
        **kwargs: Any,
    ):
        self._placeholder = placeholder
        self._label_text = label
        self._validation_state = validation_state
        self._validation_message = validation_message
        self._max_length = max_length
        self._theme = theme
        self._floating_label: FloatingLabel | None = None
        self._clear_button: ClearButton | None = None
        self._use_floating_label = label is not None

        self._container = create_transparent_frame(master)
        self._inner_container = create_transparent_frame(self._container)
        self._inner_container.pack(fill="x")

        colors = self._get_colors(theme, validation_state)

        if CTK_AVAILABLE:
            super().__init__(
                self._inner_container,
                placeholder_text=placeholder if not self._use_floating_label else "",
                fg_color=colors["bg"],
                text_color=colors["text"],
                border_color=colors["border"],
                border_width=2,
                corner_radius=8,
                height=40,
                font=get_text_style(TextStyles.BODY),
                **kwargs,
            )
        else:
            super().__init__(
                self._inner_container,
                bg=colors["bg"],
                fg=colors["text"],
                insertbackground=colors["text"],
                relief="solid",
                bd=2,
                **kwargs,
            )

        InputBase.pack(self, fill="x", padx=0, pady=(8 if self._use_floating_label else 5, 5))

        if self._use_floating_label:
            self._create_floating_label()
        if show_clear_button:
            self._create_clear_button()
        if validation_message:
            self._create_validation_message()

        self.bind("<KeyRelease>", self._on_key_release)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def update_theme(self, mode: str) -> None:
        self._theme = mode
        colors = self._get_colors(mode, self._validation_state)
        if CTK_AVAILABLE:
            self.configure(
                fg_color=colors["bg"],
                text_color=colors["text"],
                border_color=colors["border"],
            )

    def _create_floating_label(self) -> None:
        self._floating_label = FloatingLabel(
            self._inner_container,
            text=self._label_text or "",
            normal_color=secondary_text_color(self._theme),
            active_color=accent_color(self._theme),
            normal_y=12,
            active_y=-2,
            animation_duration=200,
        )

    def _create_clear_button(self) -> None:
        self._clear_button = ClearButton(
            self._inner_container,
            on_clear=self._on_clear,
            color=muted_text_color(self._theme),
            hover_color=primary_text_color(self._theme),
            size=14,
        )

    def _on_clear(self) -> None:
        self.delete(0, tk.END)
        self._update_clear_button()
        if self._floating_label:
            self._floating_label.deactivate(has_content=False)

    def _on_focus_in(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        if self._floating_label:
            self._floating_label.activate(has_content=bool(self.get()))

    def _on_focus_out(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        if self._floating_label:
            self._floating_label.deactivate(has_content=bool(self.get()))

    def _on_key_release(self, event: tk.Event[tk.Misc] | None = None) -> None:
        if self._max_length:
            self._check_length(event)
        self._update_clear_button()
        if self._floating_label and self.get():
            self._floating_label.activate(has_content=True)

    def _update_clear_button(self) -> None:
        if self._clear_button:
            if self.get():
                self._clear_button.show()
            else:
                self._clear_button.hide()

    def _create_validation_message(self) -> None:
        color = self._get_validation_color(self._validation_state)

        if CTK_AVAILABLE:
            from .input_compat import ctk

            msg_label = ctk.CTkLabel(
                self._container,
                text=self._validation_message or "",
                font=get_text_style(TextStyles.CAPTION),
                text_color=color,
                anchor="w",
            )
        else:
            msg_label = tk.Label(
                self._container,
                text=self._validation_message or "",
                font=get_text_style(TextStyles.CAPTION),
                fg=color,
                anchor="w",
            )
        msg_label.pack(fill="x", pady=(5, 0))

    def _get_colors(self, theme: str, state: ValidationState) -> dict[str, str]:
        return input_colors(theme, state)

    def _get_validation_color(self, state: ValidationState) -> str:
        return validation_color(self._theme, state)

    def _check_length(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        if self._max_length and len(self.get()) > self._max_length:
            self.delete(self._max_length, tk.END)

    def set_validation(self, state: ValidationState, message: str | None = None) -> None:
        self._validation_state = state
        self._validation_message = message
        colors = self._get_colors(self._theme, state)
        if CTK_AVAILABLE:
            self.configure(border_color=colors["border"])

    def clear(self) -> None:
        self.delete(0, tk.END)

    def pack(self, **kwargs: Any) -> None:
        self._container.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        self._container.grid(**kwargs)
