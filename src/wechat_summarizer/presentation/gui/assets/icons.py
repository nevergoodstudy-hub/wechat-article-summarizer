"""Compatibility entrypoint for the GUI icon library."""

from __future__ import annotations

from .icons_facade import _icon_manager, get_icon, get_icon_tk, list_icons
from .icons_manager import IconManager
from .icons_models import IconSize, IconStyle
from .icons_parser import SVGPathParser
from .icons_paths import ICON_PATHS
from .icons_runtime import (
    CAIROSVG_AVAILABLE as _CAIROSVG_AVAILABLE,
)
from .icons_runtime import (
    PIL_AVAILABLE as _PIL_AVAILABLE,
)
from .icons_runtime import Image, ImageDraw, ImageTk, cairosvg

__all__ = [
    "ICON_PATHS",
    "_CAIROSVG_AVAILABLE",
    "_PIL_AVAILABLE",
    "IconManager",
    "IconSize",
    "IconStyle",
    "Image",
    "ImageDraw",
    "ImageTk",
    "SVGPathParser",
    "_icon_manager",
    "cairosvg",
    "get_icon",
    "get_icon_tk",
    "list_icons",
]
