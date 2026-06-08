"""Core collapsible sidebar widget assembly."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from typing import Any

from .sidebar_animation import SidebarAnimationMixin
from .sidebar_items import SidebarItemsMixin
from .sidebar_models import DEFAULT_SIDEBAR_COLORS, NavItem
from .sidebar_state import SidebarStateMixin, resolve_sidebar_state_file
from .sidebar_tooltip import Tooltip


class CollapsibleSidebar(SidebarAnimationMixin, SidebarItemsMixin, SidebarStateMixin, tk.Frame):
    """可折叠侧边栏组件"""

    EXPANDED_WIDTH = 240
    COLLAPSED_WIDTH = 60
    ANIMATION_DURATION = 300
    ANIMATION_STEPS = 15
    MAX_BADGE = 9999

    def __init__(
        self,
        parent: tk.Widget,
        items: list[NavItem],
        on_select: Callable[[str], None] | None = None,
        persist_state: bool = True,
        state_file: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, **kwargs)

        self.items = items
        self.on_select = on_select
        self.persist_state = persist_state
        self.state_file = resolve_sidebar_state_file(state_file, component_file=__file__)

        self._expanded = True
        self._current_width = self.EXPANDED_WIDTH
        self._animating = False
        self._active_item: str | None = None
        self._expanded_submenus: set[str] = set()

        self.colors = DEFAULT_SIDEBAR_COLORS.copy()
        self.configure(bg=self.colors["bg"], width=self._current_width)

        self._item_widgets: dict[str, dict[str, Any]] = {}
        self._tooltips: list[Tooltip] = []

        self._load_state()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """构建UI"""
        self.header = tk.Frame(self, bg=self.colors["bg"], height=60)
        self.header.pack(fill=tk.X)
        self.header.pack_propagate(False)

        self.logo_label = tk.Label(
            self.header,
            text="📱" if not self._expanded else "📱 WeChat",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=("Segoe UI", 14, "bold"),
        )
        self.logo_label.pack(pady=15)

        tk.Frame(self, bg=self.colors["border"], height=1).pack(fill=tk.X)

        self.nav_container = tk.Frame(self, bg=self.colors["bg"])
        self.nav_container.pack(fill=tk.BOTH, expand=True, pady=10)
        self._render_nav_items()

        tk.Frame(self, bg=self.colors["border"], height=1).pack(fill=tk.X)

        self.footer = tk.Frame(self, bg=self.colors["bg"], height=50)
        self.footer.pack(fill=tk.X)
        self.footer.pack_propagate(False)

        self.toggle_btn = tk.Label(
            self.footer,
            text="◀" if self._expanded else "▶",
            bg=self.colors["bg"],
            fg=self.colors["text_secondary"],
            font=("Segoe UI", 12),
            cursor="hand2",
        )
        self.toggle_btn.pack(pady=12)
        self.toggle_btn.bind("<Button-1>", lambda _event: self.toggle())
        self.toggle_btn.bind(
            "<Enter>", lambda _event: self.toggle_btn.config(fg=self.colors["text"])
        )
        self.toggle_btn.bind(
            "<Leave>",
            lambda _event: self.toggle_btn.config(fg=self.colors["text_secondary"]),
        )

    def destroy(self) -> None:
        """清理资源"""
        for tooltip in self._tooltips:
            tooltip.destroy()
        self._tooltips.clear()
        self._item_widgets.clear()
        super().destroy()


__all__ = ["CollapsibleSidebar"]
