"""Base modal component."""

from __future__ import annotations

import contextlib
import tkinter as tk
from collections.abc import Callable

from ..styles.colors import ModernColors
from ..styles.typography import TextStyles, get_text_style
from .modal_compat import CTK_AVAILABLE, ctk
from .modal_models import ModalSize


class Modal:
    """现代模态框组件"""

    _modal_stack: list[Modal] = []

    def __init__(
        self,
        master,
        title: str = "标题",
        size: ModalSize = ModalSize.MEDIUM,
        closable: bool = True,
        on_close: Callable | None = None,
        theme: str = "dark",
        **kwargs,
    ):
        self._master = master
        self._title = title
        self._size = size
        self._closable = closable
        self._on_close = on_close
        self._theme = theme
        self._is_open = False
        self._colors = self._get_colors(theme)

        self._create_overlay()
        self._create_modal()

        if closable:
            self._master.bind("<Escape>", self._on_escape, add="+")

    def _get_colors(self, theme: str) -> dict:
        if theme == "dark":
            return {
                "overlay": "rgba(0,0,0,0.5)",
                "bg": ModernColors.DARK_SURFACE,
                "text": ModernColors.DARK_TEXT,
                "text_secondary": ModernColors.DARK_TEXT_SECONDARY,
                "border": ModernColors.DARK_BORDER,
                "header_bg": ModernColors.DARK_CARD,
            }
        return {
            "overlay": "rgba(0,0,0,0.3)",
            "bg": ModernColors.LIGHT_SURFACE,
            "text": ModernColors.LIGHT_TEXT,
            "text_secondary": ModernColors.LIGHT_TEXT_SECONDARY,
            "border": ModernColors.LIGHT_BORDER,
            "header_bg": ModernColors.LIGHT_CARD,
        }

    def _create_overlay(self) -> None:
        overlay_color = "#000000" if self._theme == "dark" else "#666666"

        if CTK_AVAILABLE and ctk is not None:
            self._overlay = ctk.CTkFrame(self._master, fg_color=overlay_color)
        else:
            self._overlay = tk.Frame(self._master, bg=overlay_color)

        if self._closable:
            self._overlay.bind("<Button-1>", lambda _event: self.close())

    def _create_modal(self) -> None:
        if self._size == ModalSize.FULLSCREEN:
            width = self._master.winfo_width() - 40
            height = self._master.winfo_height() - 40
        else:
            width, height = self._size.value

        if CTK_AVAILABLE and ctk is not None:
            self._modal_frame = ctk.CTkFrame(
                self._overlay,
                width=width,
                height=height,
                fg_color=self._colors["bg"],
                border_width=1,
                border_color=self._colors["border"],
                corner_radius=12,
            )
        else:
            self._modal_frame = tk.Frame(
                self._overlay,
                width=width,
                height=height,
                bg=self._colors["bg"],
                highlightthickness=1,
                highlightbackground=self._colors["border"],
            )

        self._modal_frame.bind("<Button-1>", lambda _event: "break")
        self._create_header()
        self._create_content_area()
        self._create_footer()

    def _create_header(self) -> None:
        if CTK_AVAILABLE and ctk is not None:
            header = ctk.CTkFrame(
                self._modal_frame,
                fg_color=self._colors["header_bg"],
                height=50,
                corner_radius=0,
            )
        else:
            header = tk.Frame(self._modal_frame, bg=self._colors["header_bg"], height=50)

        header.pack(fill="x", padx=1, pady=(1, 0))
        header.pack_propagate(False)

        if CTK_AVAILABLE and ctk is not None:
            title_label = ctk.CTkLabel(
                header,
                text=self._title,
                font=get_text_style(TextStyles.HEADING_4),
                text_color=self._colors["text"],
            )
        else:
            title_label = tk.Label(
                header,
                text=self._title,
                font=get_text_style(TextStyles.HEADING_4),
                fg=self._colors["text"],
                bg=self._colors["header_bg"],
            )

        title_label.pack(side="left", padx=20, pady=10)

        if self._closable:
            self._create_close_button(header)

    def _create_close_button(self, header) -> None:
        if CTK_AVAILABLE and ctk is not None:
            close_btn = ctk.CTkButton(
                header,
                text="×",
                width=30,
                height=30,
                fg_color="transparent",
                hover_color=ModernColors.ERROR,
                text_color=self._colors["text"],
                corner_radius=15,
                command=self.close,
            )
        else:
            close_btn = tk.Button(
                header,
                text="×",
                width=3,
                bg=self._colors["header_bg"],
                fg=self._colors["text"],
                relief="flat",
                command=self.close,
            )

        close_btn.pack(side="right", padx=10, pady=10)

    def _create_content_area(self) -> None:
        if CTK_AVAILABLE and ctk is not None:
            self._content = ctk.CTkFrame(self._modal_frame, fg_color="transparent")
        else:
            self._content = tk.Frame(self._modal_frame, bg=self._colors["bg"])

        self._content.pack(fill="both", expand=True, padx=20, pady=20)

    def _create_footer(self) -> None:
        if CTK_AVAILABLE and ctk is not None:
            self._footer = ctk.CTkFrame(self._modal_frame, fg_color="transparent", height=60)
        else:
            self._footer = tk.Frame(self._modal_frame, bg=self._colors["bg"], height=60)

        self._footer.pack(fill="x", padx=20, pady=(0, 20))

    def _on_escape(self, event) -> None:
        if (
            self._is_open
            and self._closable
            and Modal._modal_stack
            and Modal._modal_stack[-1] == self
        ):
            self.close()

    def open(self) -> None:
        """打开模态框"""
        if self._is_open:
            return

        self._is_open = True
        Modal._modal_stack.append(self)
        self._overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._modal_frame.place(relx=0.5, rely=0.5, anchor="center")
        self._overlay.lift()
        self._modal_frame.lift()

    def close(self) -> None:
        """关闭模态框"""
        if not self._is_open:
            return

        self._is_open = False

        if self in Modal._modal_stack:
            Modal._modal_stack.remove(self)

        self._modal_frame.place_forget()
        self._overlay.place_forget()

        if self._on_close:
            self._on_close()

    def destroy(self) -> None:
        """销毁模态框"""
        self.close()

        with contextlib.suppress(Exception):
            self._master.unbind("<Escape>")

        self._modal_frame.destroy()
        self._overlay.destroy()

    def get_content_frame(self):
        """获取内容区域Frame"""
        return self._content

    def get_footer_frame(self):
        """获取底部区域Frame"""
        return self._footer

    def set_title(self, title: str) -> None:
        """设置标题"""
        self._title = title


__all__ = ["Modal"]
