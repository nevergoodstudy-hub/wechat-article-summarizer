"""Compatibility entrypoint for modal components."""

from __future__ import annotations

from .modal_alert import AlertModal
from .modal_base import Modal
from .modal_compat import CTK_AVAILABLE as _CTK_AVAILABLE
from .modal_compat import ctk
from .modal_confirm import ConfirmModal
from .modal_factory import show_alert, show_confirm, show_modal
from .modal_models import ModalSize

__all__ = [
    "_CTK_AVAILABLE",
    "AlertModal",
    "ConfirmModal",
    "Modal",
    "ModalSize",
    "ctk",
    "show_alert",
    "show_confirm",
    "show_modal",
]
