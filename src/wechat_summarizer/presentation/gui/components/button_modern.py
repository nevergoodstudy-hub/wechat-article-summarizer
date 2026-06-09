"""Modern button widget implementation."""

from __future__ import annotations

import contextlib
import time
import tkinter as tk
from collections.abc import Callable
from typing import Any

from ..styles.colors import ModernColors
from .button_compat import CTK_AVAILABLE, ButtonBase
from .button_models import (
    ButtonSize,
    ButtonVariant,
    get_button_colors,
    get_button_font,
    get_button_size_config,
)
from .button_ripple import RippleEffect


class ModernButton(ButtonBase):  # type: ignore[misc]
    """现代按钮组件"""

    def __init__(
        self,
        master: Any,
        text: str = "Button",
        command: Callable[[], None] | None = None,
        variant: ButtonVariant = ButtonVariant.PRIMARY,
        size: ButtonSize = ButtonSize.MEDIUM,
        icon: Any | None = None,
        icon_position: str = "left",
        loading: bool = False,
        disabled: bool = False,
        debounce_ms: int = 300,
        theme: str = "dark",
        **kwargs: Any,
    ):
        self._text = text
        self._original_command = command
        self._variant = variant
        self._size = size
        self._icon = icon
        self._icon_position = icon_position
        self._loading = loading
        self._disabled = disabled
        self._debounce_ms = debounce_ms
        self._theme = theme
        self._last_click_time = 0.0
        self._ripple_effect: RippleEffect | None = None
        self._ripple_canvas: tk.Canvas | None = None

        colors = self._get_colors(theme, variant)
        size_config = self._get_size_config(size)
        font = get_button_font(size)

        if CTK_AVAILABLE:
            ctk_kwargs: dict[str, Any] = {
                "master": master,
                "text": text if not loading else "Loading...",
                "command": self._handle_click,
                "fg_color": colors["bg"],
                "hover_color": colors["hover"],
                "text_color": colors["text"],
                "corner_radius": 8,
                "height": size_config["height"],
                "font": font,
                "state": "disabled" if (disabled or loading) else "normal",
            }
            if variant == ButtonVariant.GHOST:
                ctk_kwargs["border_width"] = 2
                ctk_kwargs["border_color"] = colors.get("border", ModernColors.DARK_BORDER)
            else:
                ctk_kwargs["border_width"] = 0

            ctk_kwargs.update(kwargs)
            super().__init__(**ctk_kwargs)
        else:
            super().__init__(
                master,
                text=text if not loading else "Loading...",
                command=self._handle_click,
                bg=colors["bg"],
                fg=colors["text"],
                font=font,
                relief="flat" if variant != ButtonVariant.GHOST else "solid",
                bd=2 if variant == ButtonVariant.GHOST else 0,
                state="disabled" if (disabled or loading) else "normal",
                **kwargs,
            )

        if not CTK_AVAILABLE:
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)

        self.bind("<Button-1>", self._on_click_ripple, add="+")

    def _get_colors(self, theme: str, variant: ButtonVariant) -> dict[str, str]:
        """获取按钮颜色方案"""
        return get_button_colors(theme, variant)

    @staticmethod
    def _get_size_config(size: ButtonSize) -> dict[str, int]:
        """获取尺寸配置"""
        return get_button_size_config(size)

    def _on_click_ripple(self, event: Any) -> None:
        if self._disabled or self._loading:
            return

        if self._ripple_canvas is None:
            self._create_ripple_canvas()

        width = self.winfo_width()
        height = self.winfo_height()
        max_radius = int((width**2 + height**2) ** 0.5)

        if self._ripple_effect:
            self._ripple_effect.trigger(int(event.x), int(event.y), max_radius)

    def _create_ripple_canvas(self) -> None:
        width = self.winfo_width()
        height = self.winfo_height()

        if width <= 1 or height <= 1:
            return

        colors = self._get_colors(self._theme, self._variant)
        bg_color = colors.get("bg", "#1e1e1e")
        if bg_color == "transparent":
            bg_color = ModernColors.DARK_BG if self._theme == "dark" else ModernColors.LIGHT_BG

        ripple_color = "#FFFFFF" if self._theme == "dark" else "#000000"
        self._ripple_canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            highlightthickness=0,
            bg=bg_color,
        )
        self._ripple_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        with contextlib.suppress(Exception):
            self._ripple_canvas.tk.call("lower", str(self._ripple_canvas))

        self._ripple_effect = RippleEffect(self._ripple_canvas, color=ripple_color, duration=400)
        self._ripple_canvas.bind("<Button-1>", self._on_click_ripple)

    def _handle_click(self) -> None:
        if self._disabled or self._loading:
            return

        current_time = time.time() * 1000
        if current_time - self._last_click_time < self._debounce_ms:
            return

        self._last_click_time = current_time

        if self._original_command:
            try:
                self._original_command()
            except Exception as exc:
                print(f"按钮命令执行错误: {exc}")

    def _on_enter(self, _event: Any = None) -> None:
        if not CTK_AVAILABLE and not self._disabled and not self._loading:
            colors = self._get_colors(self._theme, self._variant)
            self.configure(bg=colors["hover"])

    def _on_leave(self, _event: Any = None) -> None:
        if not CTK_AVAILABLE:
            colors = self._get_colors(self._theme, self._variant)
            self.configure(bg=colors["bg"])

    def set_loading(self, loading: bool) -> None:
        """设置加载状态"""
        self._loading = loading
        state = "disabled" if (loading or self._disabled) else "normal"
        self.configure(text="Loading..." if loading else self._text, state=state)

    def set_disabled(self, disabled: bool) -> None:
        """设置禁用状态"""
        self._disabled = disabled
        self.configure(state="disabled" if disabled else "normal")

    def update_theme(self, mode: str) -> None:
        """热切换主题"""
        self._theme = mode
        colors = self._get_colors(mode, self._variant)
        if CTK_AVAILABLE:
            cfg: dict[str, Any] = {
                "fg_color": colors["bg"],
                "hover_color": colors["hover"],
                "text_color": colors["text"],
            }
            if self._variant == ButtonVariant.GHOST:
                cfg["border_color"] = colors.get("border", ModernColors.DARK_BORDER)
            self.configure(**cfg)
        else:
            self.configure(bg=colors["bg"], fg=colors["text"])

        if self._ripple_canvas is not None:
            bg = colors.get("bg", "#1e1e1e")
            if bg == "transparent":
                bg = ModernColors.DARK_BG if mode == "dark" else ModernColors.LIGHT_BG
            self._ripple_canvas.configure(bg=bg)
            ripple_color = "#FFFFFF" if mode == "dark" else "#000000"
            if self._ripple_effect:
                self._ripple_effect._color = ripple_color

    def set_text(self, text: str) -> None:
        """设置按钮文本"""
        self._text = text
        if not self._loading:
            self.configure(text=text)


__all__ = ["ModernButton"]
