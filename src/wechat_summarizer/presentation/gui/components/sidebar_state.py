"""State persistence helpers for collapsible sidebar navigation."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)


def default_sidebar_state_file() -> str:
    """Return the default persisted sidebar state path."""
    return os.path.join(os.path.expanduser("~"), ".wechat_summarizer", "sidebar_state.json")


def resolve_sidebar_state_file(
    state_file: str | None,
    *,
    component_file: str | None = None,
) -> str:
    """Validate and normalize the sidebar state file path."""
    if not state_file:
        return default_sidebar_state_file()

    base_dir = os.path.dirname(os.path.abspath(component_file or __file__))
    abs_path = os.path.abspath(state_file)
    if not abs_path.startswith(base_dir) and not state_file.startswith(os.path.expanduser("~")):
        logger.warning("不安全的状态文件路径: %s", state_file)
        return default_sidebar_state_file()
    return state_file


class SidebarStateMixin:
    """Persist and restore sidebar display state."""

    def _load_state(self: Any) -> None:
        """加载保存的状态"""
        if not self.persist_state:
            return

        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, encoding="utf-8") as file:
                    state = json.load(file)

                self._expanded = state.get("expanded", True)
                self._current_width = (
                    self.EXPANDED_WIDTH if self._expanded else self.COLLAPSED_WIDTH
                )
                self._active_item = state.get("active_item")
                self._expanded_submenus = set(state.get("expanded_submenus", []))

                logger.info("侧边栏状态已加载: expanded=%s", self._expanded)
        except Exception as exc:
            logger.warning("加载侧边栏状态失败: %s", exc)

    def _save_state(self: Any) -> None:
        """保存状态"""
        if not self.persist_state:
            return

        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            state = {
                "expanded": self._expanded,
                "active_item": self._active_item,
                "expanded_submenus": list(self._expanded_submenus),
                "timestamp": time.time(),
            }

            with open(self.state_file, "w", encoding="utf-8") as file:
                json.dump(state, file, indent=2)
        except Exception as exc:
            logger.warning("保存侧边栏状态失败: %s", exc)


__all__ = [
    "SidebarStateMixin",
    "default_sidebar_state_file",
    "resolve_sidebar_state_file",
]
