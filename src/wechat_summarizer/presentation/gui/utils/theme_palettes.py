"""Theme palette constants."""

from __future__ import annotations

from .theme_models import ThemeMap

WECHAT_GREEN = "#07C160"
WECHAT_BLUE = "#576B95"

THEMES: ThemeMap = {
    "light": {
        "primary": WECHAT_GREEN,
        "secondary": WECHAT_BLUE,
        "background": "#FFFFFF",
        "surface": "#F5F5F5",
        "text": "#333333",
        "text_secondary": "#666666",
        "border": "#E0E0E0",
        "success": "#52C41A",
        "warning": "#FAAD14",
        "error": "#FF4D4F",
    },
    "dark": {
        "primary": WECHAT_GREEN,
        "secondary": WECHAT_BLUE,
        "background": "#1A1A1A",
        "surface": "#2D2D2D",
        "text": "#FFFFFF",
        "text_secondary": "#AAAAAA",
        "border": "#404040",
        "success": "#52C41A",
        "warning": "#FAAD14",
        "error": "#FF4D4F",
    },
}

HIGH_CONTRAST_THEMES: ThemeMap = {
    "light": {
        "primary": "#0066CC",
        "secondary": "#003366",
        "background": "#FFFFFF",
        "surface": "#F0F0F0",
        "text": "#000000",
        "text_secondary": "#333333",
        "border": "#000000",
        "success": "#006600",
        "warning": "#CC6600",
        "error": "#CC0000",
    },
    "dark": {
        "primary": "#66B2FF",
        "secondary": "#99CCFF",
        "background": "#000000",
        "surface": "#1A1A1A",
        "text": "#FFFFFF",
        "text_secondary": "#CCCCCC",
        "border": "#FFFFFF",
        "success": "#66FF66",
        "warning": "#FFCC00",
        "error": "#FF6666",
    },
}

BASE_FONT_SIZES: dict[str, int] = {
    "xs": 10,
    "sm": 12,
    "base": 14,
    "lg": 16,
    "xl": 20,
    "2xl": 24,
    "3xl": 32,
    "4xl": 40,
}


__all__ = [
    "BASE_FONT_SIZES",
    "HIGH_CONTRAST_THEMES",
    "THEMES",
    "WECHAT_BLUE",
    "WECHAT_GREEN",
]
