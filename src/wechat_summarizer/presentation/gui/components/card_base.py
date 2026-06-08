"""Base modern card component."""

from __future__ import annotations

import tkinter as tk

from ..styles.colors import ModernColors
from .card_compat import CTK_AVAILABLE, ctk
from .card_models import CardStyle, CornerRadius, ShadowDepth


class ModernCard(ctk.CTkFrame if CTK_AVAILABLE else tk.Frame):  # type: ignore[misc]
    """现代化卡片组件"""

    def __init__(
        self,
        master,
        width: int = 300,
        height: int = 200,
        corner_radius: CornerRadius = CornerRadius.MEDIUM,
        shadow_depth: ShadowDepth = ShadowDepth.MEDIUM,
        style: CardStyle = CardStyle.ELEVATED,
        theme: str = "dark",
        hover_enabled: bool = True,
        **kwargs,
    ):
        self._theme = theme
        self._style = style
        self._shadow_depth = shadow_depth
        self._hover_enabled = hover_enabled
        self._is_hovered = False

        if theme == "dark":
            bg_color = self._get_dark_bg_color(style)
            border_color = ModernColors.DARK_BORDER
            hover_color = ModernColors.DARK_CARD_HOVER
        else:
            bg_color = self._get_light_bg_color(style)
            border_color = ModernColors.LIGHT_BORDER
            hover_color = ModernColors.LIGHT_CARD_HOVER

        self._base_color = bg_color
        self._hover_color = hover_color
        border_width = 1 if style == CardStyle.OUTLINED else 0

        if CTK_AVAILABLE:
            super().__init__(
                master,
                width=width,
                height=height,
                corner_radius=corner_radius.value,
                fg_color=bg_color,
                border_width=border_width,
                border_color=border_color,
                **kwargs,
            )
        else:
            super().__init__(
                master,
                width=width,
                height=height,
                bg=bg_color,
                highlightthickness=border_width,
                highlightbackground=border_color,
                **kwargs,
            )

        if hover_enabled:
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)

    def _get_dark_bg_color(self, style: CardStyle) -> str:
        """获取暗色主题背景色 (Tkinter兼容)"""
        if style == CardStyle.GLASS:
            return ModernColors.DARK_GLASS_SOLID
        if style == CardStyle.OUTLINED:
            return "transparent"
        return ModernColors.DARK_CARD

    def _get_light_bg_color(self, style: CardStyle) -> str:
        """获取浅色主题背景色 (Tkinter兼容)"""
        if style == CardStyle.GLASS:
            return ModernColors.LIGHT_GLASS_SOLID
        if style == CardStyle.OUTLINED:
            return "transparent"
        return ModernColors.LIGHT_CARD

    def _on_enter(self, _event: tk.Event[tk.Misc]) -> None:
        """鼠标进入 - hover效果"""
        if not self._hover_enabled:
            return

        self._is_hovered = True
        if CTK_AVAILABLE and hasattr(self, "configure"):
            self.configure(fg_color=self._hover_color)

    def _on_leave(self, _event: tk.Event[tk.Misc]) -> None:
        """鼠标离开 - 恢复原状"""
        if not self._hover_enabled:
            return

        self._is_hovered = False
        if CTK_AVAILABLE and hasattr(self, "configure"):
            self.configure(fg_color=self._base_color)

    def update_theme(self, mode: str) -> None:
        """热切换主题"""
        self._theme = mode
        if mode == "dark":
            bg_color = self._get_dark_bg_color(self._style)
            border_color = ModernColors.DARK_BORDER
            self._hover_color = ModernColors.DARK_CARD_HOVER
        else:
            bg_color = self._get_light_bg_color(self._style)
            border_color = ModernColors.LIGHT_BORDER
            self._hover_color = ModernColors.LIGHT_CARD_HOVER

        self._base_color = bg_color
        if CTK_AVAILABLE:
            cfg: dict[str, str] = {"fg_color": bg_color}
            if self._style == CardStyle.OUTLINED:
                cfg["border_color"] = border_color
            self.configure(**cfg)

    def set_shadow_depth(self, depth: ShadowDepth) -> None:
        """设置阴影深度"""
        self._shadow_depth = depth


__all__ = ["ModernCard"]
