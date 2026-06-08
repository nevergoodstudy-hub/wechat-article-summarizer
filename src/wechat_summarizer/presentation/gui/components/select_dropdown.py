"""Dropdown rendering, search, and open/close behavior for ModernSelect."""

from __future__ import annotations

import re
import tkinter as tk
from typing import Any

from ..utils.i18n import tr
from .select_compat import CTK_AVAILABLE, ctk
from .select_models import SelectOption


class SelectDropdownMixin:
    """Dropdown panel and option-list behavior."""

    def _create_dropdown(self: Any) -> None:
        """创建下拉面板"""
        if CTK_AVAILABLE and ctk is not None:
            self._dropdown = ctk.CTkFrame(
                self._container,
                fg_color=self._colors["dropdown_bg"],
                border_width=1,
                border_color=self._colors["border"],
                corner_radius=8,
            )
        else:
            self._dropdown = tk.Frame(
                self._container,
                bg=self._colors["dropdown_bg"],
                highlightthickness=1,
                highlightbackground=self._colors["border"],
            )

        if self._searchable:
            self._create_search_input()

        self._create_options_list()

    def _create_search_input(self: Any) -> None:
        """创建搜索输入框"""
        if CTK_AVAILABLE and ctk is not None:
            self._search_entry = ctk.CTkEntry(
                self._dropdown,
                placeholder_text=tr("搜索..."),
                fg_color=self._colors["bg"],
                text_color=self._colors["text"],
                border_width=1,
                border_color=self._colors["border"],
                corner_radius=6,
                height=32,
            )
        else:
            self._search_entry = tk.Entry(
                self._dropdown,
                bg=self._colors["bg"],
                fg=self._colors["text"],
                relief="solid",
                bd=1,
            )

        self._search_entry.pack(fill="x", padx=8, pady=8)
        self._search_entry.bind("<KeyRelease>", self._on_search)

    def _create_options_list(self: Any) -> None:
        """创建选项列表"""
        height = min(len(self._options), self.MAX_VISIBLE_OPTIONS) * 36

        if CTK_AVAILABLE and ctk is not None:
            self._options_frame = ctk.CTkScrollableFrame(
                self._dropdown,
                fg_color="transparent",
                height=height,
            )
        else:
            canvas = tk.Canvas(
                self._dropdown,
                bg=self._colors["dropdown_bg"],
                highlightthickness=0,
                height=height,
            )
            scrollbar = tk.Scrollbar(self._dropdown, command=canvas.yview)
            self._options_frame = tk.Frame(canvas, bg=self._colors["dropdown_bg"])

            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            canvas.create_window((0, 0), window=self._options_frame, anchor="nw")

        self._options_frame.pack(fill="both", expand=True, padx=4, pady=(0, 8))
        self._render_options()

    def _render_options(self: Any) -> None:
        """渲染选项列表"""
        for widget in self._options_frame.winfo_children():
            widget.destroy()

        for option in self._filtered_options:
            self._create_option_item(option)

    def _create_option_item(self: Any, option: SelectOption) -> None:
        """创建单个选项"""
        is_selected = option.value in self._selected_values

        def on_option_click() -> None:
            self._on_option_click(option)

        if CTK_AVAILABLE and ctk is not None:
            item = ctk.CTkButton(
                self._options_frame,
                text=option.label,
                fg_color=self._colors["accent"] if is_selected else "transparent",
                hover_color=self._colors["bg_hover"],
                text_color=self._colors["text"],
                anchor="w",
                height=32,
                corner_radius=4,
                command=on_option_click,
                state="disabled" if option.disabled else "normal",
            )
        else:
            item = tk.Button(
                self._options_frame,
                text=option.label,
                bg=self._colors["accent"] if is_selected else self._colors["dropdown_bg"],
                fg=self._colors["text"],
                anchor="w",
                relief="flat",
                command=on_option_click,
                state="disabled" if option.disabled else "normal",
            )

        item.pack(fill="x", padx=4, pady=2)

    def _toggle_dropdown(self: Any) -> None:
        """切换下拉面板显示"""
        if self._is_open:
            self._close_dropdown()
        else:
            self._open_dropdown()

    def _open_dropdown(self: Any) -> None:
        """打开下拉面板"""
        self._is_open = True
        self._dropdown.pack(fill="x", pady=(4, 0))

        if self._searchable and hasattr(self, "_search_entry"):
            self._search_entry.focus_set()

    def _close_dropdown(self: Any) -> None:
        """关闭下拉面板"""
        self._is_open = False
        self._dropdown.pack_forget()

        if self._searchable and hasattr(self, "_search_entry"):
            self._search_entry.delete(0, tk.END)
            self._filtered_options = self._options.copy()
            self._render_options()

    def _on_global_click(self: Any, event: Any) -> None:
        """全局点击事件处理"""
        if self._is_open and not self._is_child_of(event.widget, self._container):
            self._close_dropdown()

    def _is_child_of(self: Any, widget: Any, parent: Any) -> bool:
        """检查 widget 是否是 parent 的子组件"""
        try:
            while widget:
                if widget == parent:
                    return True
                widget = widget.master
        except Exception:
            pass
        return False

    def _on_search(self: Any, _event: Any) -> None:
        """搜索事件处理"""
        query = self._search_entry.get().strip().lower()
        query = re.sub(r'[<>"\']', "", query)

        if not query:
            self._filtered_options = self._options.copy()
        else:
            self._filtered_options = [opt for opt in self._options if query in opt.label.lower()]

        self._render_options()


__all__ = ["SelectDropdownMixin"]
