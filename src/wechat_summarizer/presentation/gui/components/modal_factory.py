"""Factory helpers for modal components."""

from __future__ import annotations

from collections.abc import Callable

from .modal_alert import AlertModal
from .modal_base import Modal
from .modal_confirm import ConfirmModal
from .modal_models import ModalSize


def show_modal(
    master,
    title: str = "标题",
    size: ModalSize = ModalSize.MEDIUM,
    theme: str = "dark",
) -> Modal:
    """显示模态框"""
    modal = Modal(master, title=title, size=size, theme=theme)
    modal.open()
    return modal


def show_confirm(
    master,
    message: str,
    title: str = "确认",
    on_confirm: Callable | None = None,
    on_cancel: Callable | None = None,
    theme: str = "dark",
) -> ConfirmModal:
    """显示确认对话框"""
    modal = ConfirmModal(
        master,
        title=title,
        message=message,
        on_confirm=on_confirm,
        on_cancel=on_cancel,
        theme=theme,
    )
    modal.open()
    return modal


def show_alert(
    master,
    message: str,
    title: str = "提示",
    alert_type: str = "info",
    theme: str = "dark",
) -> AlertModal:
    """显示提示对话框"""
    modal = AlertModal(
        master,
        title=title,
        message=message,
        alert_type=alert_type,
        theme=theme,
    )
    modal.open()
    return modal


__all__ = [
    "show_alert",
    "show_confirm",
    "show_modal",
]
