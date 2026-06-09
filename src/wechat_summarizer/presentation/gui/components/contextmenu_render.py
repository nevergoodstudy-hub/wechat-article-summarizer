"""Rendering and item interaction helpers for context menus."""

from __future__ import annotations

import contextlib
import html
import tkinter as tk
from typing import Any, cast

from .contextmenu_models import MAX_CONTEXT_MENU_LABEL_LENGTH, MenuItem


class ContextMenuRenderMixin:
    """Render menu items and manage item hover state."""

    def _render_items(self: Any, container: tk.Frame) -> None:
        """渲染菜单项"""
        host = cast(Any, self)
        host._item_frames.clear()

        for idx, item in enumerate(host.items):
            if item.separator:
                sep = tk.Frame(container, bg=host.colors["separator"], height=1)
                sep.pack(fill=tk.X, padx=8, pady=4)
                continue

            frame = tk.Frame(
                container,
                bg=host.colors["item_bg"],
                padx=10,
                pady=6,
                cursor="hand2" if not item.disabled else "",
            )
            frame.pack(fill=tk.X)

            if item.icon:
                icon_label = tk.Label(
                    frame,
                    text=item.icon,
                    bg=frame.cget("bg"),
                    fg=host.colors["text"] if not item.disabled else host.colors["text_disabled"],
                    font=("Segoe UI", 12),
                    width=2,
                )
                icon_label.pack(side=tk.LEFT, padx=(0, 8))

            label_text = html.escape(item.label[:MAX_CONTEXT_MENU_LABEL_LENGTH])
            label = tk.Label(
                frame,
                text=label_text,
                bg=frame.cget("bg"),
                fg=host.colors["text"] if not item.disabled else host.colors["text_disabled"],
                font=("Segoe UI", 11),
                anchor="w",
            )
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            if item.children:
                arrow = tk.Label(
                    frame,
                    text="▶",
                    bg=frame.cget("bg"),
                    fg=host.colors["shortcut"],
                    font=("Segoe UI", 8),
                )
                arrow.pack(side=tk.RIGHT, padx=(10, 0))
            elif item.shortcut:
                shortcut_label = tk.Label(
                    frame,
                    text=item.shortcut,
                    bg=frame.cget("bg"),
                    fg=host.colors["shortcut"],
                    font=("Segoe UI", 10),
                )
                shortcut_label.pack(side=tk.RIGHT, padx=(10, 0))

            host._item_frames.append({"frame": frame, "item": item, "index": idx})

            if not item.disabled:
                host._bind_item_events(frame, item, idx)

    def _bind_item_events(self: Any, frame: tk.Frame, item: MenuItem, idx: int) -> None:
        """绑定菜单项事件"""
        host = cast(Any, self)

        def on_enter(_event: tk.Event) -> None:
            host._highlight_item(idx)
            if item.children:
                host._show_submenu(frame, item)

        def on_leave(_event: tk.Event) -> None:
            if not item.children:
                host._unhighlight_item(idx)

        def on_click(_event: tk.Event) -> None:
            if not item.children:
                host._execute_item(item)

        for widget in [frame, *frame.winfo_children()]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

    def _highlight_item(self: Any, idx: int) -> None:
        """高亮菜单项"""
        host = cast(Any, self)
        if host._selected_index >= 0:
            host._unhighlight_item(host._selected_index)

        host._selected_index = idx

        for item_data in host._item_frames:
            if item_data["index"] == idx:
                frame = item_data["frame"]
                frame.configure(bg=host.colors["item_hover"])
                for child in frame.winfo_children():
                    with contextlib.suppress(tk.TclError):
                        child.configure(bg=host.colors["item_hover"])
                break

    def _unhighlight_item(self: Any, idx: int) -> None:
        """取消高亮"""
        host = cast(Any, self)
        for item_data in host._item_frames:
            if item_data["index"] == idx:
                frame = item_data["frame"]
                frame.configure(bg=host.colors["item_bg"])
                for child in frame.winfo_children():
                    with contextlib.suppress(tk.TclError):
                        child.configure(bg=host.colors["item_bg"])
                break


__all__ = ["ContextMenuRenderMixin"]
