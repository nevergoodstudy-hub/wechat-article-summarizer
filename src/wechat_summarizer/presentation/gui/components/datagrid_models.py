"""Shared data structures for DataGrid components."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

Anchor = Literal["nw", "n", "ne", "w", "center", "e", "sw", "s", "se"]
CellAlign = Literal["left", "center", "right"]


@dataclass
class Column:
    """Column definition used by DataGrid."""

    key: str
    label: str
    width: int = 150
    sortable: bool = True
    filterable: bool = True
    resizable: bool = True
    align: CellAlign = "left"
    formatter: Callable[[Any], str] | None = None
    sort_indicator: tk.Label | None = field(default=None, init=False, repr=False)


ANCHOR_BY_ALIGN: dict[CellAlign, Anchor] = {
    "left": "w",
    "center": "center",
    "right": "e",
}
