"""Runtime compatibility helpers for progress components."""

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
    LinearProgressBase: Any = ctk.CTkProgressBar
else:
    LinearProgressBase = tk.Canvas


__all__ = [
    "CTK_AVAILABLE",
    "LinearProgressBase",
    "ctk",
    "tk",
]
