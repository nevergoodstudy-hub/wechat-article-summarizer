"""Compatibility entrypoint for the GUI typography system."""

from __future__ import annotations

from .typography_chinese import ChineseFonts
from .typography_families import FontFamily
from .typography_manager import Typography
from .typography_styles import TextStyles, get_font, get_font_family, get_text_style
from .typography_tokens import FontSize, FontWeight, LetterSpacing, LineHeight

__all__ = [
    "ChineseFonts",
    "FontFamily",
    "FontSize",
    "FontWeight",
    "LetterSpacing",
    "LineHeight",
    "TextStyles",
    "Typography",
    "get_font",
    "get_font_family",
    "get_text_style",
]
