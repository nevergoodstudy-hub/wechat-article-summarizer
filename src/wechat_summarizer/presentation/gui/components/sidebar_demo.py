"""Manual demo for the collapsible sidebar component."""

from __future__ import annotations

import tkinter as tk

from ..utils.i18n import tr
from .sidebar_core import CollapsibleSidebar
from .sidebar_models import NavItem


def run_demo() -> None:
    """Run a small manual sidebar demo."""
    root = tk.Tk()
    root.title(tr("Sidebar 测试"))
    root.geometry("1000x600")
    root.configure(bg="#121212")

    nav_items = [
        NavItem(id="home", label=tr("首页"), icon="🏠"),
        NavItem(
            id="chat",
            label=tr("聊天记录"),
            icon="💬",
            badge=5,
            children=[
                NavItem(id="chat_recent", label=tr("最近"), icon="🕐"),
                NavItem(id="chat_starred", label=tr("已标记"), icon="⭐"),
                NavItem(id="chat_archived", label=tr("已归档"), icon="📦"),
            ],
        ),
        NavItem(id="summary", label=tr("摘要"), icon="📝", badge=2),
        NavItem(id="export", label=tr("导出"), icon="📤"),
        NavItem(id="settings", label=tr("设置"), icon="⚙️"),
    ]

    def on_select(item_id: str) -> None:
        print(f"选择了: {item_id}")

    main_frame = tk.Frame(root, bg="#121212")
    main_frame.pack(fill=tk.BOTH, expand=True)

    sidebar = CollapsibleSidebar(
        main_frame, items=nav_items, on_select=on_select, persist_state=True
    )
    sidebar.pack(side=tk.LEFT, fill=tk.Y)

    content = tk.Frame(main_frame, bg="#1e1e1e")
    content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    tk.Label(
        content,
        text=tr("内容区域"),
        bg="#1e1e1e",
        fg="#e5e5e5",
        font=("Segoe UI", 16),
    ).pack(pady=50)

    root.mainloop()


__all__ = ["run_demo"]
