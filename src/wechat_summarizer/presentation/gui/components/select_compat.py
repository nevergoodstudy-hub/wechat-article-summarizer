"""Compatibility helpers for Tk and CustomTkinter select widgets."""

from __future__ import annotations

import tkinter as tk
from typing import Any

try:
    import customtkinter as ctk

    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    ctk = None


def create_select_container(master: Any) -> Any:
    """Create the select root container."""
    if CTK_AVAILABLE and ctk is not None:
        return ctk.CTkFrame(master, fg_color="transparent")
    return tk.Frame(master)


__all__ = ["CTK_AVAILABLE", "create_select_container", "ctk"]
