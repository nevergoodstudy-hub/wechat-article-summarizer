"""Draft restore dialog for GUI autosave."""

from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable
from datetime import datetime

from .autosave_manager import AutoSaveManager
from .autosave_models import Draft
from .i18n import tr

logger = logging.getLogger(__name__)


class RestoreDialog(tk.Toplevel):
    """草稿恢复对话框"""

    def __init__(
        self,
        parent: tk.Tk,
        draft: Draft,
        on_restore: Callable[[], None],
        on_discard: Callable[[], None],
    ):
        super().__init__(parent)

        self.draft = draft
        self.on_restore = on_restore
        self.on_discard = on_discard
        self.result = False

        self.title(tr("恢复草稿"))
        self.geometry("400x200")
        self.configure(bg="#1a1a1a")
        self.resizable(False, False)

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 400) // 2
        y = (self.winfo_screenheight() - 200) // 2
        self.geometry(f"+{x}+{y}")

        self._setup_ui()
        self.transient(parent)
        self.grab_set()
        self.focus_set()

    def _setup_ui(self) -> None:
        msg_frame = tk.Frame(self, bg="#1a1a1a", padx=20, pady=20)
        msg_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(msg_frame, text="📝", bg="#1a1a1a", fg="#e5e5e5", font=("Segoe UI", 32)).pack()
        draft_time = datetime.fromtimestamp(self.draft.timestamp)
        time_str = draft_time.strftime("%Y-%m-%d %H:%M:%S")

        tk.Label(
            msg_frame,
            text=tr("发现未保存的草稿\n保存于: {saved_at}").format(saved_at=time_str),
            bg="#1a1a1a",
            fg="#e5e5e5",
            font=("Segoe UI", 12),
            justify="center",
        ).pack(pady=10)

        btn_frame = tk.Frame(self, bg="#1a1a1a", pady=15)
        btn_frame.pack(fill=tk.X)
        self._build_actions(btn_frame)

    def _build_actions(self, btn_frame: tk.Frame) -> None:
        restore_btn = tk.Button(
            btn_frame,
            text=tr("恢复草稿"),
            bg="#3b82f6",
            fg="#ffffff",
            font=("Segoe UI", 11),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._on_restore,
        )
        restore_btn.pack(side=tk.LEFT, padx=(60, 10))

        discard_btn = tk.Button(
            btn_frame,
            text=tr("放弃"),
            bg="#404040",
            fg="#e5e5e5",
            font=("Segoe UI", 11),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._on_discard,
        )
        discard_btn.pack(side=tk.LEFT, padx=10)

    def _on_restore(self) -> None:
        self.result = True
        try:
            self.on_restore()
        except Exception as exc:
            logger.error("恢复回调失败: %s", exc)
        self.destroy()

    def _on_discard(self) -> None:
        self.result = False
        try:
            self.on_discard()
        except Exception as exc:
            logger.error("放弃回调失败: %s", exc)
        self.destroy()


def check_and_restore(root: tk.Tk, form_id: str, manager: AutoSaveManager | None = None) -> bool:
    """检查并提示恢复草稿"""
    if manager is None:
        manager = AutoSaveManager.get_instance()

    draft = manager.get_draft(form_id)
    if draft is None:
        return False

    restored = [False]

    def on_restore() -> None:
        manager.restore(form_id, draft)
        restored[0] = True

    def on_discard() -> None:
        manager.clear_draft(form_id)
        restored[0] = False

    dialog = RestoreDialog(root, draft, on_restore, on_discard)
    root.wait_window(dialog)
    return restored[0]


__all__ = [
    "RestoreDialog",
    "check_and_restore",
]
