"""Core GUI performance monitor."""

from __future__ import annotations

import logging
import os
import threading
import time
from collections import deque
from collections.abc import Callable
from datetime import datetime
from typing import Any

import psutil

from .performance_constants import (
    MAX_HISTORY_SIZE,
    MAX_SLOW_OPS_LOG,
    MONITOR_INTERVAL_MS,
    WARNING_MEMORY_MB,
)
from .performance_models import (
    OperationSample,
    PerformanceLevel,
    PerformanceMetrics,
    SlowOperation,
)
from .performance_timer import PerformanceTimer

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器"""

    _instance: PerformanceMonitor | None = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self._initialized = True
        self._is_monitoring = False
        self._monitor_thread: threading.Thread | None = None
        self._metrics_history: deque[PerformanceMetrics] = deque(maxlen=MAX_HISTORY_SIZE)
        self._current_metrics = PerformanceMetrics()
        self._slow_operations: deque[SlowOperation] = deque(maxlen=MAX_SLOW_OPS_LOG)
        self._operation_samples: deque[OperationSample] = deque(maxlen=MAX_SLOW_OPS_LOG)
        self._frame_times: deque[float] = deque(maxlen=60)
        self._last_frame_time = time.perf_counter()
        self._process = psutil.Process(os.getpid())
        self._on_metrics_update: Callable[[PerformanceMetrics], None] | None = None
        self._on_slow_operation: Callable[[SlowOperation], None] | None = None
        self._on_memory_warning: Callable[[float], None] | None = None
        self._lock = threading.Lock()

    def start_monitoring(
        self,
        on_metrics_update: Callable[[PerformanceMetrics], None] | None = None,
        on_slow_operation: Callable[[SlowOperation], None] | None = None,
        on_memory_warning: Callable[[float], None] | None = None,
    ) -> None:
        """启动监控"""
        if self._is_monitoring:
            return

        self._on_metrics_update = on_metrics_update
        self._on_slow_operation = on_slow_operation
        self._on_memory_warning = on_memory_warning
        self._is_monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("性能监控已启动")

    def stop_monitoring(self) -> None:
        """停止监控"""
        self._is_monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)
            self._monitor_thread = None

        logger.info("性能监控已停止")

    def _monitor_loop(self) -> None:
        while self._is_monitoring:
            try:
                self._collect_metrics()
                time.sleep(MONITOR_INTERVAL_MS / 1000)
            except Exception as exc:
                logger.error("监控循环错误: %s", exc)

    def _collect_metrics(self) -> None:
        current_time = time.perf_counter()
        frame_time = (current_time - self._last_frame_time) * 1000
        self._last_frame_time = current_time
        self._frame_times.append(frame_time)

        avg_frame_time = (
            sum(self._frame_times) / len(self._frame_times) if self._frame_times else 16.67
        )
        fps = 1000 / avg_frame_time if avg_frame_time > 0 else 0
        memory_mb, cpu_percent = self._collect_process_metrics()

        metrics = PerformanceMetrics(
            fps=fps,
            frame_time_ms=avg_frame_time,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
        )

        with self._lock:
            self._current_metrics = metrics
            self._metrics_history.append(metrics)

        self._notify_metrics_update(metrics)
        self._notify_memory_warning(memory_mb)

    def _collect_process_metrics(self) -> tuple[float, float]:
        try:
            memory_info = self._process.memory_info()
            return memory_info.rss / (1024 * 1024), self._process.cpu_percent()
        except Exception:
            return 0, 0

    def _notify_metrics_update(self, metrics: PerformanceMetrics) -> None:
        if self._on_metrics_update:
            try:
                self._on_metrics_update(metrics)
            except Exception as exc:
                logger.error("指标更新回调失败: %s", exc)

    def _notify_memory_warning(self, memory_mb: float) -> None:
        if memory_mb >= WARNING_MEMORY_MB and self._on_memory_warning:
            try:
                self._on_memory_warning(memory_mb)
            except Exception as exc:
                logger.error("内存警告回调失败: %s", exc)

    def _record_slow_operation(self, name: str, duration_ms: float) -> None:
        op = SlowOperation(name=name, duration_ms=duration_ms)

        with self._lock:
            self._slow_operations.append(op)

        logger.warning("慢操作: %s (%.1fms)", name, duration_ms)

        if self._on_slow_operation:
            try:
                self._on_slow_operation(op)
            except Exception as exc:
                logger.error("慢操作回调失败: %s", exc)

    def record_operation_sample(self, name: str, duration_ms: float) -> OperationSample:
        """Record a measured GUI operation with current process metrics."""
        memory_mb, cpu_percent = self._collect_process_metrics()
        sample = OperationSample(
            name=name,
            duration_ms=duration_ms,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
        )

        with self._lock:
            self._operation_samples.append(sample)

        if duration_ms > 0:
            logger.debug(
                "性能采样: %s (%.1fms, %.1fMB, %.1f%% CPU)",
                name,
                duration_ms,
                memory_mb,
                cpu_percent,
            )

        return sample

    def record_frame(self) -> None:
        """记录帧(用于手动FPS计算)"""
        current_time = time.perf_counter()
        frame_time = (current_time - self._last_frame_time) * 1000
        self._last_frame_time = current_time
        self._frame_times.append(frame_time)

    def timer(self, name: str) -> PerformanceTimer:
        """获取计时器"""
        return PerformanceTimer(name, self)

    def get_current_metrics(self) -> PerformanceMetrics:
        """获取当前指标"""
        with self._lock:
            return self._current_metrics

    def get_metrics_history(self) -> list[PerformanceMetrics]:
        """获取历史指标"""
        with self._lock:
            return list(self._metrics_history)

    def get_slow_operations(self) -> list[SlowOperation]:
        """获取慢操作记录"""
        with self._lock:
            return list(self._slow_operations)

    def get_operation_samples(self) -> list[OperationSample]:
        """获取关键操作采样记录"""
        with self._lock:
            return list(self._operation_samples)

    def get_performance_level(self) -> PerformanceLevel:
        """获取性能等级"""
        metrics = self._current_metrics

        if metrics.fps >= 55 and metrics.memory_mb < 200:
            return PerformanceLevel.EXCELLENT
        if metrics.fps >= 30 and metrics.memory_mb < 500:
            return PerformanceLevel.GOOD
        if metrics.fps >= 20 and metrics.memory_mb < 800:
            return PerformanceLevel.FAIR
        return PerformanceLevel.POOR

    def generate_report(self) -> dict[str, Any]:
        """生成性能报告(安全脱敏)"""
        with self._lock:
            history = list(self._metrics_history)
            slow_ops = list(self._slow_operations)
            operation_samples = list(self._operation_samples)

        if not history and not operation_samples:
            return {"error": "无数据"}

        fps_values = [metric.fps for metric in history] or [0.0]
        memory_values = [metric.memory_mb for metric in history] or [
            sample.memory_mb for sample in operation_samples
        ]
        duration_values = [sample.duration_ms for sample in operation_samples]

        report: dict[str, Any] = {
            "generated_at": datetime.now().isoformat(),
            "duration_seconds": len(history) * MONITOR_INTERVAL_MS / 1000,
            "fps": {
                "avg": round(sum(fps_values) / len(fps_values), 1),
                "min": round(min(fps_values), 1),
                "max": round(max(fps_values), 1),
            },
            "memory_mb": {
                "avg": round(sum(memory_values) / len(memory_values), 1),
                "min": round(min(memory_values), 1),
                "max": round(max(memory_values), 1),
            },
            "slow_operations_count": len(slow_ops),
            "operation_samples_count": len(operation_samples),
            "performance_level": self.get_performance_level().value,
        }
        if duration_values:
            report["operation_duration_ms"] = {
                "avg": round(sum(duration_values) / len(duration_values), 1),
                "min": round(min(duration_values), 1),
                "max": round(max(duration_values), 1),
            }
        return report

    def clear_history(self) -> None:
        """清空历史记录"""
        with self._lock:
            self._metrics_history.clear()
            self._slow_operations.clear()
            self._operation_samples.clear()


__all__ = ["PerformanceMonitor"]
