"""Dialogs used by single-article GUI actions."""

from __future__ import annotations

try:
    from tkinter import messagebox
except ImportError:  # pragma: no cover - tkinter is optional in headless builds
    messagebox = None  # type: ignore[assignment]


def show_duplicate_urls_removed(duplicate_count: int) -> None:
    """Notify the user that duplicate batch URLs were removed."""
    if messagebox is not None:
        messagebox.showinfo(
            "已自动去重",
            f"检测到 {duplicate_count} 个重复链接\n已自动删除重复项",
        )


def show_empty_article_url_warning() -> None:
    """Warn that the single-article URL field is empty."""
    if messagebox is not None:
        messagebox.showwarning("提示", "请输入文章URL")


def confirm_process_non_wechat_url() -> bool:
    """Ask whether a URL that does not look like a WeChat article should continue."""
    if messagebox is None:
        return False
    return bool(
        messagebox.askyesno(
            "提示",
            "输入的链接可能不是有效的微信公众号链接\n\n是否继续处理？",
        )
    )


def show_single_fetch_error(message: str) -> None:
    """Display a single-article fetch or summarize error."""
    if messagebox is not None:
        messagebox.showerror("错误", message)


def confirm_export_without_configured_directory() -> bool:
    """Ask whether export should continue without a configured default directory."""
    if messagebox is None:
        return False
    return bool(
        messagebox.askyesno(
            "导出目录未设置",
            "您尚未设置默认导出目录。\n\n"
            "建议在「设置」页面配置导出目录，这样每次导出时会自动定位到该目录。\n\n"
            "是否继续导出？\n"
            "\n· 点击「是」继续导出（每次需手动选择位置）"
            "\n· 点击「否」前往设置页配置导出目录",
            icon="warning",
        )
    )
