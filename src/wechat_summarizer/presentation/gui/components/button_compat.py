"""Compatibility helpers for Tk and CustomTkinter buttons."""

from __future__ import annotations

import tkinter as tk
from typing import Any

try:
    import customtkinter as ctk

    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    ctk = None

if CTK_AVAILABLE and ctk is not None:
    ButtonBase: Any = ctk.CTkButton
else:
    ButtonBase = tk.Button


__all__ = [
    "CTK_AVAILABLE",
    "ButtonBase",
    "ctk",
]
