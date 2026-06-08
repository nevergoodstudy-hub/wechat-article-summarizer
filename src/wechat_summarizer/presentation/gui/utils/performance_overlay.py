"""Performance overlay window."""

from __future__ import annotations

import tkinter as tk

from .i18n import tr
from .performance_models import PerformanceLevel
from .performance_monitor import PerformanceMonitor


class PerformanceOverlay(tk.Toplevel):
    """性能监控悬浮窗"""

    def __init__(self, parent: tk.Misc, position: str = "top-right", **kwargs):
        super().__init__(parent)

        self._parent = parent
        self._position = position
        self._monitor = PerformanceMonitor()

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.85)
        self.configure(bg="#1a1a1a")
        self._setup_ui()
        self._position_window()
        self._start_update()

    def _setup_ui(self) -> None:
        self._container = tk.Frame(self, bg="#1a1a1a", padx=12, pady=8)
        self._container.pack()
        self._build_title_bar()
        tk.Frame(self._container, bg="#333333", height=1).pack(fill=tk.X, pady=4)
        self._build_metrics()
        self._level_label = tk.Label(
            self._container,
            text=tr("● 优秀"),
            bg="#1a1a1a",
            fg="#10b981",
            font=("Segoe UI", 9),
        )
        self._level_label.pack(pady=(4, 0))
        self._container.bind("<Button-1>", self._start_drag)
        self._container.bind("<B1-Motion>", self._do_drag)

    def _build_title_bar(self) -> None:
        title_frame = tk.Frame(self._container, bg="#1a1a1a")
        title_frame.pack(fill=tk.X)

        tk.Label(
            title_frame,
            text=tr("📊 性能监控"),
            bg="#1a1a1a",
            fg="#3b82f6",
            font=("Segoe UI", 10, "bold"),
        ).pack(side=tk.LEFT)

        close_btn = tk.Label(
            title_frame,
            text="×",
            bg="#1a1a1a",
            fg="#808080",
            font=("Segoe UI", 14),
            cursor="hand2",
        )
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda _event: self.destroy())

    def _build_metrics(self) -> None:
        metrics_frame = tk.Frame(self._container, bg="#1a1a1a")
        metrics_frame.pack(fill=tk.X)
        self._fps_label = self._build_metric_row(metrics_frame, "FPS", "#10b981", 6)
        self._mem_label = self._build_metric_row(metrics_frame, "内存", "#f59e0b", 8)
        self._cpu_label = self._build_metric_row(metrics_frame, "CPU", "#3b82f6", 6)

    def _build_metric_row(
        self,
        metrics_frame: tk.Frame,
        label: str,
        color: str,
        value_width: int,
    ) -> tk.Label:
        frame = tk.Frame(metrics_frame, bg="#1a1a1a")
        frame.pack(fill=tk.X, pady=2)

        tk.Label(
            frame,
            text=label,
            bg="#1a1a1a",
            fg="#808080",
            font=("Segoe UI", 9),
            width=8,
            anchor="w",
        ).pack(side=tk.LEFT)

        value_label = tk.Label(
            frame,
            text="--",
            bg="#1a1a1a",
            fg=color,
            font=("Consolas", 11, "bold"),
            width=value_width,
            anchor="e",
        )
        value_label.pack(side=tk.RIGHT)
        return value_label

    def _position_window(self) -> None:
        self.update_idletasks()

        width = self.winfo_width()
        height = self.winfo_height()
        parent_x = self._parent.winfo_rootx()
        parent_y = self._parent.winfo_rooty()
        parent_w = self._parent.winfo_width()
        parent_h = self._parent.winfo_height()
        padding = 10

        if self._position == "top-left":
            x = parent_x + padding
            y = parent_y + padding
        elif self._position == "top-right":
            x = parent_x + parent_w - width - padding
            y = parent_y + padding
        elif self._position == "bottom-left":
            x = parent_x + padding
            y = parent_y + parent_h - height - padding
        else:
            x = parent_x + parent_w - width - padding
            y = parent_y + parent_h - height - padding

        self.geometry(f"+{x}+{y}")

    def _start_drag(self, event) -> None:
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_drag(self, event) -> None:
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")

    def _start_update(self) -> None:
        self._update_metrics()

    def _update_metrics(self) -> None:
        if not self.winfo_exists():
            return

        metrics = self._monitor.get_current_metrics()
        level = self._monitor.get_performance_level()
        self._fps_label.configure(text=f"{metrics.fps:.0f}", fg=self._fps_color(metrics.fps))
        self._mem_label.configure(
            text=f"{metrics.memory_mb:.0f} MB",
            fg=self._memory_color(metrics.memory_mb),
        )
        self._cpu_label.configure(
            text=f"{metrics.cpu_percent:.0f}%",
            fg=self._cpu_color(metrics.cpu_percent),
        )
        text, color = self._level_config(level)
        self._level_label.configure(text=text, fg=color)
        self.after(500, self._update_metrics)

    def _fps_color(self, fps: float) -> str:
        return "#10b981" if fps >= 55 else ("#f59e0b" if fps >= 30 else "#ef4444")

    def _memory_color(self, memory_mb: float) -> str:
        return "#10b981" if memory_mb < 200 else ("#f59e0b" if memory_mb < 500 else "#ef4444")

    def _cpu_color(self, cpu_percent: float) -> str:
        return "#10b981" if cpu_percent < 50 else ("#f59e0b" if cpu_percent < 80 else "#ef4444")

    def _level_config(self, level: PerformanceLevel) -> tuple[str, str]:
        level_config = {
            PerformanceLevel.EXCELLENT: (tr("● 优秀"), "#10b981"),
            PerformanceLevel.GOOD: (tr("● 良好"), "#3b82f6"),
            PerformanceLevel.FAIR: (tr("● 一般"), "#f59e0b"),
            PerformanceLevel.POOR: (tr("● 较差"), "#ef4444"),
        }
        return level_config.get(level, (tr("● 未知"), "#808080"))


__all__ = ["PerformanceOverlay"]
