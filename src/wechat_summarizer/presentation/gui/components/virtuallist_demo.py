"""Manual demo for the virtual list component."""

from __future__ import annotations

import tkinter as tk
from typing import Any

from .virtuallist import VirtualList


def run_demo() -> None:
    """Run the virtual list demo."""
    root = tk.Tk()
    root.title("虚拟列表测试")
    root.geometry("600x500")
    root.configure(bg="#121212")

    test_data = [f"项目 {i + 1} - 这是一段测试文本内容" for i in range(10000)]

    def render_item(container: tk.Frame, data: Any, index: int) -> tk.Widget:
        frame = tk.Frame(container, bg="#1a1a1a")

        tk.Label(
            frame,
            text=f"#{index + 1}",
            bg="#1a1a1a",
            fg="#808080",
            font=("Segoe UI", 10),
            width=6,
        ).pack(side=tk.LEFT, padx=(12, 0))

        tk.Label(
            frame,
            text=data,
            bg="#1a1a1a",
            fg="#e5e5e5",
            font=("Segoe UI", 12),
            anchor="w",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        return frame

    def on_click(index: int, data: Any) -> None:
        print(f"点击: {index} - {data}")

    vlist = VirtualList(
        root,
        item_height=40,
        render_item=render_item,
        on_item_click=on_click,
        bg="#1a1a1a",
    )
    vlist.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    vlist.set_data(test_data)

    tk.Label(
        root,
        text=f"共 {len(test_data)} 条数据 | 只渲染可见区域",
        bg="#121212",
        fg="#808080",
        font=("Segoe UI", 10),
    ).pack(side=tk.BOTTOM, pady=10)

    root.mainloop()


if __name__ == "__main__":
    run_demo()
