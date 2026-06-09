"""Compatibility facade for GUI internationalization."""

from __future__ import annotations

from .i18n_manager import I18n

_i18n = I18n()


def tr(text: str) -> str:
    """Translate text through the global GUI i18n instance."""
    return _i18n.tr(text)


def get_i18n() -> I18n:
    """Return the global GUI i18n instance."""
    return _i18n


def set_language(lang: str) -> None:
    """Set the global GUI language."""
    _i18n.set_language(lang)


def get_language() -> str:
    """Return the current global GUI language."""
    return _i18n.get_language()


def detect_system_language() -> str:
    """Detect the system language through the global GUI i18n instance."""
    return _i18n.detect_system_language()


__all__ = [
    "_i18n",
    "detect_system_language",
    "get_i18n",
    "get_language",
    "set_language",
    "tr",
]
