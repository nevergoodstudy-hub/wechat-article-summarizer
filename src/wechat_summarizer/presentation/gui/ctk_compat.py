"""Shared optional import wrapper for CustomTkinter."""

from __future__ import annotations

from typing import Any

try:
    import customtkinter as _ctk
except ImportError:
    CTK_AVAILABLE = False
    _ctk = None
else:
    CTK_AVAILABLE = True

ctk: Any = _ctk

__all__ = ["CTK_AVAILABLE", "ctk"]
