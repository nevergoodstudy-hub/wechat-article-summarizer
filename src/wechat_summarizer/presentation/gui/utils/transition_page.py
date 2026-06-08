"""Page transition animation engine."""

from __future__ import annotations

import logging
import time
import tkinter as tk
from collections.abc import Callable

from .transition_easing import Easing
from .transition_models import TransitionConfig, TransitionType

logger = logging.getLogger(__name__)


class PageTransition:
    """页面过渡动画"""

    MAX_DURATION = 2000
    MIN_FRAME_TIME = 16
    MAX_CONCURRENT_ANIMATIONS = 3
    TIMEOUT_MS = 5000

    _active_animations = 0

    def __init__(self, container: tk.Widget, config: TransitionConfig | None = None):
        self.container = container
        self.config = config or TransitionConfig()
        self.config.duration = min(self.config.duration, self.MAX_DURATION)
        self.config.delay = min(self.config.delay, 1000)
        self._is_animating = False
        self._current_page: tk.Widget | None = None
        self._animation_id: str | None = None
        self._start_time: float = 0
        self._easing = Easing.get(self.config.easing)

    def transition_to(
        self,
        new_page: tk.Widget,
        on_complete: Callable[[], None] | None = None,
        transition_type: TransitionType | None = None,
    ) -> None:
        """切换到新页面"""
        if PageTransition._active_animations >= self.MAX_CONCURRENT_ANIMATIONS:
            logger.warning("动画并发数已达上限，跳过动画")
            self._instant_switch(new_page, on_complete)
            return

        if self._is_animating:
            self._cancel_animation()

        trans_type = transition_type or self.config.type
        old_page = self._current_page

        if trans_type == TransitionType.NONE:
            self._instant_switch(new_page, on_complete)
            return

        if self.config.delay > 0:
            self.container.after(
                self.config.delay,
                lambda: self._start_transition(old_page, new_page, trans_type, on_complete),
            )
        else:
            self._start_transition(old_page, new_page, trans_type, on_complete)

    def _start_transition(
        self,
        old_page: tk.Widget | None,
        new_page: tk.Widget,
        trans_type: TransitionType,
        on_complete: Callable[[], None] | None,
    ) -> None:
        """开始过渡动画"""
        PageTransition._active_animations += 1
        self._is_animating = True
        self._start_time = time.time() * 1000

        self._setup_initial_state(new_page, trans_type)
        frame_count = max(1, self.config.duration // self.MIN_FRAME_TIME)
        frame_duration = self.config.duration / frame_count

        def animate_frame(frame: int) -> None:
            elapsed = time.time() * 1000 - self._start_time
            if elapsed > self.TIMEOUT_MS:
                logger.warning("动画超时，强制完成")
                self._finish_transition(old_page, new_page, on_complete)
                return

            if frame > frame_count or not self._is_animating:
                self._finish_transition(old_page, new_page, on_complete)
                return

            progress = self._easing(frame / frame_count)
            self._apply_animation_frame(old_page, new_page, trans_type, progress)
            self._animation_id = self.container.after(
                int(frame_duration), lambda: animate_frame(frame + 1)
            )

        animate_frame(1)

    def _setup_initial_state(self, new_page: tk.Widget, trans_type: TransitionType) -> None:
        """设置初始状态"""
        container_width = self.container.winfo_width()
        container_height = self.container.winfo_height()

        if trans_type == TransitionType.FADE:
            new_page.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        elif trans_type == TransitionType.SLIDE_LEFT:
            new_page.place(x=container_width, y=0, relwidth=1.0, relheight=1.0)
        elif trans_type == TransitionType.SLIDE_RIGHT:
            new_page.place(x=-container_width, y=0, relwidth=1.0, relheight=1.0)
        elif trans_type == TransitionType.SLIDE_UP:
            new_page.place(x=0, y=container_height, relwidth=1.0, relheight=1.0)
        elif trans_type == TransitionType.SLIDE_DOWN:
            new_page.place(x=0, y=-container_height, relwidth=1.0, relheight=1.0)
        elif trans_type in (TransitionType.SCALE, TransitionType.SCALE_FADE):
            new_page.place(relx=0.5, rely=0.5, anchor="center", width=1, height=1)

    def _apply_animation_frame(
        self,
        old_page: tk.Widget | None,
        new_page: tk.Widget,
        trans_type: TransitionType,
        progress: float,
    ) -> None:
        """应用动画帧"""
        container_width = self.container.winfo_width()
        container_height = self.container.winfo_height()

        if trans_type == TransitionType.FADE:
            if progress > 0.5 and old_page:
                old_page.lower()
            new_page.lift()
        elif trans_type == TransitionType.SLIDE_LEFT:
            new_page.place(x=int(container_width * (1 - progress)))
            if old_page:
                old_page.place(x=int(-container_width * progress))
        elif trans_type == TransitionType.SLIDE_RIGHT:
            new_page.place(x=int(-container_width * (1 - progress)))
            if old_page:
                old_page.place(x=int(container_width * progress))
        elif trans_type == TransitionType.SLIDE_UP:
            new_page.place(y=int(container_height * (1 - progress)))
            if old_page:
                old_page.place(y=int(-container_height * progress))
        elif trans_type == TransitionType.SLIDE_DOWN:
            new_page.place(y=int(-container_height * (1 - progress)))
            if old_page:
                old_page.place(y=int(container_height * progress))
        elif trans_type == TransitionType.SCALE:
            self._place_scaled_page(new_page, container_width, container_height, progress)
        elif trans_type == TransitionType.SCALE_FADE:
            self._place_scaled_page(
                new_page,
                container_width,
                container_height,
                0.8 + 0.2 * progress,
            )
            if progress > 0.3 and old_page:
                old_page.lower()
            new_page.lift()

    def _place_scaled_page(
        self,
        new_page: tk.Widget,
        container_width: int,
        container_height: int,
        scale: float,
    ) -> None:
        """Place a page with center-origin scale."""
        width = int(container_width * scale)
        height = int(container_height * scale)
        new_page.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            width=max(1, width),
            height=max(1, height),
        )

    def _finish_transition(
        self,
        old_page: tk.Widget | None,
        new_page: tk.Widget,
        on_complete: Callable[[], None] | None,
    ) -> None:
        """完成过渡"""
        PageTransition._active_animations = max(0, PageTransition._active_animations - 1)
        self._is_animating = False
        self._animation_id = None

        if old_page:
            old_page.place_forget()

        new_page.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        new_page.lift()
        self._current_page = new_page

        if on_complete:
            try:
                on_complete()
            except Exception as exc:
                logger.error(f"过渡完成回调执行失败: {exc}")

    def _instant_switch(self, new_page: tk.Widget, on_complete: Callable[[], None] | None) -> None:
        """即时切换（无动画）"""
        if self._current_page:
            self._current_page.place_forget()

        new_page.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self._current_page = new_page

        if on_complete:
            on_complete()

    def _cancel_animation(self) -> None:
        """取消当前动画"""
        if self._animation_id:
            self.container.after_cancel(self._animation_id)
            self._animation_id = None

        self._is_animating = False
        PageTransition._active_animations = max(0, PageTransition._active_animations - 1)

    def set_config(self, config: TransitionConfig) -> None:
        """更新配置"""
        self.config = config
        self.config.duration = min(self.config.duration, self.MAX_DURATION)
        self._easing = Easing.get(self.config.easing)

    def get_current_page(self) -> tk.Widget | None:
        """获取当前页面"""
        return self._current_page

    def is_animating(self) -> bool:
        """是否正在动画"""
        return self._is_animating


__all__ = ["PageTransition"]
