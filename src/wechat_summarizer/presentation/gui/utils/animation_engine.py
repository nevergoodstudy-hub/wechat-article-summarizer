"""Animation engine for GUI utilities."""

from __future__ import annotations

import logging
import time
import tkinter as tk
from collections.abc import Callable
from typing import Any

from .animation_easing import Easing
from .animation_models import EasingType, Tween
from .display import DisplayHelper

logger = logging.getLogger(__name__)


class AnimationEngine:
    """统一动画引擎"""

    MAX_ANIMATIONS = 50
    MAX_DURATION = 10000

    _instance: AnimationEngine | None = None

    def __init__(self, root: tk.Tk):
        self.root = root
        self._animations: dict[str, Tween] = {}
        self._sequences: dict[str, list[Tween]] = {}
        self._is_running = False
        self._frame_time = DisplayHelper.get_frame_time()
        self._loop_id: str | None = None
        self._frame_count = 0
        self._last_fps_time = time.time()
        self._current_fps = 0

    @classmethod
    def get_instance(cls, root: tk.Tk | None = None) -> AnimationEngine:
        """获取单例实例"""
        if cls._instance is None:
            if root is None:
                raise ValueError("首次调用需要提供root参数")
            cls._instance = cls(root)
        return cls._instance

    def animate(
        self,
        target: Any,
        property_name: str,
        end_value: float,
        duration: int = 300,
        easing: EasingType = EasingType.EASE_OUT_CUBIC,
        delay: int = 0,
        on_update: Callable[[float], None] | None = None,
        on_complete: Callable[[], None] | None = None,
    ) -> str:
        """创建单个动画"""
        if len(self._animations) >= self.MAX_ANIMATIONS:
            logger.warning("动画数量已达上限")
            return ""

        duration = min(duration, self.MAX_DURATION)
        start_value = self._get_start_value(target, property_name)
        tween = Tween(
            target=target,
            property_name=property_name,
            start_value=float(start_value),
            end_value=float(end_value),
            duration=duration,
            easing=easing,
            delay=delay,
            on_update=on_update,
            on_complete=on_complete,
        )
        self._animations[tween._id] = tween

        if not self._is_running:
            self._start_loop()

        return tween._id

    def _get_start_value(self, target: Any, property_name: str) -> float:
        try:
            if callable(getattr(target, property_name, None)):
                return float(getattr(target, property_name)())
            return float(getattr(target, property_name))
        except Exception:
            return 0

    def animate_widget(
        self,
        widget: tk.Widget,
        properties: dict[str, float],
        duration: int = 300,
        easing: EasingType = EasingType.EASE_OUT_CUBIC,
        delay: int = 0,
        on_complete: Callable[[], None] | None = None,
    ) -> list[str]:
        """动画化Widget的多个属性"""
        ids = []

        for prop, end_value in properties.items():
            tween_id = self.animate(
                target=widget,
                property_name=prop,
                end_value=end_value,
                duration=duration,
                easing=easing,
                delay=delay,
            )
            if tween_id:
                ids.append(tween_id)

        if ids and on_complete:
            last_tween = self._animations.get(ids[-1])
            if last_tween:
                last_tween.on_complete = on_complete

        return ids

    def sequence(self, tweens: list[Tween], on_complete: Callable[[], None] | None = None) -> str:
        """顺序执行动画"""
        if not tweens:
            return ""

        seq_id = f"seq_{time.time_ns()}"
        cumulative_delay = 0
        for index, tween in enumerate(tweens):
            tween.delay = cumulative_delay
            cumulative_delay += tween.duration + tween.delay

            if index == len(tweens) - 1 and on_complete:
                original_complete = tween.on_complete

                def wrapped_complete(oc=original_complete) -> None:
                    if oc:
                        oc()
                    on_complete()

                tween.on_complete = wrapped_complete

            self._animations[tween._id] = tween

        self._sequences[seq_id] = tweens

        if not self._is_running:
            self._start_loop()

        return seq_id

    def parallel(self, tweens: list[Tween], on_complete: Callable[[], None] | None = None) -> str:
        """并行执行动画"""
        if not tweens:
            return ""

        par_id = f"par_{time.time_ns()}"
        completed_count = [0]
        total_count = len(tweens)

        def check_complete() -> None:
            completed_count[0] += 1
            if completed_count[0] >= total_count and on_complete:
                on_complete()

        for tween in tweens:
            original_complete = tween.on_complete

            def wrapped_complete(orig=original_complete) -> None:
                if orig:
                    orig()
                check_complete()

            tween.on_complete = wrapped_complete
            self._animations[tween._id] = tween

        if not self._is_running:
            self._start_loop()

        return par_id

    def stop(self, animation_id: str) -> None:
        """停止指定动画"""
        if animation_id in self._animations:
            del self._animations[animation_id]

        if animation_id in self._sequences:
            for tween in self._sequences[animation_id]:
                if tween._id in self._animations:
                    del self._animations[tween._id]
            del self._sequences[animation_id]

    def stop_all(self) -> None:
        """停止所有动画"""
        self._animations.clear()
        self._sequences.clear()
        self._stop_loop()

    def _start_loop(self) -> None:
        if self._is_running:
            return

        self._is_running = True
        self._loop()

    def _stop_loop(self) -> None:
        self._is_running = False
        if self._loop_id:
            self.root.after_cancel(self._loop_id)
            self._loop_id = None

    def _loop(self) -> None:
        if not self._is_running or not self._animations:
            self._stop_loop()
            return

        current_time = time.time() * 1000
        completed_ids = []

        for tween_id, tween in list(self._animations.items()):
            if self._step_tween(current_time, tween):
                completed_ids.append(tween_id)

        for tween_id in completed_ids:
            if tween_id in self._animations:
                del self._animations[tween_id]

        self._update_fps(current_time)

        if self._animations:
            self._loop_id = self.root.after(int(self._frame_time), self._loop)
        else:
            self._stop_loop()

    def _step_tween(self, current_time: float, tween: Tween) -> bool:
        if not tween._is_running:
            tween._start_time = current_time + tween.delay
            tween._is_running = True

        if current_time < tween._start_time:
            return False

        progress = min(1.0, (current_time - tween._start_time) / tween.duration)
        eased_progress = Easing.get(tween.easing)(progress)
        current_value = tween.start_value + (tween.end_value - tween.start_value) * eased_progress
        self._apply_tween_value(tween, current_value)
        self._notify_update(tween, current_value)

        if progress >= 1.0:
            tween._is_complete = True
            self._notify_complete(tween)
            return True

        return False

    def _apply_tween_value(self, tween: Tween, current_value: float) -> None:
        try:
            if hasattr(tween.target, "configure"):
                tween.target.configure(**{tween.property_name: current_value})
            elif hasattr(tween.target, tween.property_name):
                setattr(tween.target, tween.property_name, current_value)
        except Exception as exc:
            logger.debug("更新属性失败: %s", exc)

    def _notify_update(self, tween: Tween, current_value: float) -> None:
        if tween.on_update:
            try:
                tween.on_update(current_value)
            except Exception as exc:
                logger.error("更新回调失败: %s", exc)

    def _notify_complete(self, tween: Tween) -> None:
        if tween.on_complete:
            try:
                tween.on_complete()
            except Exception as exc:
                logger.error("完成回调失败: %s", exc)

    def _update_fps(self, current_time: float) -> None:
        self._frame_count += 1
        if current_time - self._last_fps_time * 1000 > 1000:
            self._current_fps = self._frame_count
            self._frame_count = 0
            self._last_fps_time = current_time / 1000

    def get_fps(self) -> int:
        """获取当前FPS"""
        return self._current_fps

    def get_active_count(self) -> int:
        """获取活动动画数量"""
        return len(self._animations)

    def destroy(self) -> None:
        """清理资源"""
        self.stop_all()
        AnimationEngine._instance = None


__all__ = ["AnimationEngine"]
