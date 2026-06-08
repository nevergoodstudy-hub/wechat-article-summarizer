"""Action card component."""

from __future__ import annotations

import tkinter as tk

from ..styles.colors import ModernColors
from .card_compat import CTK_AVAILABLE, ctk
from .card_content import ContentCard


class ActionCard(ContentCard):
    """操作卡片组件"""

    def __init__(
        self,
        master,
        title: str | None = None,
        action_text: str = "操作",
        action_command=None,
        theme: str = "dark",
        **kwargs,
    ):
        super().__init__(master, title=title, theme=theme, **kwargs)
        self._create_action_button(action_text, action_command)

    def _create_action_button(self, text: str, command) -> None:
        """创建操作按钮"""
        if CTK_AVAILABLE:
            button_frame = ctk.CTkFrame(self, fg_color="transparent")
        else:
            button_frame = tk.Frame(self, bg=self._base_color)

        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        accent_color = (
            ModernColors.DARK_ACCENT if self._theme == "dark" else ModernColors.LIGHT_ACCENT
        )
        hover_color = (
            ModernColors.DARK_ACCENT_HOVER
            if self._theme == "dark"
            else ModernColors.LIGHT_ACCENT_HOVER
        )

        if CTK_AVAILABLE:
            action_btn = ctk.CTkButton(
                button_frame,
                text=text,
                command=command,
                fg_color=accent_color,
                hover_color=hover_color,
                corner_radius=8,
            )
        else:
            action_btn = tk.Button(
                button_frame,
                text=text,
                command=command,
                bg=accent_color,
                fg="white",
                relief="flat",
            )

        action_btn.pack(side="right")


__all__ = ["ActionCard"]
