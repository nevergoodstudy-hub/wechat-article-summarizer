"""Context timer for GUI performance monitoring."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Literal

from .performance_constants import SLOW_OP_THRESHOLD_MS

if TYPE_CHECKING:
    from .performance_monitor import PerformanceMonitor


class PerformanceTimer:
    """性能计时器(上下文管理器)"""

    def __init__(self, name: str, monitor: PerformanceMonitor):
        self.name = name
        self.monitor = monitor
        self.start_time = 0.0

    def __enter__(self) -> PerformanceTimer:
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> Literal[False]:
        duration = (time.perf_counter() - self.start_time) * 1000
        self.monitor.record_operation_sample(self.name, duration)
        if duration > SLOW_OP_THRESHOLD_MS:
            self.monitor._record_slow_operation(self.name, duration)
        return False


__all__ = ["PerformanceTimer"]
