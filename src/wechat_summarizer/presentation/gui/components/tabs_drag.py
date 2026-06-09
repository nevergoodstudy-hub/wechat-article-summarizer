"""Tab drag sorting and keyboard navigation mixin."""

from __future__ import annotations

import tkinter as tk
from typing import Any


class TabsDragMixin:
    """Drag reordering and keyboard tab navigation."""

    def _on_drag_start(self: Any, event: tk.Event[tk.Misc], tab_id: str) -> None:
        self._drag_data["tab_id"] = tab_id
        self._drag_data["start_x"] = event.x_root
        self._drag_data["start_index"] = self._get_tab_index(tab_id)

    def _on_drag_motion(self: Any, event: tk.Event[tk.Misc]) -> None:
        current_tab_id = self._drag_data["tab_id"]
        if current_tab_id is None:
            return

        delta_x = event.x_root - self._drag_data["start_x"]
        current_index = self._get_tab_index(current_tab_id)
        tab_width = 100

        if abs(delta_x) <= tab_width // 2:
            return

        if delta_x > 0 and current_index < len(self._tabs) - 1:
            self._swap_tabs(current_index, current_index + 1)
            self._drag_data["start_x"] = event.x_root
        elif delta_x < 0 and current_index > 0:
            self._swap_tabs(current_index, current_index - 1)
            self._drag_data["start_x"] = event.x_root

    def _on_drag_end(self: Any, _event: tk.Event[tk.Misc]) -> None:
        if self._drag_data["tab_id"] and self._on_tab_reorder:
            self._on_tab_reorder([tab.id for tab in self._tabs])

        self._drag_data["tab_id"] = None

    def _swap_tabs(self: Any, index1: int, index2: int) -> None:
        if 0 <= index1 < len(self._tabs) and 0 <= index2 < len(self._tabs):
            self._tabs[index1], self._tabs[index2] = self._tabs[index2], self._tabs[index1]
            self._rebuild_tab_bar()

    def _rebuild_tab_bar(self: Any) -> None:
        old_buttons = self._tab_buttons.copy()

        for tab in self._tabs:
            if tab.id in old_buttons:
                old_buttons[tab.id]["frame"].pack_forget()
                old_buttons[tab.id]["frame"].pack(side="left", padx=2, pady=(4, 0))

        self.after(50, self._update_indicator)

    def _on_ctrl_tab(self: Any, _event: tk.Event[tk.Misc]) -> None:
        if not self._tabs:
            return

        current = self._get_tab_index(self._active_tab_id)
        next_index = (current + 1) % len(self._tabs)
        self.select_tab(self._tabs[next_index].id)

    def _on_ctrl_shift_tab(self: Any, _event: tk.Event[tk.Misc]) -> None:
        if not self._tabs:
            return

        current = self._get_tab_index(self._active_tab_id)
        prev_index = (current - 1) % len(self._tabs)
        self.select_tab(self._tabs[prev_index].id)


__all__ = ["TabsDragMixin"]
