"""Focus affordance microinteractions."""

from __future__ import annotations

import contextlib
import tkinter as tk
from typing import Any


class FocusRing:
    """焦点指示环"""

    def __init__(self, widget: tk.Widget, color: str = "#3b82f6", width: int = 2):
        self.widget = widget
        self.color = color
        self.width = width
        self._ring_frame: tk.Frame | None = None

        self.widget.bind("<FocusIn>", self._on_focus_in)
        self.widget.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, _event: Any) -> None:
        if self._ring_frame:
            return

        parent = self.widget.master
        self._ring_frame = tk.Frame(parent, bg=self.color, bd=0)
        self.widget.update_idletasks()
        x = self.widget.winfo_x() - self.width
        y = self.widget.winfo_y() - self.width
        width = self.widget.winfo_width() + 2 * self.width
        height = self.widget.winfo_height() + 2 * self.width

        self._ring_frame.place(x=x, y=y, width=width, height=height)
        self._ring_frame.lower(self.widget)

    def _on_focus_out(self, _event: Any) -> None:
        if self._ring_frame:
            self._ring_frame.destroy()
            self._ring_frame = None

    def destroy(self) -> None:
        with contextlib.suppress(tk.TclError):
            self.widget.unbind("<FocusIn>")
            self.widget.unbind("<FocusOut>")

        if self._ring_frame:
            self._ring_frame.destroy()
            self._ring_frame = None


__all__ = ["FocusRing"]
