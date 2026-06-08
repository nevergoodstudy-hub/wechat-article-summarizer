"""Manual smoke demo for GUI lazy loading."""

from __future__ import annotations

import tkinter as tk

from .i18n import tr
from .lazy_loader import LazyLoader
from .lazy_widget import LazyWidget


def run_demo() -> None:
    """Run a small local demo window."""
    root = tk.Tk()
    root.title(tr("懒加载测试"))
    root.geometry("600x400")
    root.configure(bg="#121212")

    loader = LazyLoader()
    info_label = tk.Label(
        root,
        text=tr(
            "懒加载系统已初始化\n\n支持:\n"
            "- 路由级代码分割\n- 按需加载重组件\n- 加载状态显示\n- 失败降级处理\n- 预加载支持"
        ),
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 14),
        justify=tk.LEFT,
    )
    info_label.pack(pady=50, padx=50)

    class MockComponent(tk.Frame):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, bg="#1a1a1a", **kwargs)
            tk.Label(
                self,
                text=tr("组件已加载"),
                bg="#1a1a1a",
                fg="#10b981",
                font=("Segoe UI", 16),
            ).pack(pady=20)

    loader._loaded_cache["mock_component"] = MockComponent
    lazy_widget = LazyWidget(root, component_name="mock_component", bg="#1a1a1a")
    lazy_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    root.mainloop()


__all__ = ["run_demo"]
