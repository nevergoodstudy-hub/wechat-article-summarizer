"""Dialogs used by the history page."""

from __future__ import annotations

try:
    from tkinter import messagebox
except ImportError:  # pragma: no cover - tkinter is optional in headless builds
    messagebox = None  # type: ignore[assignment]


def confirm_delete_history_article(title: str) -> bool:
    """Ask whether a cached article should be deleted."""
    if messagebox is None:
        return False
    return bool(messagebox.askyesno("确认", f'删除 "{title[:25]}..." ?'))


def show_delete_history_error(error: object) -> None:
    """Display a cached article deletion error."""
    if messagebox is not None:
        messagebox.showerror("错误", f"删除失败: {error}")


def confirm_clear_cache() -> bool:
    """Ask whether all cached history should be cleared."""
    if messagebox is None:
        return False
    return bool(messagebox.askyesno("确认", "确定清空所有缓存？此操作不可撤销。"))


def show_clear_cache_success(count: int) -> None:
    """Display the number of removed cache entries."""
    if messagebox is not None:
        messagebox.showinfo("成功", f"已清空 {count} 条缓存")


def show_clear_cache_error(error: object) -> None:
    """Display a cache clearing error."""
    if messagebox is not None:
        messagebox.showerror("错误", f"清空失败: {error}")
