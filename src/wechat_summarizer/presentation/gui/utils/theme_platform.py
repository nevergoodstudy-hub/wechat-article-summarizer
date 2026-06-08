"""Platform integration helpers for theme settings."""

from __future__ import annotations

from loguru import logger

from .theme_models import AppearanceMode


def apply_appearance_mode(mode: AppearanceMode) -> None:
    """Apply appearance mode to CustomTkinter when available."""
    try:
        import customtkinter as ctk

        if mode == AppearanceMode.SYSTEM:
            ctk.set_appearance_mode("system")
        elif mode == AppearanceMode.DARK:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
    except ImportError:
        logger.debug("customtkinter not available for theme switching")


def detect_system_theme() -> AppearanceMode:
    """检测系统主题"""
    try:
        import sys

        if sys.platform == "win32":
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return AppearanceMode.LIGHT if value else AppearanceMode.DARK
    except Exception:
        pass

    return AppearanceMode.LIGHT


def should_reduce_motion_for_system() -> bool:
    """Check platform animation preferences."""
    try:
        import sys

        if sys.platform == "win32":
            import winreg

            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop")
            value, _ = winreg.QueryValueEx(key, "UserPreferencesMask")
            winreg.CloseKey(key)
            if isinstance(value, bytes) and len(value) > 1:
                return not (value[1] & 0x02)
    except Exception:
        pass

    return False


__all__ = [
    "apply_appearance_mode",
    "detect_system_theme",
    "should_reduce_motion_for_system",
]
