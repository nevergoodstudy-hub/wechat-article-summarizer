"""Rendering and selection mixin for virtual lists."""

from __future__ import annotations

import contextlib
import logging
import time
import tkinter as tk
from typing import Any, cast

from .virtuallist_models import RENDER_TIMEOUT_MS

logger = logging.getLogger(__name__)


class VirtualListRenderMixin:
    """Rendering helpers for ``VirtualList``."""

    def _render_visible(self: Any):
        """渲染可见区域"""
        host = cast(Any, self)
        start_time = time.time()

        new_range = host._get_visible_range()
        if new_range == host._visible_range and host._rendered_widgets:
            return

        _old_start, _old_end = host._visible_range
        new_start, new_end = new_range

        for i in list(host._rendered_widgets.keys()):
            if i < new_start or i >= new_end:
                widget = host._rendered_widgets.pop(i)
                widget.destroy()

        for i in range(new_start, new_end):
            if (time.time() - start_time) * 1000 > RENDER_TIMEOUT_MS:
                logger.warning("渲染超时，延迟剩余项")
                host.after(50, host._render_visible)
                break

            if i not in host._rendered_widgets and i in host._items:
                host._render_item_at(i)

        host._visible_range = new_range
        host._check_load_more()

    def _render_item_at(self: Any, index: int):
        """渲染指定索引的项"""
        host = cast(Any, self)
        if index >= len(host._data):
            return

        item = host._items.get(index)
        if not item:
            return

        container = tk.Frame(host._content, bg=host._bg, height=item.height)

        try:
            widget = host._render_item(container, item.data, index)
            if widget:
                widget.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            logger.error(f"渲染项失败 ({index}): {e}")
            return

        container.place(x=0, y=item.y_offset, relwidth=1.0, height=item.height)
        host._bind_item_events(container, index)
        host._rendered_widgets[index] = container

    def _bind_item_events(self: Any, widget: tk.Widget, index: int):
        """绑定项事件"""
        host = cast(Any, self)

        def on_enter(_event):
            host._hover_index = index
            if index != host._selected_index:
                cast(Any, widget).configure(bg="#252525")
                for child in widget.winfo_children():
                    with contextlib.suppress(tk.TclError):
                        cast(Any, child).configure(bg="#252525")

        def on_leave(_event):
            host._hover_index = None
            if index != host._selected_index:
                cast(Any, widget).configure(bg=host._bg)
                for child in widget.winfo_children():
                    with contextlib.suppress(tk.TclError):
                        cast(Any, child).configure(bg=host._bg)

        def on_click(_event):
            host._select_item(index)
            if host._on_item_click:
                try:
                    host._on_item_click(index, host._data[index])
                except Exception as err:
                    logger.error(f"点击回调失败: {err}")

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        widget.bind("<Button-1>", on_click)

        for child in widget.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)
            child.bind("<Button-1>", on_click)

    def _select_item(self: Any, index: int):
        """选择项"""
        host = cast(Any, self)
        if host._selected_index is not None and host._selected_index in host._rendered_widgets:
            old_widget = host._rendered_widgets[host._selected_index]
            cast(Any, old_widget).configure(bg=host._bg)
            for child in old_widget.winfo_children():
                with contextlib.suppress(tk.TclError):
                    cast(Any, child).configure(bg=host._bg)

        host._selected_index = index
        if index in host._rendered_widgets:
            widget = host._rendered_widgets[index]
            cast(Any, widget).configure(bg="#3b82f6")
            for child in widget.winfo_children():
                with contextlib.suppress(tk.TclError):
                    cast(Any, child).configure(bg="#3b82f6")

    def _default_render(self: Any, container: tk.Frame, data: Any, index: int) -> tk.Widget:
        """默认渲染函数"""
        host = cast(Any, self)
        return tk.Label(
            container,
            text=str(data),
            bg=host._bg,
            fg="#e5e5e5",
            font=("Segoe UI", 12),
            anchor="w",
            padx=12,
            pady=8,
        )


__all__ = ["VirtualListRenderMixin"]
