"""Factory helpers for card components."""

from __future__ import annotations

from .card_base import ModernCard
from .card_content import ContentCard


def create_card(
    master,
    width: int = 300,
    height: int = 200,
    theme: str = "dark",
    **kwargs,
) -> ModernCard:
    """快速创建卡片"""
    return ModernCard(master, width=width, height=height, theme=theme, **kwargs)


def create_content_card(
    master,
    title: str | None = None,
    subtitle: str | None = None,
    theme: str = "dark",
    **kwargs,
) -> ContentCard:
    """快速创建内容卡片"""
    return ContentCard(master, title=title, subtitle=subtitle, theme=theme, **kwargs)


__all__ = ["create_card", "create_content_card"]
