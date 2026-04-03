"""GUI 运行时优化逻辑。

从 `app.py` 抽离低内存检测与处理逻辑，
减少主类复杂度，便于单元测试与后续演进。
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from .widgets.helpers import LOW_MEMORY_THRESHOLD_GB, get_available_memory_gb
from .widgets.toast_notification import ToastNotification


def check_memory_on_startup(gui: Any) -> None:
    """启动时检测内存，并在需要时触发提示。"""
    if gui.user_prefs.low_memory_mode or gui.user_prefs.low_memory_prompt_dismissed:
        return

    available_gb = get_available_memory_gb()
    if available_gb is None:
        logger.debug("无法检测系统内存（psutil 未安装）")
        return

    logger.info(f"系统可用内存: {available_gb:.2f} GB")
    if available_gb < LOW_MEMORY_THRESHOLD_GB:
        gui.root.after(1500, lambda: show_low_memory_warning(gui, available_gb))


def show_low_memory_warning(gui: Any, available_gb: float) -> None:
    """显示低内存警告。"""

    def on_enable() -> None:
        gui.user_prefs.low_memory_mode = True
        if hasattr(gui, "low_memory_var"):
            gui.low_memory_var.set(True)
        apply_low_memory_optimizations(gui)
        logger.info("✅ 已启用低内存模式")
        if hasattr(gui, "_toast_manager") and gui._toast_manager:
            gui._toast_manager.success("已启用低内存模式，应用将减少内存占用")
        else:
            ToastNotification(
                gui.root,
                "低内存模式",
                "已启用低内存模式，应用将减少内存占用",
                toast_type="success",
                duration_ms=3000,
            )

    def on_dismiss() -> None:
        gui.user_prefs.low_memory_prompt_dismissed = True
        logger.info("用户选择忽略低内存提示")

    ToastNotification(
        gui.root,
        "⚠️ 内存不足",
        f"检测到系统可用内存仅 {available_gb:.1f} GB（低于 {LOW_MEMORY_THRESHOLD_GB:.0f} GB）\n\n建议启用「低内存模式」以获得更好的体验。",
        toast_type="warning",
        duration_ms=0,
        show_buttons=True,
        on_confirm=on_enable,
        on_cancel=on_dismiss,
    )


def apply_low_memory_optimizations(gui: Any) -> None:
    """应用低内存模式优化。"""
    if hasattr(gui, "_log_handler") and gui._log_handler:
        gui._log_handler.set_low_memory_mode(True)

    gui._animation_running = False
    gui._low_memory_mode_active = True
    logger.debug("已应用低内存优化：减少日志缓存 (200行)、禁用动画效果")


def is_low_memory_mode(gui: Any) -> bool:
    """判断当前是否处于低内存模式。"""
    return getattr(gui, "_low_memory_mode_active", False) or gui.user_prefs.low_memory_mode
