"""Compatibility entrypoint for GUI accessibility helpers."""

from __future__ import annotations

from .accessibility_focus import FocusManager
from .accessibility_helper import AccessibilityHelper
from .accessibility_keyboard import KeyboardNavigable
from .accessibility_live import LiveRegion
from .accessibility_models import (
    FocusableElement,
    FocusDirection,
    FocusRingStyle,
    FocusRingStyleDict,
)
from .accessibility_skiplink import SkipLink

__all__ = [
    "AccessibilityHelper",
    "FocusDirection",
    "FocusManager",
    "FocusRingStyle",
    "FocusRingStyleDict",
    "FocusableElement",
    "KeyboardNavigable",
    "LiveRegion",
    "SkipLink",
]


if __name__ == "__main__":
    from .accessibility_demo import run_accessibility_demo

    run_accessibility_demo()
