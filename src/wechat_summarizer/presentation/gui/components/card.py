"""Compatibility entrypoint for modern card components."""

from __future__ import annotations

from .card_action import ActionCard
from .card_base import ModernCard
from .card_compat import CTK_AVAILABLE as _CTK_AVAILABLE
from .card_compat import ctk
from .card_content import ContentCard
from .card_factory import create_card, create_content_card
from .card_models import CardStyle, CornerRadius, ShadowDepth
from .card_stat import StatCard

__all__ = [
    "_CTK_AVAILABLE",
    "ActionCard",
    "CardStyle",
    "ContentCard",
    "CornerRadius",
    "ModernCard",
    "ShadowDepth",
    "StatCard",
    "create_card",
    "create_content_card",
    "ctk",
]
