"""Factory helpers for input components."""

from __future__ import annotations

from typing import Any

from .input_modern import ModernInput
from .input_textarea import ModernTextArea


def create_input(
    master: Any,
    label: str | None = None,
    placeholder: str = "",
    theme: str = "dark",
    **kwargs: Any,
) -> ModernInput:
    """Create a modern single-line input."""
    return ModernInput(master, label=label, placeholder=placeholder, theme=theme, **kwargs)


def create_textarea(
    master: Any,
    label: str | None = None,
    height: int = 120,
    theme: str = "dark",
    **kwargs: Any,
) -> ModernTextArea:
    """Create a modern multi-line input."""
    return ModernTextArea(master, label=label, height=height, theme=theme, **kwargs)
