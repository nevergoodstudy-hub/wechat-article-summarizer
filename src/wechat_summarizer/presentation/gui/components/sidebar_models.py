"""Models and constants for collapsible sidebar navigation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class NavItem:
    """导航项定义"""

    id: str
    label: str
    icon: str = "📄"
    badge: int = 0
    children: list[NavItem] = field(default_factory=list)
    on_click: Callable[[], None] | None = None
    disabled: bool = False


DEFAULT_SIDEBAR_COLORS = {
    "bg": "#1a1a1a",
    "item_bg": "#1a1a1a",
    "item_hover": "#2a2a2a",
    "item_active": "#1e3a5f",
    "text": "#e5e5e5",
    "text_secondary": "#808080",
    "accent": "#3b82f6",
    "indicator": "#3b82f6",
    "badge_bg": "#ef4444",
    "badge_text": "#ffffff",
    "border": "#333333",
}


def clamp_badge(count: int, max_badge: int = 9999) -> int:
    """Clamp a badge count into the sidebar's supported display range."""
    return max(0, min(count, max_badge))


__all__ = [
    "DEFAULT_SIDEBAR_COLORS",
    "NavItem",
    "clamp_badge",
]
