"""Global toast manager facade."""

from __future__ import annotations

from typing import Any

from .toast_manager import ToastManager
from .toast_models import ToastType

_toast_manager: ToastManager | None = None


def init_toast_manager(master: Any, **kwargs: Any) -> ToastManager:
    """Initialize the global toast manager."""
    global _toast_manager
    _toast_manager = ToastManager(master, **kwargs)
    return _toast_manager


def get_toast_manager() -> ToastManager | None:
    """Return the global toast manager, if initialized."""
    return _toast_manager


def show_toast(
    message: str,
    toast_type: ToastType = ToastType.INFO,
    duration: int = 3000,
) -> None:
    """Show a toast through the global manager."""
    if _toast_manager:
        _toast_manager.show(message, toast_type, duration)


def show_success(message: str) -> None:
    """Show a success toast through the global manager."""
    if _toast_manager:
        _toast_manager.success(message)


def show_error(message: str) -> None:
    """Show an error toast through the global manager."""
    if _toast_manager:
        _toast_manager.error(message)


def show_warning(message: str) -> None:
    """Show a warning toast through the global manager."""
    if _toast_manager:
        _toast_manager.warning(message)


def show_info(message: str) -> None:
    """Show an info toast through the global manager."""
    if _toast_manager:
        _toast_manager.info(message)


__all__ = [
    "get_toast_manager",
    "init_toast_manager",
    "show_error",
    "show_info",
    "show_success",
    "show_toast",
    "show_warning",
]
