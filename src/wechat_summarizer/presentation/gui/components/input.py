"""Compatibility entrypoint for modern input components."""

from __future__ import annotations

from .input_adornments import ClearButton, FloatingLabel
from .input_compat import CTK_AVAILABLE as _CTK_AVAILABLE
from .input_compat import ctk
from .input_factories import create_input, create_textarea
from .input_modern import ModernInput
from .input_password import PasswordInput
from .input_state import ValidationState
from .input_textarea import ModernTextArea

__all__ = [
    "_CTK_AVAILABLE",
    "ClearButton",
    "FloatingLabel",
    "ModernInput",
    "ModernTextArea",
    "PasswordInput",
    "ValidationState",
    "create_input",
    "create_textarea",
    "ctk",
]
