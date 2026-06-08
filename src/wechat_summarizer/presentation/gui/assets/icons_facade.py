"""Facade helpers for the GUI icon library."""

from __future__ import annotations

from typing import Any

from .icons_manager import IconManager
from .icons_models import IconSize

_icon_manager = IconManager()


def get_icon(name: str, size: IconSize = IconSize.MEDIUM, color: str = "#FFFFFF") -> Any | None:
    """快速获取图标"""
    return _icon_manager.get_icon(name, size, color)


def get_icon_tk(name: str, size: IconSize = IconSize.MEDIUM, color: str = "#FFFFFF") -> Any | None:
    """快速获取Tkinter图标"""
    return _icon_manager.get_icon_tk(name, size, color)


def list_icons() -> list[str]:
    """列出所有图标"""
    return IconManager.list_icons()


__all__ = [
    "_icon_manager",
    "get_icon",
    "get_icon_tk",
    "list_icons",
]
