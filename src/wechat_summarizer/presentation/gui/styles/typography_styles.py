"""Predefined typography styles and facade helpers."""

from __future__ import annotations

from .typography_manager import Typography
from .typography_tokens import FontSize, FontWeight


class TextStyles:
    """Predefined text style pairs."""

    HEADING_1 = (FontSize.XXXL, FontWeight.BOLD)
    HEADING_2 = (FontSize.XXL, FontWeight.BOLD)
    HEADING_3 = (FontSize.XL, FontWeight.SEMI_BOLD)
    HEADING_4 = (FontSize.LG, FontWeight.SEMI_BOLD)

    BODY_LARGE = (FontSize.MD, FontWeight.REGULAR)
    BODY = (FontSize.BASE, FontWeight.REGULAR)
    BODY_SMALL = (FontSize.SM, FontWeight.REGULAR)

    LABEL_LARGE = (FontSize.MD, FontWeight.MEDIUM)
    LABEL = (FontSize.BASE, FontWeight.MEDIUM)
    LABEL_SMALL = (FontSize.SM, FontWeight.MEDIUM)

    BUTTON_LARGE = (FontSize.MD, FontWeight.SEMI_BOLD)
    BUTTON = (FontSize.BASE, FontWeight.SEMI_BOLD)
    BUTTON_SMALL = (FontSize.SM, FontWeight.SEMI_BOLD)

    CAPTION = (FontSize.SM, FontWeight.REGULAR)
    OVERLINE = (FontSize.XS, FontWeight.MEDIUM)

    CODE_LARGE = (FontSize.MD, FontWeight.REGULAR)
    CODE = (FontSize.BASE, FontWeight.REGULAR)
    CODE_SMALL = (FontSize.SM, FontWeight.REGULAR)


_typography = Typography()


def get_font(
    size: FontSize = FontSize.BASE,
    weight: FontWeight = FontWeight.REGULAR,
    monospace: bool = False,
) -> tuple[str, int, str]:
    """Return a Tkinter/CustomTkinter compatible font tuple."""
    return _typography.create_font_tuple(size, weight, monospace)


def get_font_family(monospace: bool = False, include_cjk: bool = True) -> str:
    """Return the configured font family stack."""
    return _typography.get_font_family(monospace, include_cjk)


def get_text_style(
    style: tuple[FontSize, FontWeight],
    monospace: bool = False,
) -> tuple[str, int, str]:
    """Resolve a predefined text style into a font tuple."""
    size, weight = style
    return get_font(size, weight, monospace)


__all__ = ["TextStyles", "get_font", "get_font_family", "get_text_style"]
