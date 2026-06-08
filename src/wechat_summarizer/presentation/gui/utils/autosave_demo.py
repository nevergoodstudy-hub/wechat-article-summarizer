"""Manual demo for GUI autosave."""

from __future__ import annotations

import tkinter as tk

from .autosave_dialog import check_and_restore
from .autosave_manager import AutoSaveManager
from .autosave_models import FormField
from .i18n import tr


def run_autosave_demo() -> None:
    """Run a local autosave demo for development."""
    root = tk.Tk()
    root.title(tr("自动保存测试"))
    root.geometry("500x400")
    root.configure(bg="#121212")

    form_frame = tk.Frame(root, bg="#121212", padx=30, pady=30)
    form_frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(
        form_frame,
        text=tr("标题:"),
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 12),
    ).pack(anchor="w", pady=(0, 5))

    title_entry = tk.Entry(
        form_frame,
        bg="#252525",
        fg="#e5e5e5",
        font=("Segoe UI", 12),
        relief="flat",
        insertbackground="#e5e5e5",
    )
    title_entry.pack(fill=tk.X, pady=(0, 15))

    tk.Label(
        form_frame,
        text=tr("内容:"),
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 12),
    ).pack(anchor="w", pady=(0, 5))

    content_text = tk.Text(
        form_frame,
        bg="#252525",
        fg="#e5e5e5",
        font=("Segoe UI", 12),
        relief="flat",
        insertbackground="#e5e5e5",
        height=8,
    )
    content_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

    manager = AutoSaveManager.get_instance()
    manager.register_form(
        form_id="test_form",
        fields=[
            FormField(name="title", widget=title_entry),
            FormField(name="content", widget=content_text),
        ],
        debounce_ms=500,
    )

    status_label = tk.Label(
        form_frame,
        text=tr("输入内容后自动保存..."),
        bg="#121212",
        fg="#808080",
        font=("Segoe UI", 10),
    )
    status_label.pack(anchor="w")

    root.after(100, lambda: check_and_restore(root, "test_form", manager))
    root.mainloop()


__all__ = ["run_autosave_demo"]
