"""Manual demo for the context menu component."""

from __future__ import annotations

import tkinter as tk

from .contextmenu_manager import ContextMenuManager
from .contextmenu_models import MenuItem


def run_demo() -> None:
    """Run the context menu demo."""
    root = tk.Tk()
    root.title("上下文菜单测试")
    root.geometry("600x400")
    root.configure(bg="#121212")

    menu_items = [
        MenuItem(
            id="cut", label="剪切", icon="✂️", shortcut="Ctrl+X", on_click=lambda: print("剪切")
        ),
        MenuItem(
            id="copy",
            label="复制",
            icon="📋",
            shortcut="Ctrl+C",
            on_click=lambda: print("复制"),
        ),
        MenuItem(
            id="paste",
            label="粘贴",
            icon="📄",
            shortcut="Ctrl+V",
            on_click=lambda: print("粘贴"),
        ),
        MenuItem(id="sep1", label="", separator=True),
        MenuItem(id="select_all", label="全选", shortcut="Ctrl+A", on_click=lambda: print("全选")),
        MenuItem(id="sep2", label="", separator=True),
        MenuItem(
            id="more",
            label="更多选项",
            icon="⚙️",
            children=[
                MenuItem(id="settings", label="设置", icon="⚙️", on_click=lambda: print("设置")),
                MenuItem(id="help", label="帮助", icon="❓", on_click=lambda: print("帮助")),
            ],
        ),
        MenuItem(id="disabled", label="禁用项", disabled=True),
    ]

    label = tk.Label(
        root,
        text="右键点击此处查看上下文菜单",
        bg="#2a2a2a",
        fg="#e5e5e5",
        font=("Segoe UI", 14),
        padx=40,
        pady=80,
    )
    label.pack(expand=True)

    ContextMenuManager.bind(label, menu_items)

    root.mainloop()


if __name__ == "__main__":
    run_demo()
