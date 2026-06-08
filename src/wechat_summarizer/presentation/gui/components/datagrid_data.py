"""Data operations for DataGrid."""

from __future__ import annotations

import logging
from typing import Any, cast

logger = logging.getLogger(__name__)


class DataGridDataMixin:
    """Filtering, sorting, refresh, and public data APIs."""

    sort_column: str | None

    def _toggle_sort(self: Any, column_key: str) -> None:
        if self.sort_column == column_key:
            self.sort_order = "desc" if self.sort_order == "asc" else "asc"
        else:
            self.sort_column = column_key
            self.sort_order = "asc"

        for col in self.columns:
            if col.sort_indicator is not None:
                if col.key == column_key:
                    col.sort_indicator.config(text="↑" if self.sort_order == "asc" else "↓")
                else:
                    col.sort_indicator.config(text="")

        if self.on_sort:
            self.on_sort(self.sort_column, self.sort_order)

        self._apply_sort()
        self._refresh_display()

    def _apply_sort(self: Any) -> None:
        if not self.sort_column:
            return

        def sort_key(row: dict[str, Any]) -> tuple[int, float | str]:
            val = row.get(self.sort_column, "")
            if isinstance(val, (int, float)):
                return (0, val)
            try:
                return (0, float(val))
            except (ValueError, TypeError):
                return (1, str(val).lower())

        self._filtered_data.sort(key=sort_key, reverse=self.sort_order == "desc")

    def _apply_filters(self: Any) -> None:
        if not self.search_query and not self.filters:
            self._filtered_data = self._raw_data.copy()
        else:
            self._filtered_data = [row for row in self._raw_data if self._row_matches(row)]

        if self.sort_column:
            self._apply_sort()

    def _row_matches(self: Any, row: dict[str, Any]) -> bool:
        if self.search_query:
            match = any(self.search_query in str(value).lower() for value in row.values())
            if not match:
                return False

        for col_key, filter_val in self.filters.items():
            if filter_val and filter_val.lower() not in str(row.get(col_key, "")).lower():
                return False
        return True

    def _refresh_display(self: Any) -> None:
        self.selected_rows = cast(list[int], [])
        self._update_selection_info()
        self.table_container.set_data(self._filtered_data)
        self._update_status_bar()

    def set_data(self: Any, data: list[dict[str, Any]]) -> None:
        if not isinstance(data, list):
            logger.error("数据必须是列表类型")
            return

        if len(data) > self.MAX_ROWS:
            logger.warning("数据量超限(%s行)，已截断至%s行", len(data), self.MAX_ROWS)
            data = data[: self.MAX_ROWS]

        self._raw_data = data
        self._apply_filters()
        self._refresh_display()

    def get_data(self: Any) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], self._raw_data.copy())

    def get_filtered_data(self: Any) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], self._filtered_data.copy())

    def get_selected_data(self: Any) -> list[dict[str, Any]]:
        return [self._filtered_data[i] for i in self.selected_rows if i < len(self._filtered_data)]

    def select_all(self: Any) -> None:
        if self.multi_select:
            self.selected_rows = list(range(len(self._filtered_data)))
            self._update_selection_info()
            self.table_container._render_visible_rows()

    def clear_selection(self: Any) -> None:
        self.selected_rows = cast(list[int], [])
        self._update_selection_info()
        self.table_container._render_visible_rows()

    def set_filter(self: Any, column_key: str, value: str) -> None:
        if value:
            self.filters[column_key] = value
        elif column_key in self.filters:
            del self.filters[column_key]
        self._apply_filters()
        self._refresh_display()

    def clear_filters(self: Any) -> None:
        self.filters.clear()
        self.search_var.set("")
        self._apply_filters()
        self._refresh_display()

    def refresh(self: Any) -> None:
        self._refresh_display()

    def destroy(self: Any) -> None:
        self.table_container.destroy()
        cast(Any, super()).destroy()
