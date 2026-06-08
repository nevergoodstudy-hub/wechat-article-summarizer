"""Lazy-loaded widget container."""

from __future__ import annotations

import logging
import math
import tkinter as tk
from typing import Any

from .lazy_loader import LazyLoader
from .lazy_models import LoadResult, LoadState

logger = logging.getLogger(__name__)


class LazyWidget(tk.Frame):
    """Container that renders loading/error states before the actual component."""

    def __init__(
        self,
        parent: tk.Misc,
        component_name: str,
        component_props: dict[str, Any] | None = None,
        loading_text: str = "加载中...",
        error_text: str = "加载失败",
        retry_text: str = "重试",
        **kwargs: Any,
    ) -> None:
        bg = kwargs.pop("bg", "#1a1a1a")
        super().__init__(parent, bg=bg, **kwargs)

        self._component_name = component_name
        self._component_props = component_props or {}
        self._loading_text = loading_text
        self._error_text = error_text
        self._retry_text = retry_text
        self._bg = bg

        self._loader = LazyLoader()
        self._actual_widget: tk.Widget | None = None
        self._state = LoadState.IDLE

        self._setup_ui()
        self._start_loading()

    def _setup_ui(self) -> None:
        """Build the placeholder UI."""
        self._status_frame = tk.Frame(self, bg=self._bg)
        self._status_frame.pack(fill=tk.BOTH, expand=True)

        self._loading_label = tk.Label(
            self._status_frame,
            text=self._loading_text,
            bg=self._bg,
            fg="#808080",
            font=("Segoe UI", 14),
        )
        self._spinner_canvas = tk.Canvas(
            self._status_frame,
            width=40,
            height=40,
            bg=self._bg,
            highlightthickness=0,
        )
        self._spinner_angle = 0
        self._spinner_running = False

        self._error_label = tk.Label(
            self._status_frame,
            text=self._error_text,
            bg=self._bg,
            fg="#ef4444",
            font=("Segoe UI", 14),
        )
        self._retry_button = tk.Button(
            self._status_frame,
            text=self._retry_text,
            bg="#3b82f6",
            fg="#ffffff",
            font=("Segoe UI", 11),
            relief=tk.FLAT,
            cursor="hand2",
            command=self._start_loading,
        )

    def _show_loading(self) -> None:
        """Show the loading state."""
        self._state = LoadState.LOADING
        self._error_label.pack_forget()
        self._retry_button.pack_forget()
        self._spinner_canvas.pack(pady=(50, 10))
        self._loading_label.pack()
        self._spinner_running = True
        self._animate_spinner()

    def _show_error(self, error: str) -> None:
        """Show the error state."""
        self._state = LoadState.ERROR
        self._spinner_running = False
        self._spinner_canvas.pack_forget()
        self._loading_label.pack_forget()
        self._error_label.configure(text=f"{self._error_text}\n{error}")
        self._error_label.pack(pady=(50, 10))
        self._retry_button.pack()

    def _show_component(self, component_class: type) -> None:
        """Instantiate and show the loaded component."""
        self._state = LoadState.SUCCESS
        self._spinner_running = False
        self._status_frame.pack_forget()

        try:
            self._actual_widget = component_class(self, **self._component_props)
            self._actual_widget.pack(fill=tk.BOTH, expand=True)
        except Exception as exc:
            logger.error("组件实例化失败: %s", exc)
            self._status_frame.pack(fill=tk.BOTH, expand=True)
            self._show_error(str(exc))

    def _animate_spinner(self) -> None:
        """Draw a small rotating spinner."""
        if not self._spinner_running:
            return

        self._spinner_canvas.delete("all")
        cx, cy = 20, 20
        radius = 15

        for index in range(8):
            angle = self._spinner_angle + index * 45
            rad = math.radians(angle)
            x1 = cx + radius * 0.6 * math.cos(rad)
            y1 = cy + radius * 0.6 * math.sin(rad)
            x2 = cx + radius * math.cos(rad)
            y2 = cy + radius * math.sin(rad)
            alpha = int(255 * (1 - index / 8))
            color = f"#{alpha:02x}{alpha:02x}{255:02x}"
            self._spinner_canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill=color,
                width=2,
                capstyle=tk.ROUND,
            )

        self._spinner_angle = (self._spinner_angle + 30) % 360
        if self._spinner_running:
            self.after(50, self._animate_spinner)

    def _start_loading(self) -> None:
        """Start loading the configured component."""
        self._show_loading()

        def on_loaded(result: LoadResult) -> None:
            self.after(0, lambda: self._on_load_complete(result))

        self._loader.load_component(self._component_name, on_loaded)

    def _on_load_complete(self, result: LoadResult) -> None:
        """Render the result of a load attempt."""
        if result.state == LoadState.SUCCESS and result.component:
            self._show_component(result.component)
        else:
            self._show_error(result.error or "未知错误")

    def get_actual_widget(self) -> tk.Widget | None:
        """Return the wrapped widget if loading succeeded."""
        return self._actual_widget


__all__ = ["LazyWidget"]
