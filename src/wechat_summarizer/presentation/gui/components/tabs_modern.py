"""Modern tab view component."""

from __future__ import annotations

import html
import tkinter as tk
from collections.abc import Callable
from typing import Any

from .tab_indicator import TabIndicator
from .tabs_button import TabsButtonMixin
from .tabs_drag import TabsDragMixin
from .tabs_models import DragData, TabButtonWidgets, TabItem, TabPosition, tab_theme_colors
from .tabs_selection import TabsSelectionMixin


class ModernTabs(
    TabsButtonMixin,
    TabsSelectionMixin,
    TabsDragMixin,
    tk.Frame,
):
    """现代标签页组件"""

    MAX_TABS = 50
    MAX_LABEL_LENGTH = 50

    def __init__(
        self,
        master: Any,
        position: TabPosition = TabPosition.TOP,
        closable: bool = True,
        draggable: bool = True,
        on_tab_change: Callable[[str], None] | None = None,
        on_tab_close: Callable[[str], bool] | None = None,
        on_tab_reorder: Callable[[list[str]], None] | None = None,
        theme: str = "dark",
        **kwargs: Any,
    ):
        self._theme = theme
        self._colors = self._get_colors(theme)

        super().__init__(master, bg=self._colors["bg"], **kwargs)

        self._position = position
        self._closable = closable
        self._draggable = draggable
        self._on_tab_change = on_tab_change
        self._on_tab_close = on_tab_close
        self._on_tab_reorder = on_tab_reorder
        self._tabs: list[TabItem] = []
        self._active_tab_id: str | None = None
        self._tab_buttons: dict[str, TabButtonWidgets] = {}
        self._drag_data: DragData = {"tab_id": None, "start_x": 0, "start_index": 0}
        self._content_frame: tk.Frame

        self._setup_ui()

    def _get_colors(self, theme: str) -> dict[str, str]:
        """获取颜色配置 (Tkinter兼容版本)"""
        return tab_theme_colors(theme)

    def _setup_ui(self) -> None:
        """构建UI"""
        self._tab_bar_frame = tk.Frame(self, bg=self._colors["tab_bar_bg"])
        self._tab_bar_canvas = tk.Canvas(
            self._tab_bar_frame,
            bg=self._colors["tab_bar_bg"],
            highlightthickness=0,
            height=40,
        )
        self._tab_bar_canvas.pack(fill="x", expand=True)

        self._tabs_container = tk.Frame(self._tab_bar_canvas, bg=self._colors["tab_bar_bg"])
        self._tab_bar_canvas.create_window(0, 0, window=self._tabs_container, anchor="nw")
        self._indicator = TabIndicator(
            self._tab_bar_canvas,
            color=self._colors["indicator"],
            height=3,
            animation_duration=200,
        )

        self._content_frame = tk.Frame(self, bg=self._colors["bg"])
        self._pack_tab_regions()
        self.bind_all("<Control-Tab>", self._on_ctrl_tab)
        self.bind_all("<Control-Shift-Tab>", self._on_ctrl_shift_tab)

    def _pack_tab_regions(self) -> None:
        if self._position == TabPosition.TOP:
            self._tab_bar_frame.pack(fill="x", side="top")
            self._content_frame.pack(fill="both", expand=True, side="top")
        elif self._position == TabPosition.BOTTOM:
            self._content_frame.pack(fill="both", expand=True, side="top")
            self._tab_bar_frame.pack(fill="x", side="bottom")

    def add_tab(
        self,
        tab_id: str,
        label: str,
        content: tk.Widget | None = None,
        closable: bool | None = None,
        icon: Any | None = None,
        select: bool = True,
    ) -> bool:
        """添加标签"""
        if len(self._tabs) >= self.MAX_TABS:
            return False
        if any(tab.id == tab_id for tab in self._tabs):
            return False

        tab = TabItem(
            id=tab_id,
            label=html.escape(label[: self.MAX_LABEL_LENGTH]),
            closable=closable if closable is not None else self._closable,
            icon=icon,
            content=content,
        )
        self._tabs.append(tab)
        self._create_tab_button(tab)

        if select or self._active_tab_id is None:
            self.select_tab(tab_id)

        return True

    def destroy(self) -> None:
        """销毁组件"""
        self._indicator.destroy()

        try:
            self.unbind_all("<Control-Tab>")
            self.unbind_all("<Control-Shift-Tab>")
        except Exception:
            pass

        super().destroy()


__all__ = ["ModernTabs"]
