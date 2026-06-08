"""Compatibility entrypoint for GUI performance monitoring."""

from __future__ import annotations

from .performance_constants import (
    CRITICAL_MEMORY_MB,
    MAX_HISTORY_SIZE,
    MAX_SLOW_OPS_LOG,
    MONITOR_INTERVAL_MS,
    SLOW_OP_THRESHOLD_MS,
    WARNING_MEMORY_MB,
)
from .performance_facade import get_monitor, show_overlay, start_monitoring, stop_monitoring, timer
from .performance_models import (
    OperationSample,
    PerformanceLevel,
    PerformanceMetrics,
    SlowOperation,
)
from .performance_monitor import PerformanceMonitor
from .performance_overlay import PerformanceOverlay
from .performance_timer import PerformanceTimer

__all__ = [
    "CRITICAL_MEMORY_MB",
    "MAX_HISTORY_SIZE",
    "MAX_SLOW_OPS_LOG",
    "MONITOR_INTERVAL_MS",
    "SLOW_OP_THRESHOLD_MS",
    "WARNING_MEMORY_MB",
    "OperationSample",
    "PerformanceLevel",
    "PerformanceMetrics",
    "PerformanceMonitor",
    "PerformanceOverlay",
    "PerformanceTimer",
    "SlowOperation",
    "get_monitor",
    "show_overlay",
    "start_monitoring",
    "stop_monitoring",
    "timer",
]


if __name__ == "__main__":
    from .performance_demo import run_performance_demo

    run_performance_demo()
