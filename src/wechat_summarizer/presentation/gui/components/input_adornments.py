"""Decorative controls for modern input widgets."""

from __future__ import annotations

import contextlib
import tkinter as tk
from collections.abc import Callable
from typing import Any

from ..styles.typography import TextStyles, get_text_style
from .input_compat import CTK_AVAILABLE, ctk


class FloatingLabel:
    """Floating label animation for focused or populated inputs."""

    def __init__(
        self,
        container: Any,
        text: str,
        normal_color: str,
        active_color: str,
        normal_y: int = 12,
        active_y: int = -8,
        animation_duration: int = 200,
    ):
        self._container = container
        self._normal_color = normal_color
        self._active_color = active_color
        self._normal_y = normal_y
        self._active_y = active_y
        self._duration = max(50, min(animation_duration, 500))
        self._is_active = False
        self._animation_id: str | None = None
        self._current_y = float(normal_y)

        if CTK_AVAILABLE and ctk is not None:
            self._label: Any = ctk.CTkLabel(
                container,
                text=text,
                font=get_text_style(TextStyles.BODY),
                text_color=normal_color,
                fg_color="transparent",
            )
        else:
            self._label = tk.Label(
                container, text=text, font=get_text_style(TextStyles.BODY), fg=normal_color
            )

        self._label.place(x=10, y=self._normal_y)

    def activate(self, has_content: bool = False) -> None:
        if self._is_active and not has_content:
            return
        self._is_active = True
        self._animate_to(self._active_y, self._active_color, 0.85)

    def deactivate(self, has_content: bool = False) -> None:
        if has_content:
            return
        self._is_active = False
        self._animate_to(self._normal_y, self._normal_color, 1.0)

    def _animate_to(self, target_y: int, target_color: str, target_scale: float) -> None:
        if self._animation_id:
            with contextlib.suppress(Exception):
                self._container.after_cancel(self._animation_id)

        steps = max(1, self._duration // 16)
        start_y = self._current_y
        delta_y = target_y - start_y
        current_step = [0]

        def animate_step() -> None:
            if current_step[0] >= steps:
                self._current_y = float(target_y)
                self._label.place(x=10, y=target_y)
                if CTK_AVAILABLE:
                    self._label.configure(text_color=target_color)
                    if target_scale < 1.0:
                        self._label.configure(font=get_text_style(TextStyles.LABEL_SMALL))
                    else:
                        self._label.configure(font=get_text_style(TextStyles.BODY))
                else:
                    self._label.configure(fg=target_color)
                return

            progress = current_step[0] / steps
            eased = 1 - (1 - progress) ** 2
            new_y = start_y + delta_y * eased
            self._current_y = new_y
            self._label.place(x=10, y=int(new_y))
            current_step[0] += 1
            self._animation_id = self._container.after(16, animate_step)

        animate_step()

    def destroy(self) -> None:
        if self._animation_id:
            with contextlib.suppress(Exception):
                self._container.after_cancel(self._animation_id)
        self._label.destroy()


class ClearButton:
    """Clear button displayed inside an input field."""

    def __init__(
        self,
        container: Any,
        on_clear: Callable[[], None] | None,
        color: str = "#737373",
        hover_color: str = "#a3a3a3",
        size: int = 16,
    ):
        self._on_clear = on_clear
        self._size = max(12, min(size, 24))
        self._visible = False

        if CTK_AVAILABLE and ctk is not None:
            self._button: Any = ctk.CTkButton(
                container,
                text="×",
                width=self._size + 8,
                height=self._size + 8,
                fg_color="transparent",
                hover_color=hover_color,
                text_color=color,
                corner_radius=self._size // 2,
                font=("Arial", self._size),
                command=self._handle_clear,
            )
        else:
            self._button = tk.Button(
                container,
                text="×",
                width=2,
                bg=container.cget("bg"),
                fg=color,
                relief="flat",
                font=("Arial", self._size),
                command=self._handle_clear,
                cursor="hand2",
            )
            self._button.bind("<Enter>", lambda _event: self._button.configure(fg=hover_color))
            self._button.bind("<Leave>", lambda _event: self._button.configure(fg=color))

    def _handle_clear(self) -> None:
        if self._on_clear:
            with contextlib.suppress(Exception):
                self._on_clear()

    def show(self) -> None:
        if not self._visible:
            self._visible = True
            self._button.place(relx=1.0, rely=0.5, anchor="e", x=-5)

    def hide(self) -> None:
        if self._visible:
            self._visible = False
            self._button.place_forget()

    def destroy(self) -> None:
        self._button.destroy()
