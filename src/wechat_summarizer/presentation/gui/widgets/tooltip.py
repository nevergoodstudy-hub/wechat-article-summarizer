"""Tooltip 工具提示组件

从 WechatSummarizerGUI 提取的通用工具提示创建函数。
支持鼠标悬停显示、自动定位、自动隐藏。
"""

from __future__ import annotations

from collections.abc import Callable

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False


def create_tooltip(widget, text: str, get_font: Callable) -> None:
    """创建简单的工具提示

    Args:
        widget: 要添加提示的控件
        text: 提示文本
        get_font: 字体工厂函数 get_font(size, weight='normal') -> CTkFont
    """
    tooltip = None

    def show_tooltip(event):
        nonlocal tooltip
        if tooltip:
            return
        x = widget.winfo_rootx() + widget.winfo_width() + 5
        y = widget.winfo_rooty()

        tooltip = ctk.CTkToplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
        tooltip.attributes("-topmost", True)

        label = ctk.CTkLabel(
            tooltip,
            text=text,
            font=get_font(10),
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            corner_radius=Spacing.RADIUS_SM,
            padx=8,
            pady=4,
        )
        label.pack()

    def hide_tooltip(event):
        nonlocal tooltip
        if tooltip:
            tooltip.destroy()
            tooltip = None

    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)
