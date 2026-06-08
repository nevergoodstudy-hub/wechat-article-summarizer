"""Live region support for GUI accessibility helpers."""

from __future__ import annotations

import tkinter as tk
from typing import Any


class LiveRegion(tk.Frame):
    """ARIA Live Region - 动态内容通知"""

    def __init__(
        self,
        parent: tk.Misc,
        politeness: str = "polite",
        **kwargs: Any,
    ):
        super().__init__(parent, **kwargs)
        self.politeness = politeness
        self.configure(bg=parent.cget("bg") if hasattr(parent, "cget") else "#1a1a1a")
        self._label = tk.Label(
            self,
            text="",
            bg=self.cget("bg"),
            fg=self.cget("bg"),
            width=1,
            height=1,
        )
        self._label.pack()
        self.place(x=-9999, y=-9999, width=1, height=1)

    def announce(self, message: str, clear_delay: int = 5000) -> None:
        """宣告消息"""
        self._label.configure(text="")
        self.after(100, lambda: self._label.configure(text=message))
        if clear_delay > 0:
            self.after(clear_delay, lambda: self._label.configure(text=""))


__all__ = ["LiveRegion"]
