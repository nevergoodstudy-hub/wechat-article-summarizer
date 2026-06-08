"""Statistic card component."""

from __future__ import annotations

import tkinter as tk

from ..styles.colors import ModernColors
from .card_base import ModernCard
from .card_compat import CTK_AVAILABLE, ctk
from .card_models import CornerRadius


class StatCard(ModernCard):
    """统计卡片组件"""

    def __init__(
        self,
        master,
        label: str,
        value: str,
        change: str | None = None,
        theme: str = "dark",
        **kwargs,
    ):
        super().__init__(
            master,
            width=200,
            height=120,
            theme=theme,
            corner_radius=CornerRadius.MEDIUM,
            **kwargs,
        )

        text_color = ModernColors.DARK_TEXT if theme == "dark" else ModernColors.LIGHT_TEXT
        text_secondary = (
            ModernColors.DARK_TEXT_SECONDARY
            if theme == "dark"
            else ModernColors.LIGHT_TEXT_SECONDARY
        )

        if CTK_AVAILABLE:
            label_widget = ctk.CTkLabel(
                self,
                text=label,
                font=("Inter", 14),
                text_color=text_secondary,
            )
        else:
            label_widget = tk.Label(
                self,
                text=label,
                font=("Arial", 14),
                fg=text_secondary,
                bg=self._base_color,
            )
        label_widget.pack(pady=(20, 5))

        if CTK_AVAILABLE:
            value_widget = ctk.CTkLabel(
                self,
                text=value,
                font=("Inter", 32, "bold"),
                text_color=text_color,
            )
        else:
            value_widget = tk.Label(
                self,
                text=value,
                font=("Arial", 32, "bold"),
                fg=text_color,
                bg=self._base_color,
            )
        value_widget.pack()

        if change:
            change_color = ModernColors.SUCCESS if change.startswith("+") else ModernColors.ERROR

            if CTK_AVAILABLE:
                change_widget = ctk.CTkLabel(
                    self,
                    text=change,
                    font=("Inter", 12),
                    text_color=change_color,
                )
            else:
                change_widget = tk.Label(
                    self,
                    text=change,
                    font=("Arial", 12),
                    fg=change_color,
                    bg=self._base_color,
                )
            change_widget.pack(pady=(5, 20))


__all__ = ["StatCard"]
