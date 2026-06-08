"""Manual smoke demo for keyboard shortcuts."""

from __future__ import annotations

import tkinter as tk

from .shortcuts_manager import KeyboardShortcutManager
from .shortcuts_models import Shortcut


def run_demo() -> None:
    """Run a small local demo window."""
    root = tk.Tk()
    root.title("快捷键系统测试")
    root.geometry("600x400")
    root.configure(bg="#121212")

    manager = KeyboardShortcutManager(root)
    manager.bind_callback("save", lambda: print("保存!"))
    manager.bind_callback("open", lambda: print("打开!"))
    manager.bind_callback("find", lambda: print("查找!"))
    manager.register(
        Shortcut(
            id="custom_action",
            name="自定义操作",
            keys="Ctrl+Shift+X",
            callback=lambda: print("自定义操作触发!"),
            group="自定义",
            description="这是一个自定义快捷键",
        )
    )

    tk.Label(
        root,
        text=(
            "按 Ctrl+? 查看快捷键帮助\n\n"
            "试试:\n"
            "Ctrl+S - 保存\n"
            "Ctrl+O - 打开\n"
            "Ctrl+F - 查找\n"
            "Ctrl+Shift+X - 自定义"
        ),
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 14),
        justify="center",
    ).pack(expand=True)

    root.mainloop()


__all__ = ["run_demo"]
