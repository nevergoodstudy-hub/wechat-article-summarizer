"""Keyboard shortcut help panel."""

from __future__ import annotations

import tkinter as tk
from typing import Any

from .shortcuts_models import Shortcut


class ShortcutHelpPanel(tk.Toplevel):
    """快捷键帮助面板"""

    def __init__(self, parent: tk.Tk, manager: Any):
        super().__init__(parent)

        self.manager = manager
        self.title("快捷键帮助")
        self.geometry("500x600")
        self.configure(bg="#1a1a1a")

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 600) // 2
        self.geometry(f"+{x}+{y}")

        self.colors = {
            "bg": "#1a1a1a",
            "card_bg": "#252525",
            "text": "#e5e5e5",
            "text_secondary": "#808080",
            "accent": "#3b82f6",
            "border": "#404040",
        }

        self._setup_ui()
        self.bind("<Escape>", lambda _event: self.destroy())
        self.focus_set()
        self.grab_set()

    def _setup_ui(self) -> None:
        """构建UI"""
        header = tk.Frame(self, bg=self.colors["bg"], height=60)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))

        tk.Label(
            header,
            text="快捷键帮助",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=("Segoe UI", 16, "bold"),
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text="按 Esc 关闭",
            bg=self.colors["bg"],
            fg=self.colors["text_secondary"],
            font=("Segoe UI", 10),
        ).pack(side=tk.RIGHT)

        canvas = tk.Canvas(self, bg=self.colors["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        content = tk.Frame(canvas, bg=self.colors["bg"])

        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        canvas.create_window((0, 0), window=content, anchor=tk.NW)

        for group_name, shortcuts in self.manager.get_all_shortcuts().items():
            self._render_group(content, group_name, shortcuts)

        content.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

        def on_mousewheel(event: tk.Event[tk.Misc]) -> None:
            canvas.yview_scroll(-event.delta // 120, "units")

        canvas.bind("<MouseWheel>", on_mousewheel)

    def _render_group(self, parent: tk.Frame, group_name: str, shortcuts: list[Shortcut]) -> None:
        """渲染快捷键分组"""
        group_header = tk.Frame(parent, bg=self.colors["bg"])
        group_header.pack(fill=tk.X, pady=(15, 8))

        tk.Label(
            group_header,
            text=group_name,
            bg=self.colors["bg"],
            fg=self.colors["accent"],
            font=("Segoe UI", 12, "bold"),
        ).pack(side=tk.LEFT)

        tk.Frame(group_header, bg=self.colors["border"], height=1).pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            padx=(10, 0),
        )

        for shortcut in shortcuts:
            self._render_shortcut(parent, shortcut)

    def _render_shortcut(self, parent: tk.Frame, shortcut: Shortcut) -> None:
        """渲染单个快捷键"""
        row = tk.Frame(parent, bg=self.colors["card_bg"], padx=12, pady=8)
        row.pack(fill=tk.X, pady=2)

        tk.Label(
            row,
            text=shortcut.name,
            bg=self.colors["card_bg"],
            fg=self.colors["text"],
            font=("Segoe UI", 11),
            anchor="w",
        ).pack(side=tk.LEFT)

        key_frame = tk.Frame(row, bg=self.colors["card_bg"])
        key_frame.pack(side=tk.RIGHT)

        for index, part in enumerate(shortcut.keys.split("+")):
            if index > 0:
                tk.Label(
                    key_frame,
                    text="+",
                    bg=self.colors["card_bg"],
                    fg=self.colors["text_secondary"],
                    font=("Segoe UI", 10),
                ).pack(side=tk.LEFT, padx=2)

            tk.Label(
                key_frame,
                text=part.strip(),
                bg="#3a3a3a",
                fg=self.colors["text"],
                font=("Segoe UI", 10),
                padx=6,
                pady=2,
            ).pack(side=tk.LEFT)


__all__ = ["ShortcutHelpPanel"]
