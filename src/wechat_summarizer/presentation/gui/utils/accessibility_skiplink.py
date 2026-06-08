"""Skip-link widget for GUI accessibility helpers."""

from __future__ import annotations

import tkinter as tk
from typing import Any


class SkipLink(tk.Frame):
    """Skip Link组件 - 用于跳过导航区域"""

    def __init__(
        self,
        parent: tk.Misc,
        text: str = "跳到主要内容",
        target: tk.Misc | None = None,
        **kwargs: Any,
    ):
        super().__init__(parent, **kwargs)
        self.target = target
        self.configure(bg="#1a1a1a")
        self.link = tk.Label(
            self,
            text=text,
            bg="#3b82f6",
            fg="#ffffff",
            font=("Segoe UI", 12),
            padx=15,
            pady=8,
            cursor="hand2",
        )
        self.link.pack()
        self.link.bind("<Button-1>", self._on_click)
        self.link.bind("<Return>", self._on_click)
        self.link.bind("<space>", self._on_click)
        self.link.bind("<FocusIn>", self._on_focus_in)
        self.link.bind("<FocusOut>", self._on_focus_out)
        self.place(x=-9999, y=-9999)
        self.link["takefocus"] = True

    def _on_click(self, event: Any = None) -> str:
        if self.target and self.target.winfo_exists():
            self.target.focus_set()
        return "break"

    def _on_focus_in(self, event: Any) -> None:
        self.place(x=10, y=10)
        self.lift()

    def _on_focus_out(self, event: Any) -> None:
        self.place(x=-9999, y=-9999)

    def set_target(self, target: tk.Misc) -> None:
        """设置跳转目标"""
        self.target = target


__all__ = ["SkipLink"]
