"""Page router with transition support."""

from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable

from .transition_models import TransitionConfig, TransitionType
from .transition_page import PageTransition

logger = logging.getLogger(__name__)


class PageRouter:
    """页面路由器（带过渡动画）"""

    def __init__(self, container: tk.Widget, default_transition: TransitionConfig | None = None):
        self.container = container
        self.default_transition = default_transition or TransitionConfig()
        self._pages: dict[str, tk.Widget] = {}
        self._current_route: str | None = None
        self._transition = PageTransition(container, self.default_transition)
        self._history: list[str] = []
        self._on_route_change: Callable[[str, str], None] | None = None

    def register_page(self, route: str, page: tk.Widget) -> None:
        """注册页面"""
        self._pages[route] = page

    def navigate_to(
        self,
        route: str,
        transition_type: TransitionType | None = None,
        on_complete: Callable[[], None] | None = None,
    ) -> None:
        """导航到指定路由"""
        if route not in self._pages:
            logger.error(f"路由不存在: {route}")
            return

        if route == self._current_route:
            return

        old_route = self._current_route
        new_page = self._pages[route]

        if self._current_route:
            self._history.append(self._current_route)

        def on_transition_complete() -> None:
            self._current_route = route

            if self._on_route_change and old_route:
                self._on_route_change(old_route, route)

            if on_complete:
                on_complete()

        self._transition.transition_to(new_page, on_transition_complete, transition_type)

    def go_back(self, transition_type: TransitionType | None = None) -> bool:
        """返回上一页"""
        if not self._history:
            return False

        previous_route = self._history.pop()
        reverse_type = transition_type
        if reverse_type is None and self.default_transition.type in (
            TransitionType.SLIDE_LEFT,
            TransitionType.SLIDE_RIGHT,
        ):
            reverse_type = (
                TransitionType.SLIDE_RIGHT
                if self.default_transition.type == TransitionType.SLIDE_LEFT
                else TransitionType.SLIDE_LEFT
            )

        self.navigate_to(previous_route, reverse_type)
        return True

    def on_route_change(self, callback: Callable[[str, str], None]) -> None:
        """设置路由变化回调"""
        self._on_route_change = callback

    def get_current_route(self) -> str | None:
        """获取当前路由"""
        return self._current_route

    def get_history(self) -> list[str]:
        """获取历史记录"""
        return self._history.copy()


__all__ = ["PageRouter"]
