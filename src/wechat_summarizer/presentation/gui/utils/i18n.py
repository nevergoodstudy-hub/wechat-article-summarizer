"""Compatibility exports for GUI internationalization utilities."""

from __future__ import annotations

from .i18n_detection import (
    detect_posix_language,
    detect_windows_language,
)
from .i18n_facade import _i18n, detect_system_language, get_i18n, get_language, set_language, tr
from .i18n_loader import get_translations_dir, load_single_translation, load_translations
from .i18n_manager import I18n
from .i18n_models import (
    DEFAULT_LANGUAGE,
    LANGUAGE_CODES,
    MAX_TEXT_LENGTH,
    MAX_TRANSLATION_FILE_SIZE,
    RTL_LANGUAGES,
    SUPPORTED_LANGUAGES,
    LanguageInfo,
)
from .i18n_sanitizer import sanitize_translation_text

__all__ = [
    "DEFAULT_LANGUAGE",
    "LANGUAGE_CODES",
    "MAX_TEXT_LENGTH",
    "MAX_TRANSLATION_FILE_SIZE",
    "RTL_LANGUAGES",
    "SUPPORTED_LANGUAGES",
    "I18n",
    "LanguageInfo",
    "_i18n",
    "detect_posix_language",
    "detect_system_language",
    "detect_windows_language",
    "get_i18n",
    "get_language",
    "get_translations_dir",
    "load_single_translation",
    "load_translations",
    "sanitize_translation_text",
    "set_language",
    "tr",
]
