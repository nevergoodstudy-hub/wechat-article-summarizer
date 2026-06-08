"""Manual demo for GUI performance monitoring."""

from __future__ import annotations

import json
import time
import tkinter as tk

from .performance_monitor import PerformanceMonitor
from .performance_overlay import PerformanceOverlay


def run_performance_demo() -> None:
    """Run the manual performance monitor demo."""
    root = tk.Tk()
    root.title("性能监控测试")
    root.geometry("800x600")
    root.configure(bg="#121212")

    monitor = PerformanceMonitor()
    monitor.start_monitoring()
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

    def simulate_slow_op() -> None:
        with monitor.timer("测试慢操作"):
            time.sleep(0.15)

    def show_report() -> None:
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

    PerformanceOverlay(root, position="top-right")

    def on_close() -> None:
        monitor.stop_monitoring()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


__all__ = ["run_performance_demo"]
