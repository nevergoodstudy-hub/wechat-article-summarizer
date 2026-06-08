"""Facade helpers for GUI performance monitoring."""

from __future__ import annotations

import tkinter as tk

from .performance_monitor import PerformanceMonitor
from .performance_overlay import PerformanceOverlay
from .performance_timer import PerformanceTimer

_global_monitor: PerformanceMonitor | None = None


def get_monitor() -> PerformanceMonitor:
    """获取全局监控器"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def start_monitoring(**kwargs) -> None:
    """启动全局监控"""
    get_monitor().start_monitoring(**kwargs)


def stop_monitoring() -> None:
    """停止全局监控"""
    get_monitor().stop_monitoring()


def timer(name: str) -> PerformanceTimer:
    """获取计时器"""
    return get_monitor().timer(name)


def show_overlay(parent: tk.Misc, position: str = "top-right") -> PerformanceOverlay:
    """显示性能悬浮窗"""
    return PerformanceOverlay(parent, position)


__all__ = [
    "get_monitor",
    "show_overlay",
    "start_monitoring",
    "stop_monitoring",
    "timer",
]
