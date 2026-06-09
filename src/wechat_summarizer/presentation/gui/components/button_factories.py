"""Factory helpers for button components."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .button_icon import IconButton
from .button_models import ButtonVariant
from .button_modern import ModernButton


def create_button(
    master: Any,
    text: str,
    command: Callable[[], None] | None = None,
    variant: ButtonVariant = ButtonVariant.PRIMARY,
    theme: str = "dark",
    **kwargs: Any,
) -> ModernButton:
    """快速创建按钮"""
    return ModernButton(master, text=text, command=command, variant=variant, theme=theme, **kwargs)


def create_icon_button(
    master: Any,
    icon: Any,
    command: Callable[[], None] | None = None,
    theme: str = "dark",
    **kwargs: Any,
) -> IconButton:
    """快速创建图标按钮"""
    return IconButton(master, icon=icon, command=command, theme=theme, **kwargs)


__all__ = [
    "create_button",
    "create_icon_button",
]
