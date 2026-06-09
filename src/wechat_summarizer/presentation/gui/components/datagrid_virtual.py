"""Virtual scrolling container for DataGrid."""

from __future__ import annotations

import logging
import tkinter as tk
import tkinter.ttk as ttk
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class VirtualScrollContainer(tk.Frame):
    """Only render rows that are visible in the scroll window."""

    MAX_ROWS = 50000

    def __init__(
        self,
        parent: tk.Misc,
        row_height: int = 40,
        buffer_rows: int = 5,
        row_factory: Callable[[int], tk.Widget] | None = None,
        **kwargs: Any,
    ):
        super().__init__(parent, **kwargs)

        self.row_height = row_height
        self.buffer_rows = buffer_rows
        self.visible_start = 0
        self.visible_end = 0
        self.total_rows = 0
        self.data: list[Any] = []
        self.row_widgets: dict[int, tk.Widget] = {}
        self.row_factory = row_factory

        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(self, yscrollcommand=self.scrollbar.set, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.canvas.yview)

        self.content_frame = tk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            0, 0, window=self.content_frame, anchor=tk.NW
        )

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)

    def set_data(self, data: list[Any]) -> None:
        if len(data) > self.MAX_ROWS:
            logger.warning("数据量过大(%s行)，已截断至%s行", len(data), self.MAX_ROWS)
            data = data[: self.MAX_ROWS]

        self.data = data
        self.total_rows = len(data)
        total_height = self.total_rows * self.row_height
        self.canvas.config(scrollregion=(0, 0, 800, total_height))
        self._render_visible_rows()

    def _render_visible_rows(self) -> None:
        canvas_height = self.canvas.winfo_height()
        if canvas_height <= 1:
            canvas_height = 400

        scroll_y = self.canvas.yview()[0]
        visible_top = int(scroll_y * self.total_rows * self.row_height)
        start_row = max(0, (visible_top // self.row_height) - self.buffer_rows)
        end_row = min(
            self.total_rows, ((visible_top + canvas_height) // self.row_height) + self.buffer_rows
        )

        for idx in list(self.row_widgets.keys()):
            if idx < start_row or idx >= end_row:
                self.row_widgets[idx].destroy()
                del self.row_widgets[idx]

        for idx in range(start_row, end_row):
            if idx not in self.row_widgets and idx < len(self.data):
                row_widget = self._create_row(idx)
                row_widget.place(x=0, y=idx * self.row_height, relwidth=1.0, height=self.row_height)
                self.row_widgets[idx] = row_widget

        self.visible_start = start_row
        self.visible_end = end_row

    def _create_row(self, index: int) -> tk.Widget:
        if self.row_factory is not None:
            return self.row_factory(index)
        frame = tk.Frame(self.content_frame)
        tk.Label(frame, text=f"Row {index}").pack()
        return frame

    def _on_canvas_configure(self, event: tk.Event[tk.Misc]) -> None:
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self._render_visible_rows()

    def _on_mousewheel(self, event: tk.Event[tk.Misc]) -> None:
        if getattr(event, "num", None) == 4:
            delta = 1
        elif getattr(event, "num", None) == 5:
            delta = -1
        else:
            delta = event.delta // 120

        self.canvas.yview_scroll(-delta, "units")
        self._render_visible_rows()

    def destroy(self) -> None:
        for widget in self.row_widgets.values():
            widget.destroy()
        self.row_widgets.clear()
        super().destroy()
