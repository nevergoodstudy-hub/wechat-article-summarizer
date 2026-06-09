"""Dialogs used by batch URL import and validation actions."""

from __future__ import annotations

try:
    from tkinter import filedialog, messagebox
except ImportError:  # pragma: no cover - tkinter is optional in headless builds
    filedialog = None  # type: ignore[assignment]
    messagebox = None  # type: ignore[assignment]


def choose_url_text_file() -> str | None:
    """Ask for a text file containing article URLs."""
    if filedialog is None:
        return None
    return (
        filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        or None
    )


def show_url_file_read_error(error: object) -> None:
    """Display an error from reading an imported URL file."""
    if messagebox is not None:
        messagebox.showerror("错误", f"读取失败: {error}")


def show_clipboard_empty_warning() -> None:
    """Warn that the clipboard did not contain usable text."""
    if messagebox is not None:
        messagebox.showwarning("提示", "剪贴板为空")


def show_empty_batch_url_warning() -> None:
    """Warn that the batch URL input is empty."""
    if messagebox is not None:
        messagebox.showwarning("提示", "请输入URL")


def show_no_valid_url_warning() -> None:
    """Warn that no valid URL was found in the batch input."""
    if messagebox is not None:
        messagebox.showwarning("提示", "未找到有效URL")
