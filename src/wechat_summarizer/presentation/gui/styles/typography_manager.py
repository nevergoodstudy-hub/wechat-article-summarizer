"""Typography manager for Tk-compatible font tuples."""

from __future__ import annotations

import platform

from .typography_families import FontFamily
from .typography_tokens import TK_WEIGHT_MAP, FontSize, FontWeight, LineHeight


class Typography:
    """Manage platform-aware font families and Tk font tuple creation."""

    def __init__(self) -> None:
        self._system = self._detect_system()

    @staticmethod
    def _detect_system() -> str:
        """Return a normalized platform name."""
        system = platform.system().lower()
        if "darwin" in system:
            return "mac"
        if "win" in system:
            return "windows"
        return "linux"

    def get_font_family(self, monospace: bool = False, include_cjk: bool = True) -> str:
        """Return a comma-separated CSS/Tk-style font family stack."""
        if monospace:
            fonts = FontFamily.MONOSPACE.copy()
        elif include_cjk:
            fonts = FontFamily.COMBINED.copy()
        else:
            fonts = FontFamily.PRIMARY.copy()
        return ", ".join(fonts)

    def get_primary_font(self) -> str:
        """Return the best primary font for the current platform."""
        if self._system == "mac":
            return "SF Pro Display"
        if self._system == "windows":
            return "Segoe UI"
        return "Inter"

    def get_monospace_font(self) -> str:
        """Return the best monospace font for the current platform."""
        if self._system == "mac":
            return "SF Mono"
        if self._system == "windows":
            return "Cascadia Code"
        return "JetBrains Mono"

    @staticmethod
    def get_font_config(
        size: FontSize = FontSize.BASE,
        weight: FontWeight = FontWeight.REGULAR,
        line_height: LineHeight | None = None,
    ) -> dict[str, int | float]:
        """Return a serializable font config dictionary."""
        config: dict[str, int | float] = {
            "size": size.value,
            "weight": weight.value,
        }
        if line_height:
            config["line_height"] = line_height.value
        return config

    def create_font_tuple(
        self,
        size: FontSize = FontSize.BASE,
        weight: FontWeight = FontWeight.REGULAR,
        monospace: bool = False,
    ) -> tuple[str, int, str]:
        """Create a Tkinter/CustomTkinter compatible font tuple."""
        font_family = self.get_monospace_font() if monospace else self.get_primary_font()
        return font_family, size.value, TK_WEIGHT_MAP.get(weight, "normal")


__all__ = ["Typography"]
