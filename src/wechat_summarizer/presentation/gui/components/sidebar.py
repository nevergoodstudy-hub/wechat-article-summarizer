"""Compatibility entrypoint for the collapsible sidebar component."""

from __future__ import annotations

from .sidebar_core import CollapsibleSidebar
from .sidebar_demo import run_demo
from .sidebar_models import NavItem
from .sidebar_state import default_sidebar_state_file, resolve_sidebar_state_file
from .sidebar_tooltip import Tooltip

__all__ = [
    "CollapsibleSidebar",
    "NavItem",
    "Tooltip",
    "default_sidebar_state_file",
    "resolve_sidebar_state_file",
    "run_demo",
]


if __name__ == "__main__":
    run_demo()
