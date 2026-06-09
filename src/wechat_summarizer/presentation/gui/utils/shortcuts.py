"""Compatibility entrypoint for keyboard shortcuts."""

from __future__ import annotations

from .shortcuts_manager import KeyboardShortcutManager
from .shortcuts_models import Shortcut
from .shortcuts_panel import ShortcutHelpPanel

__all__ = [
    "KeyboardShortcutManager",
    "Shortcut",
    "ShortcutHelpPanel",
]


if __name__ == "__main__":
    from .shortcuts_demo import run_demo

    run_demo()
