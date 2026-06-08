"""Manual demo for GUI accessibility helpers."""

from __future__ import annotations

import tkinter as tk

from .accessibility_focus import FocusManager
from .accessibility_helper import AccessibilityHelper
from .accessibility_live import LiveRegion
from .accessibility_skiplink import SkipLink
from .i18n import tr


def run_accessibility_demo() -> None:
    """Run the manual accessibility demo."""
    root = tk.Tk()
    root.title(tr("可访问性测试"))
    root.geometry("600x400")
    root.configure(bg="#121212")

    focus_manager = FocusManager(root)
    main_content = tk.Frame(root, bg="#121212")
    SkipLink(root, text=tr("跳到主要内容"), target=main_content)

    nav_frame = tk.Frame(root, bg="#1a1a1a", padx=20, pady=10)
    nav_frame.pack(fill=tk.X)
    for index, text in enumerate(["首页", "文章", "设置", "帮助"]):
        label = tr(text)
        btn = tk.Button(
            nav_frame,
            text=label,
            bg="#252525",
            fg="#e5e5e5",
            relief="flat",
            padx=15,
            pady=5,
        )
        btn.pack(side=tk.LEFT, padx=5)
        focus_manager.register(btn, tab_index=index, group="nav", label=label)

    main_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    tk.Label(
        main_content,
        text=tr("主要内容区域"),
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 16, "bold"),
    ).pack(pady=20)

    form_frame = tk.Frame(main_content, bg="#121212")
    form_frame.pack(fill=tk.X, pady=10)
    _add_labeled_entry(form_frame, tr("用户名:"))
    username_entry = _create_entry(form_frame)
    username_entry.pack(fill=tk.X, pady=(5, 15))
    focus_manager.register(username_entry, tab_index=10, group="form", label=tr("用户名"))

    _add_labeled_entry(form_frame, tr("密码:"))
    password_entry = _create_entry(form_frame)
    password_entry.configure(show="•")
    password_entry.pack(fill=tk.X, pady=(5, 15))
    focus_manager.register(password_entry, tab_index=11, group="form", label=tr("密码"))

    submit_btn = tk.Button(
        form_frame,
        text=tr("提交"),
        bg="#3b82f6",
        fg="#ffffff",
        font=("Segoe UI", 12),
        relief="flat",
        padx=20,
        pady=8,
    )
    submit_btn.pack(anchor="w")
    focus_manager.register(submit_btn, tab_index=12, group="form", label=tr("提交按钮"))

    live_region = LiveRegion(root, politeness="polite")

    def on_submit() -> None:
        live_region.announce(tr("表单已提交"))

    submit_btn.configure(command=on_submit)
    AccessibilityHelper.add_keyboard_activation(submit_btn, on_submit)
    tk.Label(
        root,
        text=tr("按Tab键在元素间导航 | 按Enter或Space激活按钮"),
        bg="#121212",
        fg="#808080",
        font=("Segoe UI", 10),
    ).pack(side=tk.BOTTOM, pady=10)
    root.mainloop()


def _add_labeled_entry(parent: tk.Misc, text: str) -> None:
    tk.Label(parent, text=text, bg="#121212", fg="#e5e5e5", font=("Segoe UI", 12)).pack(anchor="w")


def _create_entry(parent: tk.Misc) -> tk.Entry:
    return tk.Entry(
        parent,
        bg="#252525",
        fg="#e5e5e5",
        font=("Segoe UI", 12),
        relief="flat",
        insertbackground="#e5e5e5",
    )


__all__ = ["run_accessibility_demo"]
