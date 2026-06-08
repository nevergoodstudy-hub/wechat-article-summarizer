"""Tooltip helper used by collapsed sidebar navigation rows."""

from __future__ import annotations

import tkinter as tk
from typing import Any


class Tooltip:
    """Tooltip提示组件"""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.tooltip_window: tk.Toplevel | None = None

        self.widget.bind("<Enter>", self._show)
        self.widget.bind("<Leave>", self._hide)

    def _show(self, event: Any = None) -> None:
        if self.tooltip_window:
            return

        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 5
        y = self.widget.winfo_rooty()

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            bg="#333333",
            fg="#ffffff",
            font=("Segoe UI", 10),
            padx=8,
            pady=4,
        )
        label.pack()

    def _hide(self, event: Any = None) -> None:
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def update_text(self, text: str) -> None:
        self.text = text

    def destroy(self) -> None:
        self._hide()
        self.widget.unbind("<Enter>")
        self.widget.unbind("<Leave>")


__all__ = ["Tooltip"]
