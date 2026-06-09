"""Optional runtime dependencies for GUI icon rendering."""

from __future__ import annotations

from typing import Any, cast

try:
    from PIL import Image, ImageDraw, ImageTk

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = cast(Any, None)
    ImageDraw = cast(Any, None)
    ImageTk = cast(Any, None)

try:
    import cairosvg

    CAIROSVG_AVAILABLE = True
except ImportError:
    CAIROSVG_AVAILABLE = False
    cairosvg = cast(Any, None)


__all__ = [
    "CAIROSVG_AVAILABLE",
    "PIL_AVAILABLE",
    "Image",
    "ImageDraw",
    "ImageTk",
    "cairosvg",
]
