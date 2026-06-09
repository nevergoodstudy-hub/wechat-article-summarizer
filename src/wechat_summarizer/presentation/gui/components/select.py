"""Compatibility entrypoint for modern select widgets."""

from __future__ import annotations

from .select_compat import CTK_AVAILABLE as _CTK_AVAILABLE
from .select_compat import ctk
from .select_factory import create_select
from .select_models import SelectMode, SelectOption
from .select_modern import ModernSelect

__all__ = [
    "_CTK_AVAILABLE",
    "ModernSelect",
    "SelectMode",
    "SelectOption",
    "create_select",
    "ctk",
]
