"""Compatibility entrypoint for modern button components."""

from __future__ import annotations

from .button_compat import CTK_AVAILABLE as _CTK_AVAILABLE
from .button_compat import ctk
from .button_factories import create_button, create_icon_button
from .button_group import ButtonGroup
from .button_icon import IconButton
from .button_models import ButtonSize, ButtonVariant
from .button_modern import ModernButton
from .button_ripple import RippleEffect

__all__ = [
    "_CTK_AVAILABLE",
    "ButtonGroup",
    "ButtonSize",
    "ButtonVariant",
    "IconButton",
    "ModernButton",
    "RippleEffect",
    "create_button",
    "create_icon_button",
    "ctk",
]
