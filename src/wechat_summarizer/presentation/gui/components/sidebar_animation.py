"""Collapse and expand animation mixin for the sidebar."""

from __future__ import annotations

from typing import Any, cast


class SidebarAnimationMixin:
    """Sidebar width transition behavior."""

    def toggle(self: Any) -> None:
        """切换展开/收起状态"""
        if self._animating:
            return

        self._expanded = not self._expanded
        self._animate_toggle()
        self._save_state()

    def _animate_toggle(self: Any) -> None:
        """执行展开/收起动画"""
        self._animating = True

        start_width = self._current_width
        end_width = self.EXPANDED_WIDTH if self._expanded else self.COLLAPSED_WIDTH
        delta = end_width - start_width
        step_delay = self.ANIMATION_DURATION // self.ANIMATION_STEPS

        def ease_out(progress: float) -> float:
            return 1 - (1 - progress) ** 3

        def animate_step(step: int) -> None:
            if step > self.ANIMATION_STEPS:
                self._animating = False
                self._current_width = end_width
                self.configure(width=end_width)
                self._on_animation_complete()
                return

            progress = ease_out(step / self.ANIMATION_STEPS)
            new_width = int(start_width + delta * progress)
            self._current_width = new_width
            self.configure(width=new_width)

            self.after(step_delay, lambda: animate_step(step + 1))

        animate_step(1)

    def _on_animation_complete(self: Any) -> None:
        """动画完成后更新UI"""
        self.logo_label.config(text="📱" if not self._expanded else "📱 WeChat")
        self.toggle_btn.config(text="◀" if self._expanded else "▶")
        self._render_nav_items()

    def expand(self: Any) -> None:
        """展开侧边栏"""
        if not self._expanded:
            self.toggle()

    def collapse(self: Any) -> None:
        """收起侧边栏"""
        if self._expanded:
            self.toggle()

    def is_expanded(self: Any) -> bool:
        """是否展开状态"""
        return cast(bool, self._expanded)


__all__ = ["SidebarAnimationMixin"]
