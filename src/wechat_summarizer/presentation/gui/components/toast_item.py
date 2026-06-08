"""Single toast notification widget."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..styles.typography import TextStyles, get_text_style
from .toast_models import ToastType, toast_colors_for, toast_icon_for_type
from .toast_runtime import CTK_AVAILABLE, ctk, tk


class Toast:
    """Single toast notification instance."""

    def __init__(
        self,
        master: Any,
        message: str,
        toast_type: ToastType = ToastType.INFO,
        duration: int = 3000,
        on_close: Callable[[], None] | None = None,
        theme: str = "dark",
    ) -> None:
        self._master = master
        self._message = message
        self._toast_type = toast_type
        self._duration = duration
        self._on_close = on_close
        self._theme = theme
        self._timer_id: str | None = None

        colors = toast_colors_for(theme, toast_type)
        if CTK_AVAILABLE and ctk is not None:
            self._frame = ctk.CTkFrame(
                master,
                fg_color=colors["bg"],
                corner_radius=8,
                border_width=1,
                border_color=colors["border"],
            )
        else:
            self._frame = tk.Frame(
                master,
                bg=colors["bg"],
                highlightthickness=1,
                highlightbackground=colors["border"],
            )

        self._create_icon(colors)
        self._create_message(message, colors)
        self._create_close_button(colors)

        if duration > 0:
            self._timer_id = self._frame.after(duration, self.close)

    def _create_icon(self, colors: dict[str, str]) -> None:
        """Create toast icon label."""
        icon_text = self._get_icon_text(self._toast_type)
        if CTK_AVAILABLE and ctk is not None:
            icon_label = ctk.CTkLabel(
                self._frame,
                text=icon_text,
                text_color=colors["icon"],
                font=("Arial", 16),
            )
        else:
            icon_label = tk.Label(
                self._frame,
                text=icon_text,
                fg=colors["icon"],
                bg=colors["bg"],
                font=("Arial", 16),
            )
        icon_label.pack(side="left", padx=(12, 8), pady=12)

    def _create_message(self, message: str, colors: dict[str, str]) -> None:
        """Create toast message label."""
        if CTK_AVAILABLE and ctk is not None:
            message_label = ctk.CTkLabel(
                self._frame,
                text=message,
                text_color=colors["text"],
                font=get_text_style(TextStyles.BODY),
                anchor="w",
                justify="left",
            )
        else:
            message_label = tk.Label(
                self._frame,
                text=message,
                fg=colors["text"],
                bg=colors["bg"],
                font=get_text_style(TextStyles.BODY),
                anchor="w",
                justify="left",
            )
        message_label.pack(side="left", fill="both", expand=True, padx=(0, 12), pady=12)

    def _create_close_button(self, colors: dict[str, str]) -> None:
        """Create close button."""
        if CTK_AVAILABLE and ctk is not None:
            close_btn = ctk.CTkButton(
                self._frame,
                text="×",
                width=24,
                height=24,
                fg_color="transparent",
                hover_color=colors["hover"],
                text_color=colors["text"],
                command=self.close,
            )
        else:
            close_btn = tk.Button(
                self._frame,
                text="×",
                width=2,
                bg=colors["bg"],
                fg=colors["text"],
                relief="flat",
                command=self.close,
            )
        close_btn.pack(side="right", padx=(0, 8), pady=8)

    def _get_colors(self, theme: str, toast_type: ToastType) -> dict[str, str]:
        """Return toast colors for compatibility with the old private method."""
        return toast_colors_for(theme, toast_type)

    @staticmethod
    def _get_icon_text(toast_type: ToastType) -> str:
        """Return compact icon text for compatibility with the old private method."""
        return toast_icon_for_type(toast_type)

    def close(self) -> None:
        """Close and destroy the toast."""
        if self._timer_id:
            self._frame.after_cancel(self._timer_id)
            self._timer_id = None
        self._frame.destroy()
        if self._on_close:
            self._on_close()

    def pack(self, **kwargs: Any) -> None:
        """Pack the toast frame."""
        self._frame.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """Grid the toast frame."""
        self._frame.grid(**kwargs)


__all__ = ["Toast"]
