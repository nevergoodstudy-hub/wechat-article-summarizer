"""Manual demo for responsive GUI layout utilities."""

from __future__ import annotations

import tkinter as tk

from .responsive_breakpoints import BreakpointManager
from .responsive_grid import ResponsiveGrid
from .responsive_models import Breakpoint


def run_demo() -> None:
    """Run the responsive layout demo."""
    root = tk.Tk()
    root.title("响应式布局测试")
    root.geometry("1200x800")
    root.configure(bg="#121212")

    bp_manager = BreakpointManager(root)

    def on_bp_change(bp: Breakpoint, width: int, height: int) -> None:
        info_label.config(text=f"断点: {bp.value} | 宽度: {width}px | 高度: {height}px")

    bp_manager.on_breakpoint_change(on_bp_change)

    info_label = tk.Label(
        root,
        text="调整窗口大小查看断点变化",
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 14),
    )
    info_label.pack(pady=20)

    grid = ResponsiveGrid(root, bp_manager, gap=20, bg="#121212")
    grid.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"]
    for i in range(12):
        card = tk.Frame(grid, bg=colors[i % len(colors)])
        tk.Label(
            card,
            text=f"Card {i + 1}",
            bg=colors[i % len(colors)],
            fg="#ffffff",
            font=("Segoe UI", 12, "bold"),
        ).pack(expand=True)
        grid.add_item(card)

    root.mainloop()


if __name__ == "__main__":
    run_demo()
