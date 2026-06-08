"""Compatibility helpers for Tk and CustomTkinter input widgets."""

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
    InputBase: Any = ctk.CTkEntry
    TextAreaBase: Any = ctk.CTkTextbox
else:
    InputBase = tk.Entry
    TextAreaBase = tk.Text


def create_transparent_frame(master: Any) -> Any:
    """Create a transparent frame when CustomTkinter is available."""
    if CTK_AVAILABLE and ctk is not None:
        return ctk.CTkFrame(master, fg_color="transparent")
    return tk.Frame(master)
