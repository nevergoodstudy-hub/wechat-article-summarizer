"""Factory helpers for progress components."""

from __future__ import annotations

from typing import Any

from .progress_circular import CircularProgress
from .progress_linear import LinearProgress


def create_linear_progress(
    master: Any,
    width: int = 300,
    indeterminate: bool = False,
    theme: str = "dark",
) -> LinearProgress:
    """Create a linear progress bar."""
    return LinearProgress(master, width=width, indeterminate=indeterminate, theme=theme)


def create_circular_progress(
    master: Any,
    size: int = 100,
    indeterminate: bool = False,
    theme: str = "dark",
) -> CircularProgress:
    """Create a circular progress indicator."""
    return CircularProgress(master, size=size, indeterminate=indeterminate, theme=theme)


__all__ = [
    "create_circular_progress",
    "create_linear_progress",
]
