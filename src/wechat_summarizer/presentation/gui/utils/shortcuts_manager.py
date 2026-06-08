"""Keyboard shortcut registration and binding manager."""

from __future__ import annotations

import contextlib
import logging
import tkinter as tk
from collections.abc import Callable

from .shortcuts_models import Shortcut, default_shortcuts
from .shortcuts_panel import ShortcutHelpPanel
from .shortcuts_storage import (
    default_shortcuts_config_file,
    load_custom_bindings,
    save_custom_bindings,
)

logger = logging.getLogger(__name__)


class KeyboardShortcutManager:
    """快捷键管理器"""

    MAX_SHORTCUTS = 100
    MODIFIER_MAP = {
        "Ctrl": "Control",
        "Alt": "Alt",
        "Shift": "Shift",
        "Meta": "Meta",
        "Cmd": "Meta",
    }

    _instance: KeyboardShortcutManager | None = None

    def __init__(self, root: tk.Tk):
        self.root = root
        self._shortcuts: dict[str, Shortcut] = {}
        self._bindings: dict[str, str] = {}
        self._enabled = True
        self._config_file = default_shortcuts_config_file()

        self._load_custom_bindings()
        self._register_defaults()
        self.register(
            Shortcut(
                id="show_help",
                name="显示快捷键帮助",
                keys="Ctrl+?",
                callback=self.show_help_panel,
                group="帮助",
            )
        )

    @classmethod
    def get_instance(cls, root: tk.Tk | None = None) -> KeyboardShortcutManager:
        """获取单例实例"""
        if cls._instance is None:
            if root is None:
                raise ValueError("首次调用需要提供root参数")
            cls._instance = cls(root)
        return cls._instance

    def _register_defaults(self) -> None:
        """注册默认快捷键"""
        for shortcut in default_shortcuts():
            if shortcut.id not in self._shortcuts:
                self.register(shortcut, bind=False)

    def register(self, shortcut: Shortcut, bind: bool = True) -> bool:
        """注册快捷键"""
        if len(self._shortcuts) >= self.MAX_SHORTCUTS:
            logger.warning("快捷键数量已达上限")
            return False

        tk_key = self._parse_keys(shortcut.keys)
        if tk_key in self._bindings:
            existing_id = self._bindings[tk_key]
            if existing_id != shortcut.id:
                logger.warning(f"快捷键冲突: {shortcut.keys} 已被 {existing_id} 使用")
                return False

        self._shortcuts[shortcut.id] = shortcut
        self._bindings[tk_key] = shortcut.id

        if bind and shortcut.callback:
            self._bind_key(tk_key, shortcut)

        return True

    def unregister(self, shortcut_id: str) -> None:
        """注销快捷键"""
        if shortcut_id not in self._shortcuts:
            return

        shortcut = self._shortcuts[shortcut_id]
        tk_key = self._parse_keys(shortcut.keys)

        with contextlib.suppress(tk.TclError):
            self.root.unbind_all(f"<{tk_key}>")

        self._bindings.pop(tk_key, None)
        del self._shortcuts[shortcut_id]

    def bind_callback(self, shortcut_id: str, callback: Callable[[], None]) -> None:
        """为已注册的快捷键绑定回调"""
        if shortcut_id not in self._shortcuts:
            logger.warning(f"快捷键不存在: {shortcut_id}")
            return

        shortcut = self._shortcuts[shortcut_id]
        shortcut.callback = callback
        tk_key = self._parse_keys(shortcut.keys)
        self._bind_key(tk_key, shortcut)

    def _bind_key(self, tk_key: str, shortcut: Shortcut) -> None:
        """绑定Tk事件"""

        def handler(_event: tk.Event[tk.Misc]) -> str | None:
            if not self._enabled or not shortcut.enabled:
                return None

            if shortcut.callback:
                try:
                    shortcut.callback()
                except Exception as exc:
                    logger.error(f"快捷键回调执行失败 ({shortcut.id}): {exc}")

            return "break"

        try:
            self.root.bind_all(f"<{tk_key}>", handler)
        except tk.TclError as exc:
            logger.error(f"绑定快捷键失败 ({shortcut.keys}): {exc}")

    def _parse_keys(self, keys: str) -> str:
        """解析快捷键字符串为Tk格式"""
        tk_parts: list[str] = []

        for part in keys.split("+"):
            part = part.strip()
            if part in self.MODIFIER_MAP:
                tk_parts.append(self.MODIFIER_MAP[part])
            elif part == "?":
                tk_parts.append("question")
            elif part == "=":
                tk_parts.append("equal")
            elif part == "-":
                tk_parts.append("minus")
            elif len(part) == 1:
                tk_parts.append(part.lower())
            else:
                tk_parts.append(part)

        return "-".join(tk_parts)

    def rebind(self, shortcut_id: str, new_keys: str) -> bool:
        """重新绑定快捷键"""
        if shortcut_id not in self._shortcuts:
            return False

        shortcut = self._shortcuts[shortcut_id]
        old_tk_key = self._parse_keys(shortcut.keys)
        new_tk_key = self._parse_keys(new_keys)

        if new_tk_key in self._bindings and self._bindings[new_tk_key] != shortcut_id:
            logger.warning(f"快捷键冲突: {new_keys}")
            return False

        with contextlib.suppress(tk.TclError):
            self.root.unbind_all(f"<{old_tk_key}>")

        self._bindings.pop(old_tk_key, None)
        shortcut.keys = new_keys
        self._bindings[new_tk_key] = shortcut_id

        if shortcut.callback:
            self._bind_key(new_tk_key, shortcut)

        self._save_custom_bindings()
        return True

    def enable(self, shortcut_id: str | None = None) -> None:
        """启用快捷键"""
        if shortcut_id:
            if shortcut_id in self._shortcuts:
                self._shortcuts[shortcut_id].enabled = True
        else:
            self._enabled = True

    def disable(self, shortcut_id: str | None = None) -> None:
        """禁用快捷键"""
        if shortcut_id:
            if shortcut_id in self._shortcuts:
                self._shortcuts[shortcut_id].enabled = False
        else:
            self._enabled = False

    def get_shortcut(self, shortcut_id: str) -> Shortcut | None:
        """获取快捷键"""
        return self._shortcuts.get(shortcut_id)

    def get_all_shortcuts(self) -> dict[str, list[Shortcut]]:
        """获取所有快捷键（按组分类）"""
        grouped: dict[str, list[Shortcut]] = {}
        for shortcut in self._shortcuts.values():
            grouped.setdefault(shortcut.group, []).append(shortcut)
        return grouped

    def _load_custom_bindings(self) -> None:
        """加载自定义绑定"""
        load_custom_bindings(self._shortcuts, self._config_file)

    def _save_custom_bindings(self) -> None:
        """保存自定义绑定"""
        save_custom_bindings(self._shortcuts, self._config_file)

    def show_help_panel(self) -> None:
        """显示快捷键帮助面板"""
        ShortcutHelpPanel(self.root, self)


__all__ = ["KeyboardShortcutManager"]
