"""Breakpoint tracking for responsive GUI layouts."""

from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable

from .responsive_models import Breakpoint, BreakpointConfig

logger = logging.getLogger(__name__)


class BreakpointManager:
    """断点管理器 - 监听窗口大小变化"""

    MAX_CALLBACKS = 50
    THROTTLE_MS = 100

    def __init__(self, root: tk.Misc, config: BreakpointConfig | None = None):
        self.root = root
        self.config = config or BreakpointConfig()

        self._callbacks: list[Callable[[Breakpoint, int, int], None]] = []
        self._current_breakpoint: Breakpoint | None = None
        self._last_resize_time: float = 0
        self._pending_resize: str | None = None

        self._last_width = 0
        self._last_height = 0
        self._update_breakpoint()
        self._start_size_polling()

    def _start_size_polling(self) -> None:
        """安全的窗口尺寸轮询（替代 <Configure> 事件绑定）"""
        try:
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            if width != self._last_width or height != self._last_height:
                self._last_width = width
                self._last_height = height
                self._update_breakpoint()
        except Exception:
            pass
        self._pending_resize = self.root.after(500, self._start_size_polling)

    def _update_breakpoint(self) -> None:
        """更新当前断点"""
        self._pending_resize = None

        width = self.root.winfo_width()
        height = self.root.winfo_height()

        new_breakpoint = self._get_breakpoint(width)

        if new_breakpoint != self._current_breakpoint:
            old_breakpoint = self._current_breakpoint
            self._current_breakpoint = new_breakpoint

            logger.info(f"断点变化: {old_breakpoint} -> {new_breakpoint} (width={width})")

            for callback in self._callbacks:
                try:
                    callback(new_breakpoint, width, height)
                except Exception as e:
                    logger.error(f"断点回调执行失败: {e}")

    def _get_breakpoint(self, width: int) -> Breakpoint:
        """根据宽度获取断点"""
        if width < self.config.xs_max:
            return Breakpoint.XS
        if width < self.config.sm_max:
            return Breakpoint.SM
        if width < self.config.md_max:
            return Breakpoint.MD
        if width < self.config.lg_max:
            return Breakpoint.LG
        return Breakpoint.XL

    def on_breakpoint_change(self, callback: Callable[[Breakpoint, int, int], None]) -> bool:
        """注册断点变化回调"""
        if len(self._callbacks) >= self.MAX_CALLBACKS:
            logger.warning(f"回调数量已达上限({self.MAX_CALLBACKS})")
            return False

        self._callbacks.append(callback)
        return True

    def off_breakpoint_change(self, callback: Callable[[Breakpoint, int, int], None]) -> None:
        """移除断点变化回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_current_breakpoint(self) -> Breakpoint:
        """获取当前断点"""
        if self._current_breakpoint is None:
            self._update_breakpoint()
        if self._current_breakpoint is None:
            return Breakpoint.MD
        return self._current_breakpoint

    def get_window_size(self) -> tuple[int, int]:
        """获取当前窗口大小"""
        return self.root.winfo_width(), self.root.winfo_height()

    def is_mobile(self) -> bool:
        """是否为移动端尺寸"""
        return self.get_current_breakpoint() == Breakpoint.XS

    def is_tablet(self) -> bool:
        """是否为平板尺寸"""
        breakpoint = self.get_current_breakpoint()
        return breakpoint in (Breakpoint.SM, Breakpoint.MD)

    def is_desktop(self) -> bool:
        """是否为桌面尺寸"""
        breakpoint = self.get_current_breakpoint()
        return breakpoint in (Breakpoint.LG, Breakpoint.XL)

    def destroy(self) -> None:
        """清理资源"""
        if self._pending_resize:
            self.root.after_cancel(self._pending_resize)
        self._callbacks.clear()


__all__ = ["BreakpointManager"]
