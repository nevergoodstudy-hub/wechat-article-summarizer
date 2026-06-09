"""Confirmation modal component."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from ..styles.colors import ModernColors
from ..styles.typography import TextStyles, get_text_style
from .modal_base import Modal
from .modal_compat import CTK_AVAILABLE, ctk
from .modal_models import ModalSize


class ConfirmModal(Modal):
    """确认对话框"""

    def __init__(
        self,
        master,
        title: str = "确认",
        message: str = "确定要执行此操作吗？",
        confirm_text: str = "确定",
        cancel_text: str = "取消",
        on_confirm: Callable | None = None,
        on_cancel: Callable | None = None,
        theme: str = "dark",
        **kwargs,
    ):
        self._message = message
        self._confirm_text = confirm_text
        self._cancel_text = cancel_text
        self._on_confirm = on_confirm
        self._on_cancel_callback = on_cancel

        super().__init__(
            master,
            title=title,
            size=ModalSize.SMALL,
            theme=theme,
            on_close=on_cancel,
            **kwargs,
        )
        self._setup_content()

    def _setup_content(self) -> None:
        content = self.get_content_frame()

        if CTK_AVAILABLE and ctk is not None:
            msg_label = ctk.CTkLabel(
                content,
                text=self._message,
                font=get_text_style(TextStyles.BODY),
                text_color=self._colors["text"],
                wraplength=350,
            )
        else:
            msg_label = tk.Label(
                content,
                text=self._message,
                font=get_text_style(TextStyles.BODY),
                fg=self._colors["text"],
                bg=self._colors["bg"],
                wraplength=350,
            )

        msg_label.pack(expand=True)
        footer = self.get_footer_frame()
        self._create_cancel_button(footer)
        self._create_confirm_button(footer)

    def _create_cancel_button(self, footer) -> None:
        if CTK_AVAILABLE and ctk is not None:
            cancel_btn = ctk.CTkButton(
                footer,
                text=self._cancel_text,
                fg_color="transparent",
                hover_color=self._colors["border"],
                text_color=self._colors["text"],
                border_width=1,
                border_color=self._colors["border"],
                corner_radius=8,
                command=self._handle_cancel,
            )
        else:
            cancel_btn = tk.Button(
                footer,
                text=self._cancel_text,
                bg=self._colors["bg"],
                fg=self._colors["text"],
                relief="solid",
                bd=1,
                command=self._handle_cancel,
            )

        cancel_btn.pack(side="right", padx=(10, 0))

    def _create_confirm_button(self, footer) -> None:
        accent = ModernColors.DARK_ACCENT if self._theme == "dark" else ModernColors.LIGHT_ACCENT
        hover = (
            ModernColors.DARK_ACCENT_HOVER
            if self._theme == "dark"
            else ModernColors.LIGHT_ACCENT_HOVER
        )

        if CTK_AVAILABLE and ctk is not None:
            confirm_btn = ctk.CTkButton(
                footer,
                text=self._confirm_text,
                fg_color=accent,
                hover_color=hover,
                text_color="#FFFFFF",
                corner_radius=8,
                command=self._handle_confirm,
            )
        else:
            confirm_btn = tk.Button(
                footer,
                text=self._confirm_text,
                bg=accent,
                fg="#FFFFFF",
                relief="flat",
                command=self._handle_confirm,
            )

        confirm_btn.pack(side="right")

    def _handle_confirm(self) -> None:
        self.close()
        if self._on_confirm:
            self._on_confirm()

    def _handle_cancel(self) -> None:
        self.close()
        if self._on_cancel_callback:
            self._on_cancel_callback()


__all__ = ["ConfirmModal"]
