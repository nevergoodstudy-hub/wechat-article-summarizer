"""Manual demo for microinteraction effects."""

from __future__ import annotations

import tkinter as tk

from .i18n import tr
from .microinteractions_loading import SkeletonLoader, Spinner
from .microinteractions_manager import MicroInteractions


def run_microinteractions_demo() -> None:
    """Run a local visual demo for development."""
    root = tk.Tk()
    root.title(tr("微交互动画测试"))
    root.geometry("800x600")
    root.configure(bg="#121212")

    tk.Label(
        root,
        text=tr("微交互动画演示"),
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 16, "bold"),
    ).pack(pady=20)

    ripple_btn = tk.Label(
        root,
        text=tr("点击查看水波纹效果"),
        bg="#3b82f6",
        fg="#ffffff",
        font=("Segoe UI", 12),
        padx=20,
        pady=12,
        cursor="hand2",
    )
    ripple_btn.pack(pady=10)
    MicroInteractions.add_ripple(ripple_btn)

    scale_btn = tk.Label(
        root,
        text=tr("点击查看缩放效果"),
        bg="#10b981",
        fg="#ffffff",
        font=("Segoe UI", 12),
        padx=20,
        pady=12,
        cursor="hand2",
    )
    scale_btn.pack(pady=10)
    MicroInteractions.add_scale(scale_btn)

    hover_frame = tk.Frame(root, bg="#2a2a2a", padx=20, pady=12)
    hover_frame.pack(pady=10)
    tk.Label(
        hover_frame,
        text=tr("悬停查看上浮效果"),
        bg="#2a2a2a",
        fg="#e5e5e5",
        font=("Segoe UI", 12),
    ).pack()
    MicroInteractions.add_hover(hover_frame, hover_bg="#3a3a3a", normal_bg="#2a2a2a")

    tk.Label(
        root,
        text=tr("Skeleton 骨架屏:"),
        bg="#121212",
        fg="#808080",
        font=("Segoe UI", 10),
    ).pack(pady=(20, 5))

    skeleton = SkeletonLoader(root, width=300, height=20, bg_color="#2a2a2a")
    skeleton.pack(pady=5)

    tk.Label(
        root,
        text=tr("Spinner 加载指示器:"),
        bg="#121212",
        fg="#808080",
        font=("Segoe UI", 10),
    ).pack(pady=(20, 5))

    spinner = Spinner(root, size=40, color="#3b82f6", bg="#121212")
    spinner.pack(pady=5)

    pulse_label = tk.Label(
        root,
        text=tr("  脉冲效果  "),
        bg="#3b82f6",
        fg="#ffffff",
        font=("Segoe UI", 12),
        padx=20,
        pady=10,
    )
    pulse_label.pack(pady=20)
    pulse = MicroInteractions.add_pulse(pulse_label, "#3b82f6", "#60a5fa")
    pulse.start()

    root.mainloop()


__all__ = ["run_microinteractions_demo"]
