"""Alert modal component."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from ..styles.colors import ModernColors
from ..styles.typography import TextStyles, get_text_style
from .modal_base import Modal
from .modal_compat import CTK_AVAILABLE, ctk
from .modal_models import ModalSize


class AlertModal(Modal):
    """警告/提示对话框"""

    def __init__(
        self,
        master,
        title: str = "提示",
        message: str = "",
        button_text: str = "知道了",
        alert_type: str = "info",
        on_close: Callable | None = None,
        theme: str = "dark",
        **kwargs,
    ):
        self._message = message
        self._button_text = button_text
        self._alert_type = alert_type

        super().__init__(
            master,
            title=title,
            size=ModalSize.SMALL,
            theme=theme,
            on_close=on_close,
            **kwargs,
        )
        self._setup_content()

    def _get_type_color(self) -> str:
        colors = {
            "info": ModernColors.INFO,
            "success": ModernColors.SUCCESS,
            "warning": ModernColors.WARNING,
            "error": ModernColors.ERROR,
        }
        return colors.get(self._alert_type, ModernColors.INFO)

    def _setup_content(self) -> None:
        content = self.get_content_frame()
        icon = self._get_icon_text()

        if CTK_AVAILABLE and ctk is not None:
            icon_label = ctk.CTkLabel(
                content,
                text=icon,
                font=("Arial", 32),
                text_color=self._get_type_color(),
            )
        else:
            icon_label = tk.Label(
                content,
                text=icon,
                font=("Arial", 32),
                fg=self._get_type_color(),
                bg=self._colors["bg"],
            )

        icon_label.pack(pady=(0, 10))
        self._create_message(content)
        self._create_ok_button(self.get_footer_frame())

    def _get_icon_text(self) -> str:
        icon_map = {
            "info": "ℹ",
            "success": "✓",
            "warning": "⚠",
            "error": "✕",
        }
        return icon_map.get(self._alert_type, "ℹ")

    def _create_message(self, content) -> None:
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

        msg_label.pack()

    def _create_ok_button(self, footer) -> None:
        if CTK_AVAILABLE and ctk is not None:
            ok_btn = ctk.CTkButton(
                footer,
                text=self._button_text,
                fg_color=self._get_type_color(),
                hover_color=self._get_type_color(),
                text_color="#FFFFFF",
                corner_radius=8,
                command=self.close,
            )
        else:
            ok_btn = tk.Button(
                footer,
                text=self._button_text,
                bg=self._get_type_color(),
                fg="#FFFFFF",
                relief="flat",
                command=self.close,
            )

        ok_btn.pack(side="right")


__all__ = ["AlertModal"]
