"""Data models for GUI autosave."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class Draft:
    """草稿数据"""

    form_id: str
    data: dict[str, Any]
    timestamp: float
    version: int = 1
    encrypted: bool = False


@dataclass
class FormField:
    """表单字段定义"""

    name: str
    widget: tk.Widget
    get_value: Callable[[], Any] | None = None
    set_value: Callable[[Any], None] | None = None
    sensitive: bool = False


__all__ = [
    "Draft",
    "FormField",
]
