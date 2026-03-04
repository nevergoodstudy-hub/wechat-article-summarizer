"""Toast通知弹窗

带动画效果的通知弹窗组件。
"""

from __future__ import annotations

import contextlib

import customtkinter as ctk

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing
from .animation_helper import AnimationHelper


class ToastNotification:
    """Toast通知弹窗 - 带动画效果"""

    def __init__(
        self,
        parent,
        title: str,
        message: str,
        toast_type: str = "info",
        duration_ms: int = 3000,
        show_buttons: bool = False,
        on_confirm=None,
        on_cancel=None,
    ):
        """\n        Args:\n            parent: 父窗口\n            title: 通知标题\n            message: 通知消息\n            toast_type: 类型 ("info", "success", "warning", "error")\n            duration_ms: 显示时长（毫秒），0表示不自动关闭\n            show_buttons: 是否显示按钮\n            on_confirm: 确认回调\n            on_cancel: 取消回调\n"""
        self.parent = parent
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self._closed = False
        colors = {
            "info": (ModernColors.INFO, "#e0f2fe", "ℹ️"),
            "success": (ModernColors.SUCCESS, "#d1fae5", "✅"),
            "warning": (ModernColors.WARNING, "#fef3c7", "⚠️"),
            "error": (ModernColors.ERROR, "#fee2e2", "❌"),
        }
        accent_color, bg_color, icon = colors.get(toast_type, colors["info"])
        self.window = ctk.CTkToplevel(parent)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.container = ctk.CTkFrame(
            self.window,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(bg_color, ModernColors.DARK_CARD),
            border_width=2,
            border_color=accent_color,
        )
        self.container.pack(fill="both", expand=True, padx=2, pady=2)
        content = ctk.CTkFrame(self.container, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=15)
        title_frame = ctk.CTkFrame(content, fg_color="transparent")
        title_frame.pack(fill="x")
        ctk.CTkLabel(
            title_frame,
            text=f"{icon} {title}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=accent_color,
        ).pack(side="left")
        close_btn = ctk.CTkButton(
            title_frame,
            text="✕",
            width=25,
            height=25,
            corner_radius=Spacing.RADIUS_LG,
            fg_color="transparent",
            hover_color=(ModernColors.LIGHT_HOVER_SUBTLE, ModernColors.DARK_HOVER_SUBTLE),
            text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
            command=self._close,
        )
        close_btn.pack(side="right")
        ctk.CTkLabel(
            content,
            text=message,
            font=ctk.CTkFont(size=13),
            wraplength=350,
            justify="left",
            anchor="w",
            text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
        ).pack(fill="x", pady=(10, 0))
        if show_buttons:
            btn_frame = ctk.CTkFrame(content, fg_color="transparent")
            btn_frame.pack(fill="x", pady=(15, 0))
            ctk.CTkButton(
                btn_frame,
                text="取消",
                width=80,
                height=32,
                corner_radius=Spacing.RADIUS_MD,
                fg_color=ModernColors.NEUTRAL_BTN_DISABLED,
                command=self._on_cancel_click,
            ).pack(side="right", padx=(5, 0))
            ctk.CTkButton(
                btn_frame,
                text="确认填入",
                width=100,
                height=32,
                corner_radius=Spacing.RADIUS_MD,
                fg_color=accent_color,
                command=self._on_confirm_click,
            ).pack(side="right")
        self.window.update_idletasks()
        width = max(400, self.container.winfo_reqwidth() + 4)
        height = self.container.winfo_reqheight() + 4
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + (parent_w - width) // 2
        y = parent_y + (parent_h - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.attributes("-alpha", 0)
        self.window.deiconify()
        self._fade_in()
        if duration_ms > 0 and (not show_buttons):
            self.window.after(duration_ms, self._fade_out)

    def _fade_in(self):
        """淡入动画"""

        def update_alpha(val):
            if not self._closed:
                try:
                    self.window.attributes("-alpha", val)
                except Exception:
                    return None

        AnimationHelper.animate_value(
            self.parent, 0, 1, 200, update_alpha, easing=AnimationHelper.ease_out_cubic
        )

    def _fade_out(self):
        """淡出动画并关闭"""
        if self._closed:
            return None

        def update_alpha(val):
            if not self._closed:
                with contextlib.suppress(Exception):
                    self.window.attributes("-alpha", val)

        def on_complete():
            self._close()

        AnimationHelper.animate_value(
            self.parent,
            1,
            0,
            150,
            update_alpha,
            easing=AnimationHelper.ease_out_cubic,
            on_complete=on_complete,
        )

    def _close(self):
        """关闭窗口"""
        if self._closed:
            return None
        self._closed = True
        try:
            if self.window.winfo_exists():
                self.window.withdraw()
                self.window.after(10, self._destroy_window)
        except Exception:
            pass

    def _destroy_window(self):
        """实际销毁窗口"""
        try:
            if self.window.winfo_exists():
                self.window.destroy()
        except Exception:
            pass

    def _on_confirm_click(self):
        """确认按钮点击"""
        if self.on_confirm:
            self.on_confirm()
        self._close()

    def _on_cancel_click(self):
        """取消按钮点击"""
        if self.on_cancel:
            self.on_cancel()
        self._close()
