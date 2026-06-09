"""Row rendering and selection behavior for DataGrid."""

from __future__ import annotations

import html
import tkinter as tk
from typing import Any, cast

from .datagrid_models import ANCHOR_BY_ALIGN


class DataGridRowsMixin:
    """Visible row creation, hover effects, and selection state."""

    def _create_table_row(self: Any, index: int) -> tk.Widget:
        if index >= len(self._filtered_data):
            return tk.Frame(self.table_container.content_frame, bg=self.colors["bg"])

        row_data = self._filtered_data[index]
        is_selected = index in self.selected_rows
        is_alt = index % 2 == 1
        bg_color = self._row_background(is_selected, is_alt)
        row_frame = tk.Frame(self.table_container.content_frame, bg=bg_color, height=42)

        def on_enter(_event: tk.Event[tk.Misc], frame: tk.Frame = row_frame) -> None:
            if not is_selected:
                self._set_row_color(frame, self.colors["row_hover"])

        def on_leave(_event: tk.Event[tk.Misc], frame: tk.Frame = row_frame) -> None:
            if not is_selected:
                self._set_row_color(frame, self._row_background(False, is_alt))

        def on_row_click(event: tk.Event[tk.Misc], i: int = index) -> None:
            self._select_row(i, event)

        row_frame.bind("<Enter>", on_enter)
        row_frame.bind("<Leave>", on_leave)
        if self.selectable:
            row_frame.bind("<Button-1>", on_row_click)

        x_offset = 0
        for col in self.columns:
            value = row_data.get(col.key, "")
            display_value = self._format_cell_value(value, col.formatter)
            cell = tk.Label(
                row_frame,
                text=display_value,
                bg=bg_color,
                fg=self.colors["text"],
                font=("Segoe UI", 10),
                anchor=ANCHOR_BY_ALIGN[col.align],
                padx=10,
            )
            cell.place(x=x_offset, y=0, width=col.width, height=42)
            if self.selectable:
                cell.bind("<Button-1>", on_row_click)
            cell.bind("<Enter>", on_enter)
            cell.bind("<Leave>", on_leave)
            x_offset += col.width

        return row_frame

    def _row_background(self: Any, is_selected: bool, is_alt: bool) -> str:
        if is_selected:
            return str(self.colors["row_selected"])
        if is_alt:
            return str(self.colors["row_alt_bg"])
        return str(self.colors["row_bg"])

    def _set_row_color(self: Any, frame: tk.Frame, color: str) -> None:
        frame.config(bg=color)
        for child in frame.winfo_children():
            cast(Any, child).config(bg=color)

    def _format_cell_value(self: Any, value: Any, formatter: Any) -> str:
        if formatter:
            try:
                display_value = formatter(value)
            except Exception:
                display_value = str(value)
        else:
            display_value = str(value)
        return str(html.escape(str(display_value)[: self.MAX_CELL_LENGTH]))

    def _select_row(self: Any, index: int, event: tk.Event[tk.Misc] | None = None) -> None:
        event_state = int(event.state) if event is not None else 0
        ctrl_pressed = bool(event_state & 0x4)
        shift_pressed = bool(event_state & 0x1)

        if not self.multi_select:
            self.selected_rows = [index]
        elif ctrl_pressed:
            if index in self.selected_rows:
                self.selected_rows.remove(index)
            else:
                self.selected_rows.append(index)
        elif shift_pressed and self.selected_rows:
            last = self.selected_rows[-1]
            start, end = min(last, index), max(last, index)
            for i in range(start, end + 1):
                if i not in self.selected_rows:
                    self.selected_rows.append(i)
        else:
            self.selected_rows = [index]

        self._update_selection_info()
        if self.on_row_select:
            self.on_row_select(self.selected_rows)
        self.table_container._render_visible_rows()

    def _update_selection_info(self: Any) -> None:
        count = len(self.selected_rows)
        self.selection_label.config(text=f"已选择 {count} 行" if count > 0 else "")
