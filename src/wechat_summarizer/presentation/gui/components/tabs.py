"""Compatibility entrypoint for modern tab components."""

from __future__ import annotations

from .tab_indicator import TabIndicator
from .tabs_compat import CTK_AVAILABLE as _CTK_AVAILABLE
from .tabs_compat import ctk
from .tabs_factory import create_tabs
from .tabs_models import DragData, TabButtonWidgets, TabItem, TabPosition
from .tabs_modern import ModernTabs

__all__ = [
    "_CTK_AVAILABLE",
    "DragData",
    "ModernTabs",
    "TabButtonWidgets",
    "TabIndicator",
    "TabItem",
    "TabPosition",
    "create_tabs",
    "ctk",
]
