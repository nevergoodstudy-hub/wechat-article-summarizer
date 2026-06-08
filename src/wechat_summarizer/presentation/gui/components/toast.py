"""Compatibility entrypoint for toast notification components."""

from __future__ import annotations

from .toast_facade import (
    get_toast_manager,
    init_toast_manager,
    show_error,
    show_info,
    show_success,
    show_toast,
    show_warning,
)
from .toast_item import Toast
from .toast_manager import ToastManager
from .toast_models import ToastType
from .toast_runtime import CTK_AVAILABLE as _CTK_AVAILABLE
from .toast_runtime import ctk

__all__ = [
    "_CTK_AVAILABLE",
    "Toast",
    "ToastManager",
    "ToastType",
    "ctk",
    "get_toast_manager",
    "init_toast_manager",
    "show_error",
    "show_info",
    "show_success",
    "show_toast",
    "show_warning",
]
