"""CustomTkinter compatibility for card components."""

from __future__ import annotations

try:
    import customtkinter as ctk

    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    ctk = None  # type: ignore[assignment]


__all__ = ["CTK_AVAILABLE", "ctk"]
