"""Navigation item rendering and interaction mixin for the sidebar."""

from __future__ import annotations

import contextlib
import tkinter as tk
from typing import Any, cast

from .sidebar_models import NavItem, clamp_badge
from .sidebar_tooltip import Tooltip


class SidebarItemsMixin:
    """Render navigation rows, badges, tooltips, and submenu state."""

    _active_item: str | None

    def _render_nav_items(self: Any) -> None:
        """渲染导航项"""
        for widget in self.nav_container.winfo_children():
            widget.destroy()

        self._item_widgets.clear()
        for tooltip in self._tooltips:
            tooltip.destroy()
        self._tooltips.clear()

        for item in self.items:
            self._create_nav_item(item, self.nav_container, level=0)

    def _create_nav_item(self: Any, item: NavItem, parent: tk.Widget, level: int = 0) -> None:
        """创建单个导航项"""
        badge = clamp_badge(item.badge, self.MAX_BADGE)
        is_active = self._active_item == item.id
        has_children = bool(item.children)
        is_submenu_expanded = item.id in self._expanded_submenus

        item_frame = tk.Frame(parent, bg=self.colors["bg"])
        item_frame.pack(fill=tk.X, padx=5, pady=1)

        row = tk.Frame(
            item_frame,
            bg=self.colors["item_active"] if is_active else self.colors["item_bg"],
            height=44,
        )
        row.pack(fill=tk.X)
        row.pack_propagate(False)

        indicator = tk.Frame(
            row, bg=self.colors["indicator"] if is_active else self.colors["bg"], width=4
        )
        indicator.pack(side=tk.LEFT, fill=tk.Y)

        if level > 0:
            tk.Frame(row, bg=row.cget("bg"), width=level * 20).pack(side=tk.LEFT)

        icon_label = tk.Label(
            row,
            text=item.icon,
            bg=row.cget("bg"),
            fg=self.colors["text"],
            font=("Segoe UI", 14),
            width=3,
        )
        icon_label.pack(side=tk.LEFT, padx=(10, 5))

        label = tk.Label(
            row,
            text=item.label,
            bg=row.cget("bg"),
            fg=self.colors["text"] if not item.disabled else self.colors["text_secondary"],
            font=("Segoe UI", 11),
            anchor="w",
        )
        if self._expanded:
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        badge_label = self._create_badge_label(row, badge)
        arrow_label = self._create_arrow_label(row, has_children, is_submenu_expanded)

        self._item_widgets[item.id] = {
            "frame": item_frame,
            "row": row,
            "indicator": indicator,
            "icon": icon_label,
            "label": label,
            "badge": badge_label,
            "arrow": arrow_label,
            "item": item,
        }

        self._add_collapsed_tooltip(row, item, badge)
        self._bind_nav_row(row, icon_label, label, item, is_active)
        self._render_submenu(item, item_frame, has_children, is_submenu_expanded, level)

    def _create_badge_label(self: Any, row: tk.Frame, badge: int) -> tk.Label | None:
        if badge <= 0:
            return None

        badge_text = str(badge) if badge < 100 else "99+"
        badge_label = tk.Label(
            row,
            text=badge_text,
            bg=self.colors["badge_bg"],
            fg=self.colors["badge_text"],
            font=("Segoe UI", 9, "bold"),
            padx=5,
            pady=1,
        )
        if self._expanded:
            badge_label.pack(side=tk.RIGHT, padx=10)
        return badge_label

    def _create_arrow_label(
        self: Any,
        row: tk.Frame,
        has_children: bool,
        is_submenu_expanded: bool,
    ) -> tk.Label | None:
        if not has_children or not self._expanded:
            return None

        arrow_label = tk.Label(
            row,
            text="▼" if is_submenu_expanded else "▶",
            bg=row.cget("bg"),
            fg=self.colors["text_secondary"],
            font=("Segoe UI", 8),
        )
        arrow_label.pack(side=tk.RIGHT, padx=10)
        return arrow_label

    def _add_collapsed_tooltip(self: Any, row: tk.Frame, item: NavItem, badge: int) -> None:
        if self._expanded:
            return

        tooltip_text = item.label
        if badge > 0:
            tooltip_text += f" ({badge})"
        self._tooltips.append(Tooltip(row, tooltip_text))

    def _bind_nav_row(
        self: Any,
        row: tk.Frame,
        icon_label: tk.Label,
        label: tk.Label,
        item: NavItem,
        is_active: bool,
    ) -> None:
        if item.disabled:
            return

        def on_enter(_event: Any, r: tk.Frame = row, active: bool = is_active) -> None:
            if not active:
                self._set_row_bg(r, self.colors["item_hover"])

        def on_leave(_event: Any, r: tk.Frame = row, active: bool = is_active) -> None:
            if not active:
                self._set_row_bg(r, self.colors["item_bg"])

        def on_click(_event: Any, nav_item: NavItem = item) -> None:
            self._on_item_click(nav_item)

        for widget in [row, icon_label, label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)
            cast(Any, widget).configure(cursor="hand2")

    @staticmethod
    def _set_row_bg(row: tk.Frame, color: str) -> None:
        row.config(bg=color)
        for child in row.winfo_children():
            with contextlib.suppress(tk.TclError):
                cast(Any, child).config(bg=color)

    def _render_submenu(
        self: Any,
        item: NavItem,
        item_frame: tk.Frame,
        has_children: bool,
        is_submenu_expanded: bool,
        level: int,
    ) -> None:
        if not has_children or not is_submenu_expanded or not self._expanded:
            return

        submenu_frame = tk.Frame(item_frame, bg=self.colors["bg"])
        submenu_frame.pack(fill=tk.X)
        for child in item.children:
            self._create_nav_item(child, submenu_frame, level + 1)

    def _on_item_click(self: Any, item: NavItem) -> None:
        """处理项点击"""
        if item.children:
            if item.id in self._expanded_submenus:
                self._expanded_submenus.discard(item.id)
            else:
                self._expanded_submenus.add(item.id)
            self._render_nav_items()
        else:
            self._active_item = item.id
            self._render_nav_items()

            if item.on_click:
                item.on_click()
            if self.on_select:
                self.on_select(item.id)

        self._save_state()

    def set_active(self: Any, item_id: str) -> None:
        """设置活动项"""
        self._active_item = item_id
        self._render_nav_items()
        self._save_state()

    def get_active(self: Any) -> str | None:
        """获取当前活动项ID"""
        return cast(str | None, self._active_item)

    def set_badge(self: Any, item_id: str, count: int) -> None:
        """设置徽章数量"""
        self._set_item_badge(self.items, item_id, clamp_badge(count, self.MAX_BADGE))
        self._render_nav_items()

    def _set_item_badge(self: Any, items: list[NavItem], item_id: str, count: int) -> bool:
        for item in items:
            if item.id == item_id:
                item.badge = count
                return True
            if self._set_item_badge(item.children, item_id, count):
                return True
        return False

    def update_items(self: Any, items: list[NavItem]) -> None:
        """更新导航项"""
        self.items = items
        self._render_nav_items()


__all__ = ["SidebarItemsMixin"]
