"""Factory helpers for glass components."""

from __future__ import annotations

from .glass_card import GlassCard
from .glass_frame import LiquidGlassFrame


def create_glass_frame(
    master,
    width: int = 200,
    height: int = 200,
    theme: str = "dark",
    **kwargs,
) -> LiquidGlassFrame:
    """Create a liquid glass frame."""
    return LiquidGlassFrame(master, width=width, height=height, theme=theme, **kwargs)


def create_glass_card(
    master,
    title: str | None = None,
    width: int = 300,
    height: int = 200,
    theme: str = "dark",
    **kwargs,
) -> GlassCard:
    """Create a glass card."""
    return GlassCard(master, title=title, width=width, height=height, theme=theme, **kwargs)


__all__ = ["create_glass_card", "create_glass_frame"]
