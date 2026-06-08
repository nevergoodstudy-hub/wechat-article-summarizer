"""Factory helpers for tab components."""

from __future__ import annotations

from typing import Any

from .tabs_modern import ModernTabs


def create_tabs(
    master: Any,
    tabs: list[dict[str, Any]] | None = None,
    closable: bool = True,
    draggable: bool = True,
    theme: str = "dark",
    **kwargs: Any,
) -> ModernTabs:
    """快速创建标签页组件"""
    tab_widget = ModernTabs(master, closable=closable, draggable=draggable, theme=theme, **kwargs)

    if tabs:
        for tab in tabs:
            tab_widget.add_tab(
                tab_id=tab.get("id", str(id(tab))),
                label=tab.get("label", "Tab"),
                closable=tab.get("closable", closable),
                select=tab.get("select", False),
            )

    return tab_widget


__all__ = ["create_tabs"]
