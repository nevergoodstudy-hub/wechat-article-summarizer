"""Toolbar, search, and status bar behavior for DataGrid."""

from __future__ import annotations

import tkinter as tk
from typing import Any


class DataGridToolbarMixin:
    """Search toolbar and status label rendering."""

    def _create_toolbar(self: Any) -> None:
        self.toolbar = tk.Frame(self, bg=self.colors["bg"], height=50)
        self.toolbar.pack(fill=tk.X, padx=10, pady=(10, 5))
        self.toolbar.pack_propagate(False)

        search_frame = tk.Frame(self.toolbar, bg=self.colors["row_bg"], padx=10, pady=5)
        search_frame.pack(side=tk.LEFT)

        tk.Label(
            search_frame,
            text="🔍",
            bg=self.colors["row_bg"],
            fg=self.colors["text_secondary"],
            font=("Segoe UI", 12),
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_change)

        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            bg=self.colors["row_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief=tk.FLAT,
            font=("Segoe UI", 11),
            width=25,
        )
        self.search_entry.pack(side=tk.LEFT)

        self.batch_frame = tk.Frame(self.toolbar, bg=self.colors["bg"])
        self.batch_frame.pack(side=tk.LEFT, padx=20)

        self.selection_label = tk.Label(
            self.toolbar,
            text="",
            bg=self.colors["bg"],
            fg=self.colors["text_secondary"],
            font=("Segoe UI", 10),
        )
        self.selection_label.pack(side=tk.RIGHT)

    def _on_search_change(self: Any, *_args: object) -> None:
        query = self.search_var.get().strip()
        if len(query) > 100:
            query = query[:100]
            self.search_var.set(query)

        self.search_query = query.lower()
        self._apply_filters()
        self._refresh_display()

    def _create_status_bar(self: Any) -> None:
        self.status_bar = tk.Frame(self, bg=self.colors["header_bg"], height=30)
        self.status_bar.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.status_label = tk.Label(
            self.status_bar,
            text="共 0 条记录",
            bg=self.colors["header_bg"],
            fg=self.colors["text_secondary"],
            font=("Segoe UI", 9),
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)

    def _update_status_bar(self: Any) -> None:
        total = len(self._raw_data)
        filtered = len(self._filtered_data)
        if filtered == total:
            self.status_label.config(text=f"共 {total} 条记录")
        else:
            self.status_label.config(text=f"显示 {filtered} / {total} 条记录")
