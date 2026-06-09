"""Header rendering and column resizing for DataGrid."""

from __future__ import annotations

import contextlib
import tkinter as tk
from typing import Any, cast

from .datagrid_models import ANCHOR_BY_ALIGN, Column


class DataGridHeaderMixin:
    """Table header, sorting affordances, and resize handles."""

    _resize_column: int | None

    def _create_header(self: Any) -> None:
        self.header_frame = tk.Frame(self, bg=self.colors["header_bg"], height=45)
        self.header_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        self.header_frame.pack_propagate(False)

        self.header_cells: list[tk.Frame] = []
        x_offset = 0

        for idx, col in enumerate(self.columns):
            cell = self._create_header_cell(col, idx, x_offset)
            self.header_cells.append(cell)
            x_offset += col.width

    def _create_header_cell(
        self: Any,
        col: Column,
        idx: int,
        x_offset: int,
    ) -> tk.Frame:
        cell = tk.Frame(self.header_frame, bg=self.colors["header_bg"], width=col.width, height=45)
        cell.place(x=x_offset, y=0, width=col.width, height=45)

        content = tk.Frame(cell, bg=self.colors["header_bg"])
        content.pack(fill=tk.BOTH, expand=True, padx=10)

        label = tk.Label(
            content,
            text=col.label,
            bg=self.colors["header_bg"],
            fg=self.colors["text"],
            font=("Segoe UI", 11, "bold"),
            anchor=ANCHOR_BY_ALIGN[col.align],
        )
        label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if col.sortable:
            self._attach_sort_controls(col, label, content, cell)

        if col.resizable:
            self._attach_resize_handle(cell, idx)

        return cell

    def _attach_sort_controls(
        self: Any,
        col: Column,
        label: tk.Label,
        content: tk.Frame,
        cell: tk.Frame,
    ) -> None:
        sort_indicator = tk.Label(
            content,
            text="",
            bg=self.colors["header_bg"],
            fg=self.colors["accent"],
            font=("Segoe UI", 10),
        )
        sort_indicator.pack(side=tk.RIGHT, padx=(5, 0))
        col.sort_indicator = sort_indicator

        def on_sort_click(_event: tk.Event[tk.Misc], key: str = col.key) -> None:
            self._toggle_sort(key)

        for widget in [label, content, cell]:
            widget.bind("<Button-1>", on_sort_click)
            with contextlib.suppress(Exception):
                cast(Any, widget).configure(cursor="hand2")

    def _attach_resize_handle(self: Any, cell: tk.Frame, idx: int) -> None:
        resize_handle = tk.Frame(
            cell, bg=self.colors["border"], width=4, cursor="sb_h_double_arrow"
        )
        resize_handle.place(relx=1.0, y=0, relheight=1.0, anchor="ne")

        def on_resize_start(event: tk.Event[tk.Misc], i: int = idx) -> None:
            self._start_resize(event, i)

        resize_handle.bind("<Button-1>", on_resize_start)
        resize_handle.bind("<B1-Motion>", self._do_resize)
        resize_handle.bind("<ButtonRelease-1>", self._end_resize)

    def _start_resize(self: Any, event: tk.Event[tk.Misc], col_index: int) -> None:
        self._resize_column = col_index
        self._resize_start_x = event.x_root
        self._resize_start_width = self.columns[col_index].width

    def _do_resize(self: Any, event: tk.Event[tk.Misc]) -> None:
        if self._resize_column is None:
            return

        delta = event.x_root - self._resize_start_x
        new_width = max(50, min(500, self._resize_start_width + delta))

        self.columns[self._resize_column].width = new_width
        self._refresh_header()
        self.table_container._render_visible_rows()

    def _end_resize(self: Any, _event: tk.Event[tk.Misc]) -> None:
        self._resize_column = None

    def _refresh_header(self: Any) -> None:
        x_offset = 0
        for idx, col in enumerate(self.columns):
            self.header_cells[idx].place(x=x_offset, width=col.width)
            x_offset += col.width
