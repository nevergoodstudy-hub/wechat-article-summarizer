"""Dialog helpers used by the settings page."""

from __future__ import annotations

from pathlib import Path

from ..utils.i18n import tr

try:
    from tkinter import filedialog, messagebox
except ImportError:  # pragma: no cover - tkinter is expected for GUI runtime
    filedialog = None  # type: ignore[assignment]
    messagebox = None  # type: ignore[assignment]


def choose_export_directory(current_dir: str) -> str | None:
    """Ask the user to choose the default export directory."""
    if filedialog is None:
        return None
    initial_dir = current_dir if current_dir and Path(current_dir).exists() else str(Path.home())
    return filedialog.askdirectory(title=tr("选择默认导出目录"), initialdir=initial_dir) or None


def confirm_clear_api_keys() -> bool:
    """Confirm clearing all API keys."""
    if messagebox is None:
        return True
    return bool(messagebox.askyesno(tr("确认"), tr("确定要清除所有API密钥吗？")))


def confirm_reset_export_settings() -> bool:
    """Confirm resetting export settings."""
    if messagebox is None:
        return True
    return bool(messagebox.askyesno(tr("确认"), tr("确定要重置所有导出设置吗？")))


def confirm_create_missing_directory(export_dir: str) -> bool:
    """Confirm creating a missing export directory."""
    if messagebox is None:
        return False
    return bool(
        messagebox.askyesno(
            tr("确认"),
            tr("目录不存在\n{path}\n\n是否创建？").format(path=export_dir),
        )
    )


def show_missing_export_directory(export_dir: str) -> None:
    """Show a warning for a missing export directory."""
    if messagebox is not None:
        messagebox.showwarning(tr("提示"), tr("目录不存在: {path}").format(path=export_dir))


def show_export_directory_not_configured() -> None:
    """Show an info dialog when no export directory has been configured."""
    if messagebox is not None:
        messagebox.showinfo(tr("提示"), tr("请先设置导出目录"))


def show_startup_error(message: str) -> None:
    """Show an autostart operation error."""
    if messagebox is not None:
        messagebox.showerror(tr("错误"), message)


def show_create_directory_error(message: str) -> None:
    """Show a create-directory error."""
    if messagebox is not None:
        messagebox.showerror(tr("错误"), message)


__all__ = [
    "choose_export_directory",
    "confirm_clear_api_keys",
    "confirm_create_missing_directory",
    "confirm_reset_export_settings",
    "show_create_directory_error",
    "show_export_directory_not_configured",
    "show_missing_export_directory",
    "show_startup_error",
]
