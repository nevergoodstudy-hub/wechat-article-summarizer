"""Persistence helpers for custom keyboard shortcuts."""

from __future__ import annotations

import json
import os

from loguru import logger

from .shortcuts_models import Shortcut


def default_shortcuts_config_file() -> str:
    """Return the user-specific shortcuts configuration path."""
    return os.path.join(os.path.expanduser("~"), ".wechat_summarizer", "shortcuts.json")


def load_custom_bindings(
    shortcuts: dict[str, Shortcut],
    config_file: str,
) -> None:
    """Apply persisted custom key strings to registered shortcuts."""
    try:
        if os.path.exists(config_file):
            with open(config_file, encoding="utf-8") as file:
                custom = json.load(file)

            for shortcut_id, keys in custom.items():
                if shortcut_id in shortcuts:
                    shortcuts[shortcut_id].keys = keys

    except Exception as exc:
        logger.warning(f"加载快捷键配置失败: {exc}")


def save_custom_bindings(
    shortcuts: dict[str, Shortcut],
    config_file: str,
) -> None:
    """Persist current key strings."""
    try:
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        custom = {shortcut.id: shortcut.keys for shortcut in shortcuts.values()}

        with open(config_file, "w", encoding="utf-8") as file:
            json.dump(custom, file, indent=2, ensure_ascii=False)

    except Exception as exc:
        logger.warning(f"保存快捷键配置失败: {exc}")


__all__ = [
    "default_shortcuts_config_file",
    "load_custom_bindings",
    "save_custom_bindings",
]
