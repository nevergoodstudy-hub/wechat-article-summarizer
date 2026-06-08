"""Dialog helpers for export workflows."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from ..styles.colors import ModernColors

try:
    from tkinter import filedialog, messagebox
except ImportError:  # pragma: no cover - tkinter is expected for GUI runtime
    filedialog = None  # type: ignore[assignment]
    messagebox = None  # type: ignore[assignment]


def show_export_options_dialog(
    parent: Any,
    exporter_info: dict[str, Any],
    on_select: Callable[[str], None],
) -> None:
    """Show a single-article export format chooser."""
    export_window = ctk.CTkToplevel(parent)
    export_window.title("导出选项")
    export_window.geometry("400x350")
    export_window.transient(parent)
    ctk.CTkLabel(
        export_window, text="📥 选择导出格式", font=ctk.CTkFont(size=18, weight="bold")
    ).pack(pady=20)

    def export_as(target: str) -> None:
        export_window.destroy()
        on_select(target)

    for name, info in exporter_info.items():
        btn_text = f"{('✓' if info.available else '✗')} {name.upper()}"
        if name == "word" and info.available:
            btn_text += " (预览)"
        btn = ctk.CTkButton(
            export_window,
            text=btn_text,
            font=ctk.CTkFont(size=14),
            height=45,
            corner_radius=10,
            fg_color=ModernColors.INFO if info.available else ModernColors.NEUTRAL_BTN_DISABLED,
            state="normal" if info.available else "disabled",
            command=lambda target=name: export_as(target),
        )
        btn.pack(fill="x", padx=30, pady=5)
        if not info.available and info.reason:
            ctk.CTkLabel(
                export_window, text=info.reason, font=ctk.CTkFont(size=11), text_color="gray"
            ).pack()


def choose_export_file_path(
    *,
    extension: str,
    filetype_name: str,
    filetype_pattern: str,
    article_title: str,
    initial_dir: str | None,
) -> str | None:
    """Ask for a single-article export path."""
    if filedialog is None:
        return None
    return (
        filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=[(filetype_name, filetype_pattern)],
            initialfile=f"{article_title[:30]}{extension}",
            initialdir=initial_dir,
        )
        or None
    )


def choose_batch_output_directory() -> str | None:
    """Ask for a batch export output directory."""
    if filedialog is None:
        return None
    return filedialog.askdirectory(title="选择输出目录") or None


def show_export_success(message: str) -> None:
    """Show a generic export success message."""
    if messagebox is not None:
        messagebox.showinfo("成功", f"导出成功: {message}")


def show_export_error(message: str) -> None:
    """Show a generic export failure message."""
    if messagebox is not None:
        messagebox.showerror("错误", f"导出失败: {message}")


def show_batch_export_success(success_count: int, total: int, dir_path: str) -> None:
    """Show a batch export success summary."""
    if messagebox is not None:
        messagebox.showinfo("成功", f"导出完成: {success_count}/{total} 篇\n输出目录: {dir_path}")


__all__ = [
    "choose_batch_output_directory",
    "choose_export_file_path",
    "show_batch_export_success",
    "show_export_error",
    "show_export_options_dialog",
    "show_export_success",
]
