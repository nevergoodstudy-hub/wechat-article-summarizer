"""
性能监控系统 (Performance Monitor)
实时监控GUI性能指标

功能特性:
- FPS实时监测
- 内存占用追踪
- 慢操作警告(>100ms)
- 性能报告生成
- 性能指标可视化

安全措施:
- 监控数据不含敏感信息
- 内存使用限制
- 日志脱敏处理
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import tkinter as tk
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import psutil

logger = logging.getLogger(__name__)


# 安全限制
MAX_HISTORY_SIZE = 1000  # 最大历史记录数
MAX_SLOW_OPS_LOG = 100  # 最大慢操作记录数
SLOW_OP_THRESHOLD_MS = 100  # 慢操作阈值
WARNING_MEMORY_MB = 500  # 内存警告阈值
CRITICAL_MEMORY_MB = 1000  # 内存临界阈值
MONITOR_INTERVAL_MS = 100  # 监控间隔


class PerformanceLevel(Enum):
    """性能等级"""

    EXCELLENT = "excellent"  # 优秀 (FPS >= 55, Memory < 200MB)
    GOOD = "good"  # 良好 (FPS >= 30, Memory < 500MB)
    FAIR = "fair"  # 一般 (FPS >= 20, Memory < 800MB)
    POOR = "poor"  # 较差 (FPS < 20 or Memory >= 800MB)


@dataclass
class PerformanceMetrics:
    """性能指标"""

    fps: float = 0.0
    frame_time_ms: float = 0.0
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """转为字典(不含敏感信息)"""
        return {
            "fps": round(self.fps, 1),
            "frame_time_ms": round(self.frame_time_ms, 2),
            "memory_mb": round(self.memory_mb, 1),
            "cpu_percent": round(self.cpu_percent, 1),
            "timestamp": self.timestamp,
        }


@dataclass
class SlowOperation:
    """慢操作记录"""

    name: str
    duration_ms: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name[:50],  # 限制名称长度
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": self.timestamp,
        }


class PerformanceTimer:
    """性能计时器(上下文管理器)"""

    def __init__(self, name: str, monitor: PerformanceMonitor):
        self.name = name
        self.monitor = monitor
        self.start_time = 0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.perf_counter() - self.start_time) * 1000
        if duration > SLOW_OP_THRESHOLD_MS:
            self.monitor._record_slow_operation(self.name, duration)
        return False


class PerformanceMonitor:
    """性能监控器

    单例模式，全局监控应用性能
    """

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

        # 监控状态
        self._is_monitoring = False
        self._monitor_thread: threading.Thread | None = None

        # 性能数据
        self._metrics_history: deque[PerformanceMetrics] = deque(maxlen=MAX_HISTORY_SIZE)
        self._current_metrics = PerformanceMetrics()
        self._slow_operations: deque[SlowOperation] = deque(maxlen=MAX_SLOW_OPS_LOG)

        # FPS计算
        self._frame_times: deque[float] = deque(maxlen=60)
        self._last_frame_time = time.perf_counter()

        # 进程信息
        self._process = psutil.Process(os.getpid())

        # 回调
        self._on_metrics_update: Callable[[PerformanceMetrics], None] | None = None
        self._on_slow_operation: Callable[[SlowOperation], None] | None = None
        self._on_memory_warning: Callable[[float], None] | None = None

        # 锁
        self._lock = threading.Lock()

    def start_monitoring(
        self,
        on_metrics_update: Callable[[PerformanceMetrics], None] | None = None,
        on_slow_operation: Callable[[SlowOperation], None] | None = None,
        on_memory_warning: Callable[[float], None] | None = None,
    ):
        """启动监控

        Args:
            on_metrics_update: 指标更新回调
            on_slow_operation: 慢操作回调
            on_memory_warning: 内存警告回调
        """
        if self._is_monitoring:
            return

        self._on_metrics_update = on_metrics_update
        self._on_slow_operation = on_slow_operation
        self._on_memory_warning = on_memory_warning

        self._is_monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        logger.info("性能监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        self._is_monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)
            self._monitor_thread = None

        logger.info("性能监控已停止")

    def _monitor_loop(self):
        """监控循环"""
        while self._is_monitoring:
            try:
                self._collect_metrics()
                time.sleep(MONITOR_INTERVAL_MS / 1000)
            except Exception as e:
                logger.error(f"监控循环错误: {e}")

    def _collect_metrics(self):
        """收集性能指标"""
        # 计算FPS
        current_time = time.perf_counter()
        frame_time = (current_time - self._last_frame_time) * 1000
        self._last_frame_time = current_time
        self._frame_times.append(frame_time)

        avg_frame_time = (
            sum(self._frame_times) / len(self._frame_times) if self._frame_times else 16.67
        )
        fps = 1000 / avg_frame_time if avg_frame_time > 0 else 0

        # 内存和CPU
        try:
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            cpu_percent = self._process.cpu_percent()
        except Exception:
            memory_mb = 0
            cpu_percent = 0

        # 创建指标
        metrics = PerformanceMetrics(
            fps=fps, frame_time_ms=avg_frame_time, memory_mb=memory_mb, cpu_percent=cpu_percent
        )

        with self._lock:
            self._current_metrics = metrics
            self._metrics_history.append(metrics)

        # 回调
        if self._on_metrics_update:
            try:
                self._on_metrics_update(metrics)
            except Exception as e:
                logger.error(f"指标更新回调失败: {e}")

        # 内存警告
        if memory_mb >= WARNING_MEMORY_MB and self._on_memory_warning:
            try:
                self._on_memory_warning(memory_mb)
            except Exception as e:
                logger.error(f"内存警告回调失败: {e}")

    def _record_slow_operation(self, name: str, duration_ms: float):
        """记录慢操作"""
        op = SlowOperation(name=name, duration_ms=duration_ms)

        with self._lock:
            self._slow_operations.append(op)

        logger.warning(f"慢操作: {name} ({duration_ms:.1f}ms)")

        if self._on_slow_operation:
            try:
                self._on_slow_operation(op)
            except Exception as e:
                logger.error(f"慢操作回调失败: {e}")

    def record_frame(self):
        """记录帧(用于手动FPS计算)"""
        current_time = time.perf_counter()
        frame_time = (current_time - self._last_frame_time) * 1000
        self._last_frame_time = current_time
        self._frame_times.append(frame_time)

    def timer(self, name: str) -> PerformanceTimer:
        """获取计时器

        Usage:
            with monitor.timer("operation"):
                do_something()
        """
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

    def get_performance_level(self) -> PerformanceLevel:
        """获取性能等级"""
        metrics = self._current_metrics

        if metrics.fps >= 55 and metrics.memory_mb < 200:
            return PerformanceLevel.EXCELLENT
        elif metrics.fps >= 30 and metrics.memory_mb < 500:
            return PerformanceLevel.GOOD
        elif metrics.fps >= 20 and metrics.memory_mb < 800:
            return PerformanceLevel.FAIR
        else:
            return PerformanceLevel.POOR

    def generate_report(self) -> dict[str, Any]:
        """生成性能报告(安全脱敏)"""
        with self._lock:
            history = list(self._metrics_history)
            slow_ops = list(self._slow_operations)

        if not history:
            return {"error": "无数据"}

        # 计算统计
        fps_values = [m.fps for m in history]
        memory_values = [m.memory_mb for m in history]

        report = {
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
            "performance_level": self.get_performance_level().value,
        }

        return report

    def clear_history(self):
        """清空历史记录"""
        with self._lock:
            self._metrics_history.clear()
            self._slow_operations.clear()


class PerformanceOverlay(tk.Toplevel):
    """性能监控悬浮窗"""

    def __init__(self, parent: tk.Misc, position: str = "top-right", **kwargs):
        """
        Args:
            parent: 父窗口
            position: 位置 (top-left, top-right, bottom-left, bottom-right)
        """
        super().__init__(parent)

        self._parent = parent
        self._position = position
        self._monitor = PerformanceMonitor()

        # 窗口配置
        self.overrideredirect(True)  # 无边框
        self.attributes("-topmost", True)  # 置顶
        self.attributes("-alpha", 0.85)  # 半透明

        self.configure(bg="#1a1a1a")

        self._setup_ui()
        self._position_window()
        self._start_update()

    def _setup_ui(self):
        """构建UI"""
        # 容器
        self._container = tk.Frame(self, bg="#1a1a1a", padx=12, pady=8)
        self._container.pack()

        # 标题栏
        title_frame = tk.Frame(self._container, bg="#1a1a1a")
        title_frame.pack(fill=tk.X)

        tk.Label(
            title_frame,
            text="📊 性能监控",
            bg="#1a1a1a",
            fg="#3b82f6",
            font=("Segoe UI", 10, "bold"),
        ).pack(side=tk.LEFT)

        # 关闭按钮
        close_btn = tk.Label(
            title_frame, text="×", bg="#1a1a1a", fg="#808080", font=("Segoe UI", 14), cursor="hand2"
        )
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda e: self.destroy())

        # 分隔线
        tk.Frame(self._container, bg="#333333", height=1).pack(fill=tk.X, pady=4)

        # 指标显示
        metrics_frame = tk.Frame(self._container, bg="#1a1a1a")
        metrics_frame.pack(fill=tk.X)

        # FPS
        fps_frame = tk.Frame(metrics_frame, bg="#1a1a1a")
        fps_frame.pack(fill=tk.X, pady=2)

        tk.Label(
            fps_frame,
            text="FPS",
            bg="#1a1a1a",
            fg="#808080",
            font=("Segoe UI", 9),
            width=8,
            anchor="w",
        ).pack(side=tk.LEFT)

        self._fps_label = tk.Label(
            fps_frame,
            text="--",
            bg="#1a1a1a",
            fg="#10b981",
            font=("Consolas", 11, "bold"),
            width=6,
            anchor="e",
        )
        self._fps_label.pack(side=tk.RIGHT)

        # 内存
        mem_frame = tk.Frame(metrics_frame, bg="#1a1a1a")
        mem_frame.pack(fill=tk.X, pady=2)

        tk.Label(
            mem_frame,
            text="内存",
            bg="#1a1a1a",
            fg="#808080",
            font=("Segoe UI", 9),
            width=8,
            anchor="w",
        ).pack(side=tk.LEFT)

        self._mem_label = tk.Label(
            mem_frame,
            text="--",
            bg="#1a1a1a",
            fg="#f59e0b",
            font=("Consolas", 11, "bold"),
            width=8,
            anchor="e",
        )
        self._mem_label.pack(side=tk.RIGHT)

        # CPU
        cpu_frame = tk.Frame(metrics_frame, bg="#1a1a1a")
        cpu_frame.pack(fill=tk.X, pady=2)

        tk.Label(
            cpu_frame,
            text="CPU",
            bg="#1a1a1a",
            fg="#808080",
            font=("Segoe UI", 9),
            width=8,
            anchor="w",
        ).pack(side=tk.LEFT)

        self._cpu_label = tk.Label(
            cpu_frame,
            text="--",
            bg="#1a1a1a",
            fg="#3b82f6",
            font=("Consolas", 11, "bold"),
            width=6,
            anchor="e",
        )
        self._cpu_label.pack(side=tk.RIGHT)

        # 性能等级
        self._level_label = tk.Label(
            self._container, text="● 优秀", bg="#1a1a1a", fg="#10b981", font=("Segoe UI", 9)
        )
        self._level_label.pack(pady=(4, 0))

        # 拖拽支持
        self._container.bind("<Button-1>", self._start_drag)
        self._container.bind("<B1-Motion>", self._do_drag)

    def _position_window(self):
        """定位窗口"""
        self.update_idletasks()

        w = self.winfo_width()
        h = self.winfo_height()

        parent_x = self._parent.winfo_rootx()
        parent_y = self._parent.winfo_rooty()
        parent_w = self._parent.winfo_width()
        parent_h = self._parent.winfo_height()

        padding = 10

        if self._position == "top-left":
            x = parent_x + padding
            y = parent_y + padding
        elif self._position == "top-right":
            x = parent_x + parent_w - w - padding
            y = parent_y + padding
        elif self._position == "bottom-left":
            x = parent_x + padding
            y = parent_y + parent_h - h - padding
        else:  # bottom-right
            x = parent_x + parent_w - w - padding
            y = parent_y + parent_h - h - padding

        self.geometry(f"+{x}+{y}")

    def _start_drag(self, event):
        """开始拖拽"""
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_drag(self, event):
        """执行拖拽"""
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")

    def _start_update(self):
        """开始更新"""
        self._update_metrics()

    def _update_metrics(self):
        """更新指标显示"""
        if not self.winfo_exists():
            return

        metrics = self._monitor.get_current_metrics()
        level = self._monitor.get_performance_level()

        # 更新FPS
        fps_color = (
            "#10b981" if metrics.fps >= 55 else ("#f59e0b" if metrics.fps >= 30 else "#ef4444")
        )
        self._fps_label.configure(text=f"{metrics.fps:.0f}", fg=fps_color)

        # 更新内存
        mem_color = (
            "#10b981"
            if metrics.memory_mb < 200
            else ("#f59e0b" if metrics.memory_mb < 500 else "#ef4444")
        )
        self._mem_label.configure(text=f"{metrics.memory_mb:.0f} MB", fg=mem_color)

        # 更新CPU
        cpu_color = (
            "#10b981"
            if metrics.cpu_percent < 50
            else ("#f59e0b" if metrics.cpu_percent < 80 else "#ef4444")
        )
        self._cpu_label.configure(text=f"{metrics.cpu_percent:.0f}%", fg=cpu_color)

        # 更新等级
        level_config = {
            PerformanceLevel.EXCELLENT: ("● 优秀", "#10b981"),
            PerformanceLevel.GOOD: ("● 良好", "#3b82f6"),
            PerformanceLevel.FAIR: ("● 一般", "#f59e0b"),
            PerformanceLevel.POOR: ("● 较差", "#ef4444"),
        }
        text, color = level_config.get(level, ("● 未知", "#808080"))
        self._level_label.configure(text=text, fg=color)

        # 继续更新
        self.after(500, self._update_metrics)


# 便捷函数
_global_monitor: PerformanceMonitor | None = None


def get_monitor() -> PerformanceMonitor:
    """获取全局监控器"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def start_monitoring(**kwargs):
    """启动全局监控"""
    get_monitor().start_monitoring(**kwargs)


