"""Clipboard access helpers."""

from __future__ import annotations

from loguru import logger


class ClipboardManager:
    """剪贴板管理器 - 使用 pyperclip 安全访问剪贴板"""

    @staticmethod
    def get_clipboard_content() -> str | None:
        """获取剪贴板内容"""
        try:
            import pyperclip

            content = pyperclip.paste()
            if content:
                logger.debug(f"剪贴板内容长度: {len(content)} 字符")
            return content if content else None
        except Exception as exc:
            logger.debug(f"pyperclip 获取剪贴板失败: {exc}")

        try:
            import tkinter as tk

            temp_root = tk.Tk()
            temp_root.withdraw()
            try:
                content = temp_root.clipboard_get()
                logger.debug(f"剪贴板内容长度: {len(content) if content else 0} 字符")
                return content
            except tk.TclError:
                return None
            finally:
                temp_root.destroy()
        except Exception as exc:
            logger.debug(f"tkinter 获取剪贴板失败: {exc}")
            return None


__all__ = ["ClipboardManager"]
