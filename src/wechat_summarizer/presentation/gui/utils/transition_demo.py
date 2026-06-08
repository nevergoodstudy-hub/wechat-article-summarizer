"""Manual smoke demo for page transitions."""

from __future__ import annotations

import tkinter as tk
from functools import partial

from .transition_models import EasingFunction, TransitionConfig, TransitionType
from .transition_router import PageRouter


def run_demo() -> None:
    """Run a small transition demo window."""
    root = tk.Tk()
    root.title("页面切换动画测试")
    root.geometry("800x600")
    root.configure(bg="#121212")

    container = tk.Frame(root, bg="#121212")
    container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    pages = {}
    colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"]

    for index, color in enumerate(colors):
        page = tk.Frame(container, bg=color)
        tk.Label(
            page,
            text=f"页面 {index + 1}",
            bg=color,
            fg="#ffffff",
            font=("Segoe UI", 24, "bold"),
        ).pack(expand=True)
        pages[f"page{index + 1}"] = page

    router = PageRouter(
        container,
        TransitionConfig(
            type=TransitionType.SLIDE_LEFT,
            duration=400,
            easing=EasingFunction.EASE_OUT_CUBIC,
        ),
    )

    for route, page in pages.items():
        router.register_page(route, page)

    router.navigate_to("page1", TransitionType.NONE)

    btn_frame = tk.Frame(root, bg="#121212")
    btn_frame.pack(pady=10)

    transitions = [
        ("Fade", TransitionType.FADE),
        ("Slide Left", TransitionType.SLIDE_LEFT),
        ("Slide Up", TransitionType.SLIDE_UP),
        ("Scale", TransitionType.SCALE),
    ]
    current_page_idx = [0]

    def next_page(trans_type: TransitionType) -> None:
        current_page_idx[0] = (current_page_idx[0] + 1) % 4
        router.navigate_to(f"page{current_page_idx[0] + 1}", trans_type)

    for name, trans_type in transitions:
        tk.Button(
            btn_frame,
            text=name,
            command=partial(next_page, trans_type),
            bg="#333333",
            fg="#ffffff",
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            padx=15,
            pady=8,
        ).pack(side=tk.LEFT, padx=5)

    root.mainloop()


__all__ = ["run_demo"]
