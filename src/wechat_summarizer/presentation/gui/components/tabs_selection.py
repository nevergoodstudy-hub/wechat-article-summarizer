"""Tab selection, close, and content mixin."""

from __future__ import annotations

import html
import tkinter as tk
from typing import Any, cast

from .tabs_compat import CTK_AVAILABLE
from .tabs_models import TabItem


class TabsSelectionMixin:
    """Selection, content, and label mutation behavior for tabs."""

    _active_tab_id: str | None
    _colors: dict[str, str]
    _content_frame: tk.Frame
    _tab_buttons: dict[str, Any]
    _tabs: list[TabItem]

    def select_tab(self: Any, tab_id: str) -> None:
        """选中标签"""
        tab = self._get_tab(tab_id)
        if not tab or tab.disabled:
            return

        old_id = self._active_tab_id
        self._active_tab_id = tab_id
        self._update_tab_styles()
        self._update_content(tab)
        self._update_indicator()

        if self._on_tab_change and old_id != tab_id:
            self._on_tab_change(tab_id)

    def close_tab(self: Any, tab_id: str) -> bool:
        """关闭标签"""
        tab = self._get_tab(tab_id)
        if not tab or not tab.closable:
            return False

        if self._on_tab_close and not self._on_tab_close(tab_id):
            return False

        index = self._get_tab_index(tab_id)

        if tab_id in self._tab_buttons:
            self._tab_buttons[tab_id]["frame"].destroy()
            del self._tab_buttons[tab_id]

        self._tabs.remove(tab)

        if self._active_tab_id == tab_id:
            if self._tabs:
                new_index = min(index, len(self._tabs) - 1)
                self.select_tab(self._tabs[new_index].id)
            else:
                self._active_tab_id = None
                self._clear_content()

        return True

    def _get_tab(self: Any, tab_id: str) -> TabItem | None:
        for tab in self._tabs:
            if tab.id == tab_id:
                return cast(TabItem, tab)
        return None

    def _get_tab_index(self: Any, tab_id: str | None) -> int:
        if tab_id is None:
            return -1
        for index, tab in enumerate(self._tabs):
            if tab.id == tab_id:
                return index
        return -1

    def _update_tab_styles(self: Any) -> None:
        for tab_id, widgets in self._tab_buttons.items():
            is_active = tab_id == self._active_tab_id
            label_btn = widgets["label"]

            if CTK_AVAILABLE:
                if is_active:
                    label_btn.configure(
                        text_color=self._colors["text"],
                        fg_color=self._colors["tab_active_bg"],
                    )
                else:
                    label_btn.configure(
                        text_color=self._colors["text_secondary"],
                        fg_color="transparent",
                    )
            elif is_active:
                label_btn.configure(fg=self._colors["text"], bg=self._colors["tab_active_bg"])
            else:
                label_btn.configure(
                    fg=self._colors["text_secondary"],
                    bg=self._colors["tab_bar_bg"],
                )

    def _update_content(self: Any, tab: TabItem) -> None:
        for child in self._content_frame.winfo_children():
            cast(Any, child).pack_forget()

        if tab.content:
            tab.content.pack(fill="both", expand=True)

    def _clear_content(self: Any) -> None:
        for child in self._content_frame.winfo_children():
            cast(Any, child).pack_forget()

    def _update_indicator(self: Any) -> None:
        if not self._active_tab_id or self._active_tab_id not in self._tab_buttons:
            return

        btn_frame = self._tab_buttons[self._active_tab_id]["frame"]
        self._tabs_container.update_idletasks()
        self._indicator.move_to(btn_frame.winfo_x(), btn_frame.winfo_width(), 37)

    def get_content_frame(self: Any) -> tk.Frame:
        """获取内容区域Frame"""
        return cast(tk.Frame, self._content_frame)

    def get_active_tab(self: Any) -> str | None:
        """获取当前活动标签ID"""
        return cast(str | None, self._active_tab_id)

    def get_tabs(self: Any) -> list[str]:
        """获取所有标签ID"""
        return [tab.id for tab in self._tabs]

    def set_tab_label(self: Any, tab_id: str, label: str) -> None:
        """设置标签文本"""
        tab = self._get_tab(tab_id)
        if not tab:
            return

        label = html.escape(label[: self.MAX_LABEL_LENGTH])
        tab.label = label

        if tab_id in self._tab_buttons:
            self._tab_buttons[tab_id]["label"].configure(text=label)


__all__ = ["TabsSelectionMixin"]