def stop_monitoring():
    """停止全局监控"""
    get_monitor().stop_monitoring()


def timer(name: str) -> PerformanceTimer:
    """获取计时器"""
    return get_monitor().timer(name)


def show_overlay(parent: tk.Misc, position: str = "top-right") -> PerformanceOverlay:
    """显示性能悬浮窗"""
    return PerformanceOverlay(parent, position)


# 使用示例
if __name__ == "__main__":
    root = tk.Tk()
    root.title("性能监控测试")
    root.geometry("800x600")
    root.configure(bg="#121212")

    # 启动监控
    monitor = PerformanceMonitor()
    monitor.start_monitoring()

    # 主内容
    main_frame = tk.Frame(root, bg="#121212")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    tk.Label(
        main_frame,
        text="性能监控系统\n\n功能:\n• FPS实时监测\n• 内存占用追踪\n• CPU使用率\n• 慢操作警告\n• 性能报告生成",
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 14),
        justify=tk.LEFT,
    ).pack(pady=20)

    # 测试按钮
    def simulate_slow_op():
        with monitor.timer("测试慢操作"):
            time.sleep(0.15)

    def show_report():
        report = monitor.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))

    btn_frame = tk.Frame(main_frame, bg="#121212")
    btn_frame.pack(pady=20)

    tk.Button(
        btn_frame,
        text="模拟慢操作",
        bg="#3b82f6",
        fg="#ffffff",
        font=("Segoe UI", 11),
        relief=tk.FLAT,
        command=simulate_slow_op,
    ).pack(side=tk.LEFT, padx=5)

    tk.Button(
        btn_frame,
        text="生成报告",
        bg="#10b981",
        fg="#ffffff",
        font=("Segoe UI", 11),
        relief=tk.FLAT,
        command=show_report,
    ).pack(side=tk.LEFT, padx=5)

    # 显示悬浮窗
    overlay = PerformanceOverlay(root, position="top-right")

    def on_close():
        monitor.stop_monitoring()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
