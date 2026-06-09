"""Compatibility entrypoint for the DataGrid component."""

from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable
from typing import Any, Literal

from .datagrid_data import DataGridDataMixin
from .datagrid_header import DataGridHeaderMixin
from .datagrid_models import Column
from .datagrid_rows import DataGridRowsMixin
from .datagrid_toolbar import DataGridToolbarMixin
from .datagrid_virtual import VirtualScrollContainer

logger = logging.getLogger(__name__)


class DataGrid(
    DataGridToolbarMixin,
    DataGridHeaderMixin,
    DataGridRowsMixin,
    DataGridDataMixin,
    tk.Frame,
):
    """Modern virtualized data table component."""

    MAX_ROWS = 50000
    MAX_COLUMNS = 100
    MAX_CELL_LENGTH = 500

    def __init__(
        self,
        parent: tk.Misc,
        columns: list[Column],
        selectable: bool = True,
        multi_select: bool = False,
        on_row_select: Callable[[list[int]], None] | None = None,
        on_sort: Callable[[str, str], None] | None = None,
        on_filter: Callable[[str, str], None] | None = None,
        **kwargs: Any,
    ):
        super().__init__(parent, **kwargs)

        if len(columns) > self.MAX_COLUMNS:
            logger.warning("列数过多(%s)，已截断至%s列", len(columns), self.MAX_COLUMNS)
            columns = columns[: self.MAX_COLUMNS]

        self.columns = columns
        self.selectable = selectable
        self.multi_select = multi_select
        self.on_row_select = on_row_select
        self.on_sort = on_sort
        self.on_filter = on_filter

        self._raw_data: list[dict[str, Any]] = []
        self._filtered_data: list[dict[str, Any]] = []
        self.selected_rows: list[int] = []
        self.sort_column: str | None = None
        self.sort_order: Literal["asc", "desc"] = "asc"
        self.filters: dict[str, str] = {}
        self.search_query: str = ""

        self.colors = {
            "bg": "#1a1a1a",
            "header_bg": "#252525",
            "row_bg": "#1e1e1e",
            "row_alt_bg": "#222222",
            "row_hover": "#2a2a2a",
            "row_selected": "#1e3a5f",
            "border": "#404040",
            "text": "#e5e5e5",
            "text_secondary": "#a0a0a0",
            "accent": "#3b82f6",
        }
        self.configure(bg=self.colors["bg"])

        self._resize_column: int | None = None
        self._resize_start_x = 0
        self._resize_start_width = 0

        self._setup_ui()

    def _setup_ui(self) -> None:
        self._create_toolbar()
        self._create_header()

        self.table_container = VirtualScrollContainer(
            self,
            row_height=42,
            buffer_rows=5,
            row_factory=self._create_table_row,
            bg=self.colors["bg"],
        )
        self.table_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.table_container.canvas.configure(bg=self.colors["bg"])
        self.table_container.content_frame.configure(bg=self.colors["bg"])

        self._create_status_bar()


__all__ = [
    "Column",
    "DataGrid",
    "VirtualScrollContainer",
]


if __name__ == "__main__":
    from .datagrid_demo import run_datagrid_demo

    run_datagrid_demo()
