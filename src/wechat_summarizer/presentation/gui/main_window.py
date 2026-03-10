"""主窗口协调器。

封装 GUI 壳层中的窗口显示、托盘恢复和页面导航逻辑，
作为从 ``app.py`` 继续下沉职责的第一层脚手架。
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from .styles.colors import ModernColors
from .widgets.animation_helper import TransitionManager

if TYPE_CHECKING:
    from .app import WechatSummarizerGUI

_PAGE_NAMES = {
    "home": "首页",
    "single": "单篇处理",
    "batch": "批量处理",
    "history": "历史记录",
    "settings": "设置",
}


class MainWindowCoordinator:
    """协调主窗口外壳与页面切换。"""

    def __init__(self, gui: WechatSummarizerGUI) -> None:
        self.gui = gui

    def bind_event_bus(self):
        """绑定主窗口层的事件总线订阅。"""
        return self.gui.event_bus.subscribe("navigate", self.handle_navigation_event)

    def handle_navigation_event(
        self,
        page_id: str,
        animated: bool = False,
        **_: Any,
    ) -> None:
        """处理页面切换事件。"""
        if animated:
            self.gui._show_page_animated(page_id)
        else:
            self.gui._show_page(page_id)

    def show_main_window(self) -> None:
        """显示主窗口并播放欢迎动画。"""
        self.gui.root.deiconify()
        self.gui.root.lift()
        self.gui.root.focus_force()
        self.gui._play_welcome_animation()

    def restore_from_tray(self) -> None:
        """从托盘恢复窗口。"""
        self.gui.root.deiconify()
        self.gui.root.lift()
        self.gui.root.focus_force()

    def show_page(self, page_id: str) -> None:
        """切换页面。"""
        for frame in self.gui._page_frames.values():
            frame.grid_forget()
        if page_id in self.gui._page_frames:
            self.gui._page_frames[page_id].grid(row=0, column=0, sticky="nsew")
        page = self.gui._page_frames.get(page_id)
        self._notify_page_shown(page)
        for pid, btn in getattr(self.gui, "_nav_buttons", {}).items():
            if pid == page_id:
                btn.configure(
                    fg_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
                    text_color="white",
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
                )
        self.gui._current_page = page_id

    def show_page_animated(self, page_id: str):
        """带平滑滑动动画的页面切换。"""
        if self.gui._current_page == page_id:
            return None

        old_page = self.gui._page_frames.get(self.gui._current_page)
        new_page = self.gui._page_frames.get(page_id)
        if not new_page:
            return None

        if self.gui._is_low_memory_mode():
            self.gui._show_page(page_id)
            return None

        direction = self._resolve_transition_direction(page_id)
        self.gui._update_nav_buttons_animated(page_id)
        self.gui._current_page = page_id

        def on_complete() -> None:
            self.gui._animate_status_change(f"已切换到{self._page_name(page_id)}")
            self._notify_page_shown(new_page)

        TransitionManager.slide_transition(
            self.gui.root,
            self.gui.content_area,
            old_page,
            new_page,
            direction=direction,
            on_complete=on_complete,
        )
        return None

    def fade_in_page(self, page_id: str):
        """淡入新页面并更新导航按钮状态。"""
        new_page = self.gui._page_frames.get(page_id)
        if not new_page:
            return None
        new_page.grid(row=0, column=0, sticky="nsew")
        self.gui._update_nav_buttons_animated(page_id)
        self.gui._current_page = page_id
        self.gui._animate_status_change(f"已切换到{self._page_name(page_id)}")
        return None

    def update_nav_buttons_animated(self, active_page_id: str) -> None:
        """带平滑过渡动画更新导航按钮状态。"""
        for pid, btn in getattr(self.gui, "_nav_buttons", {}).items():
            if pid == active_page_id:
                btn.configure(
                    fg_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
                    text_color="white",
                    hover_color=(ModernColors.LIGHT_ACCENT_HOVER, ModernColors.DARK_ACCENT_HOVER),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
                    hover_color=(ModernColors.LIGHT_HOVER_SUBTLE, ModernColors.DARK_HOVER_SUBTLE),
                )

    def _resolve_transition_direction(self, page_id: str):
        page_order = [
            self.gui.PAGE_HOME,
            self.gui.PAGE_SINGLE,
            self.gui.PAGE_BATCH,
            self.gui.PAGE_HISTORY,
            self.gui.PAGE_SETTINGS,
        ]
        try:
            old_idx = page_order.index(self.gui._current_page)
            new_idx = page_order.index(page_id)
            return (
                TransitionManager.DIRECTION_LEFT
                if new_idx > old_idx
                else TransitionManager.DIRECTION_RIGHT
            )
        except ValueError:
            return TransitionManager.DIRECTION_LEFT

    @staticmethod
    def _notify_page_shown(page: Any) -> None:
        """通知页面已显示。"""
        if page and hasattr(page, "on_page_shown"):
            with contextlib.suppress(Exception):
                page.on_page_shown()

    @staticmethod
    def _page_name(page_id: str) -> str:
        """返回页面显示名称。"""
        return _PAGE_NAMES.get(page_id, page_id)
