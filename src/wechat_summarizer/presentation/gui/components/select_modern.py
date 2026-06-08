"""Modern select widget."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from typing import Any

from ..styles.typography import TextStyles, get_text_style
from .select_compat import CTK_AVAILABLE, create_select_container, ctk
from .select_dropdown import SelectDropdownMixin
from .select_models import SelectMode, SelectOption, select_theme_colors


class ModernSelect(SelectDropdownMixin):
    """现代下拉选择器组件"""

    MAX_VISIBLE_OPTIONS = 8
    MAX_OPTIONS = 10000

    def __init__(
        self,
        master: Any,
        options: list[SelectOption] | None = None,
        mode: SelectMode = SelectMode.SINGLE,
        placeholder: str = "请选择...",
        searchable: bool = True,
        label: str | None = None,
        on_change: Callable[[Any], None] | None = None,
        theme: str = "dark",
        width: int = 300,
        **_kwargs: Any,
    ):
        self._master = master
        self._options = options[: self.MAX_OPTIONS] if options else []
        self._filtered_options = self._options.copy()
        self._mode = mode
        self._placeholder = placeholder
        self._searchable = searchable
        self._label = label
        self._on_change = on_change
        self._theme = theme
        self._width = width
        self._is_open = False
        self._selected_values: list[Any] = []
        self._colors = self._get_colors(theme)
        self._container = create_select_container(master)

        self._create_label()
        self._create_select_button()
        self._create_dropdown()
        master.bind("<Button-1>", self._on_global_click, add="+")

    def _get_colors(self, theme: str) -> dict[str, str]:
        """获取颜色配置"""
        return select_theme_colors(theme)

    def _create_label(self) -> None:
        """创建标签"""
        if not self._label:
            return

        if CTK_AVAILABLE and ctk is not None:
            label = ctk.CTkLabel(
                self._container,
                text=self._label,
                font=get_text_style(TextStyles.LABEL_SMALL),
                text_color=self._colors["text_secondary"],
                anchor="w",
            )
        else:
            label = tk.Label(
                self._container,
                text=self._label,
                font=get_text_style(TextStyles.LABEL_SMALL),
                fg=self._colors["text_secondary"],
                anchor="w",
            )

        label.pack(fill="x", pady=(0, 5))

    def _create_select_button(self) -> None:
        """创建选择按钮"""
        if CTK_AVAILABLE and ctk is not None:
            self._select_btn = ctk.CTkButton(
                self._container,
                text=self._placeholder,
                width=self._width,
                height=40,
                fg_color=self._colors["bg"],
                hover_color=self._colors["bg_hover"],
                text_color=self._colors["text_secondary"],
                border_width=1,
                border_color=self._colors["border"],
                corner_radius=8,
                anchor="w",
                command=self._toggle_dropdown,
            )
        else:
            self._select_btn = tk.Button(
                self._container,
                text=self._placeholder,
                width=self._width // 8,
                bg=self._colors["bg"],
                fg=self._colors["text_secondary"],
                relief="solid",
                bd=1,
                anchor="w",
                command=self._toggle_dropdown,
            )

        self._select_btn.pack(fill="x")

    def _on_option_click(self, option: SelectOption) -> None:
        """选项点击事件"""
        if option.disabled:
            return

        if self._mode == SelectMode.SINGLE:
            self._selected_values = [option.value]
            self._update_display()
            self._close_dropdown()
        else:
            if option.value in self._selected_values:
                self._selected_values.remove(option.value)
            else:
                self._selected_values.append(option.value)
            self._update_display()
            self._render_options()

        if self._on_change:
            self._on_change(self.get_value())

    def _update_display(self) -> None:
        """更新显示文本"""
        if not self._selected_values:
            display_text = self._placeholder
            text_color = self._colors["text_secondary"]
        elif self._mode == SelectMode.SINGLE:
            selected_opt = next(
                (option for option in self._options if option.value == self._selected_values[0]),
                None,
            )
            display_text = selected_opt.label if selected_opt else self._placeholder
            text_color = self._colors["text"]
        else:
            display_text = f"已选择 {len(self._selected_values)} 项"
            text_color = self._colors["text"]

        if CTK_AVAILABLE and ctk is not None:
            self._select_btn.configure(text=display_text, text_color=text_color)
        else:
            self._select_btn.configure(text=display_text, fg=text_color)

    def get_value(self) -> Any:
        """获取选中值"""
        if self._mode == SelectMode.SINGLE:
            return self._selected_values[0] if self._selected_values else None
        return self._selected_values.copy()

    def set_value(self, value: Any) -> None:
        """设置选中值"""
        if self._mode == SelectMode.SINGLE:
            self._selected_values = [value] if value is not None else []
        else:
            self._selected_values = list(value) if value else []

        self._update_display()

    def set_options(self, options: list[SelectOption]) -> None:
        """设置选项列表"""
        self._options = options[: self.MAX_OPTIONS]
        self._filtered_options = self._options.copy()
        self._selected_values = []
        self._update_display()

        if self._is_open:
            self._render_options()

    def clear(self) -> None:
        """清空选择"""
        self._selected_values = []
        self._update_display()

    def pack(self, **kwargs: Any) -> None:
        """打包"""
        self._container.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """网格布局"""
        self._container.grid(**kwargs)


__all__ = ["ModernSelect"]
