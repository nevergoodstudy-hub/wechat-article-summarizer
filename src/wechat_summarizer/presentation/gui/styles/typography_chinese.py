"""Chinese font detection helpers."""

from __future__ import annotations


class ChineseFonts:
    """Detect the best available Chinese font with a safe fallback."""

    CHINESE_FONT_FAMILIES = [
        "Microsoft YaHei UI",
        "Microsoft YaHei",
        "SimHei",
        "SimSun",
        "NSimSun",
        "KaiTi",
        "FangSong",
        "Arial",
    ]
    SIZE_TITLE = 24
    SIZE_HEADING = 18
    SIZE_SUBHEADING = 16
    SIZE_NORMAL = 14
    SIZE_SMALL = 12
    SIZE_TINY = 11
    _detected_font: str | None = None

    @classmethod
    def get_best_font(cls) -> str:
        """Detect and return the best available Chinese font."""
        if cls._detected_font:
            return cls._detected_font

        try:
            import tkinter as tk
            from tkinter import font as tkfont

            temp_root = tk.Tk()
            temp_root.withdraw()
            available_fonts = set(tkfont.families())
            temp_root.destroy()

            for font_name in cls.CHINESE_FONT_FAMILIES:
                if font_name in available_fonts:
                    cls._detected_font = font_name
                    return font_name
        except Exception:
            pass

        cls._detected_font = "Microsoft YaHei UI"
        return cls._detected_font


__all__ = ["ChineseFonts"]
