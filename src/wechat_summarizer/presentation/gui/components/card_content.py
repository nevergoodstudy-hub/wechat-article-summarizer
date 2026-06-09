"""Content card component."""

from __future__ import annotations

import tkinter as tk
from typing import Any

from ..styles.colors import ModernColors
from .card_base import ModernCard
from .card_compat import CTK_AVAILABLE, ctk
from .card_models import CornerRadius, ShadowDepth


class ContentCard(ModernCard):
    """内容卡片组件"""

    def __init__(
        self,
        master,
        title: str | None = None,
        subtitle: str | None = None,
        width: int = 300,
        height: int = 200,
        theme: str = "dark",
        **kwargs,
    ):
        super().__init__(
            master,
            width=width,
            height=height,
            theme=theme,
            corner_radius=CornerRadius.MEDIUM,
            shadow_depth=ShadowDepth.MEDIUM,
            **kwargs,
        )
        self._header_frame: Any | None = None
        self._content_frame: Any | None = None

        if title or subtitle:
            self._create_header(title, subtitle)

    def _create_header(self, title: str | None, subtitle: str | None) -> None:
        """创建头部区域"""
        text_color = ModernColors.DARK_TEXT if self._theme == "dark" else ModernColors.LIGHT_TEXT
        text_secondary = (
            ModernColors.DARK_TEXT_SECONDARY
            if self._theme == "dark"
            else ModernColors.LIGHT_TEXT_SECONDARY
        )

        if CTK_AVAILABLE:
            self._header_frame = ctk.CTkFrame(self, fg_color="transparent")
        else:
            self._header_frame = tk.Frame(self, bg=self._base_color)
        assert self._header_frame is not None

        self._header_frame.pack(fill="x", padx=20, pady=(20, 10))

        if title:
            if CTK_AVAILABLE:
                title_label = ctk.CTkLabel(
                    self._header_frame,
                    text=title,
                    font=("Inter", 20, "bold"),
                    text_color=text_color,
                    anchor="w",
                )
            else:
                title_label = tk.Label(
                    self._header_frame,
                    text=title,
                    font=("Arial", 20, "bold"),
                    fg=text_color,
                    bg=self._base_color,
                    anchor="w",
                )
            title_label.pack(fill="x")

        if subtitle:
            if CTK_AVAILABLE:
                subtitle_label = ctk.CTkLabel(
                    self._header_frame,
                    text=subtitle,
                    font=("Inter", 14),
                    text_color=text_secondary,
                    anchor="w",
                )
            else:
                subtitle_label = tk.Label(
                    self._header_frame,
                    text=subtitle,
                    font=("Arial", 14),
                    fg=text_secondary,
                    bg=self._base_color,
                    anchor="w",
                )
            subtitle_label.pack(fill="x", pady=(5, 0))

    def add_content(self, widget) -> None:
        """添加内容组件"""
        if self._content_frame is None:
            if CTK_AVAILABLE:
                self._content_frame = ctk.CTkFrame(self, fg_color="transparent")
            else:
                self._content_frame = tk.Frame(self, bg=self._base_color)

            self._content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        widget.pack(in_=self._content_frame, fill="both", expand=True)


__all__ = ["ContentCard"]
