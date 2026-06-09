"""Runtime GUI internationalization manager."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

from loguru import logger

from .i18n_detection import (
    detect_posix_language,
    detect_system_language,
    detect_windows_language,
)
from .i18n_loader import load_single_translation, load_translations
from .i18n_models import (
    DEFAULT_LANGUAGE as MODEL_DEFAULT_LANGUAGE,
)
from .i18n_models import (
    LANGUAGE_CODES as MODEL_LANGUAGE_CODES,
)
from .i18n_models import (
    RTL_LANGUAGES as MODEL_RTL_LANGUAGES,
)
from .i18n_models import (
    SUPPORTED_LANGUAGES as MODEL_SUPPORTED_LANGUAGES,
)
from .i18n_models import (
    LanguageInfo,
)
from .i18n_sanitizer import sanitize_translation_text


class I18n:
    """Internationalization manager with hot reload and RTL helpers."""

    SUPPORTED_LANGUAGES = MODEL_SUPPORTED_LANGUAGES
    LANGUAGE_CODES = MODEL_LANGUAGE_CODES
    RTL_LANGUAGES = MODEL_RTL_LANGUAGES
    DEFAULT_LANGUAGE = MODEL_DEFAULT_LANGUAGE

    _instance: ClassVar[I18n | None] = None
    _initialized: bool

    def __new__(cls) -> I18n:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._translations: dict[str, dict[str, str]] = {}
        self._current_language = self.DEFAULT_LANGUAGE
        self._observers: list[Callable[[], None]] = []
        self._cache_hash: dict[str, str] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        """Load all translation files."""
        loaded = load_translations(self._cache_hash)
        self._translations.update(loaded)

    def _load_single_translation(self, lang_file: Path, lang_code: str) -> None:
        """Load one translation file into the current catalog."""
        loaded = load_single_translation(lang_file, lang_code, self._cache_hash)
        if loaded is not None:
            self._translations[lang_code] = loaded

    def _sanitize_text(self, text: str) -> str:
        """Sanitize a translation string."""
        return sanitize_translation_text(text)

    def reload_translations(self) -> None:
        """Reload translation files and notify observers."""
        self._load_translations()
        self._notify_observers()

    def detect_system_language(self) -> str:
        """Detect system UI language."""
        return detect_system_language(self.DEFAULT_LANGUAGE)

    def _detect_windows_language(self) -> str:
        """Detect Windows UI language."""
        return detect_windows_language(self.DEFAULT_LANGUAGE)

    def _detect_posix_language(self) -> str:
        """Detect POSIX UI language."""
        return detect_posix_language(self.DEFAULT_LANGUAGE)

    def get_language(self) -> str:
        """Return the current language code."""
        return self._current_language

    def set_language(self, lang: str) -> None:
        """Set current language by code."""
        if lang == "auto":
            actual_lang = self.detect_system_language()
        elif lang in self.LANGUAGE_CODES:
            actual_lang = lang
        else:
            logger.warning(f"不支持的语言: {lang}, 使用默认语言")
            actual_lang = self.DEFAULT_LANGUAGE

        if actual_lang != self._current_language:
            self._current_language = actual_lang
            logger.info(f"语言已切换: {actual_lang}")
            self._notify_observers()

    def tr(self, text: str) -> str:
        """Translate source text, falling back to the original string."""
        if self._current_language == self.DEFAULT_LANGUAGE:
            return text

        translations = self._translations.get(self._current_language, {})
        return translations.get(text) or text

    def add_observer(self, callback: Callable[[], None]) -> None:
        """Register a language-change callback."""
        if callback not in self._observers:
            self._observers.append(callback)

    def remove_observer(self, callback: Callable[[], None]) -> None:
        """Remove a language-change callback."""
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self) -> None:
        """Notify all language-change observers."""
        for callback in self._observers:
            try:
                callback()
            except Exception as exc:
                logger.error(f"语言变化回调执行失败: {exc}")

    def get_language_display_name(self, lang_code: str) -> str:
        """Return the native display name for a language code."""
        info = self.get_language_info(lang_code)
        return info.native_name if info else lang_code

    def get_available_languages(self) -> list[str]:
        """Return available language codes."""
        return self.LANGUAGE_CODES.copy()

    def get_language_info(self, lang_code: str) -> LanguageInfo | None:
        """Return metadata for a language code."""
        for lang in self.SUPPORTED_LANGUAGES:
            if lang.code == lang_code:
                return lang
        return None

    def get_all_language_info(self) -> list[LanguageInfo]:
        """Return metadata for all supported languages."""
        return list(self.SUPPORTED_LANGUAGES)

    def is_rtl(self, lang_code: str | None = None) -> bool:
        """Return whether the language is right-to-left."""
        return (lang_code or self._current_language) in self.RTL_LANGUAGES

    def get_text_direction(self) -> str:
        """Return current text direction."""
        return "rtl" if self.is_rtl() else "ltr"

    def get_text_align(self) -> str:
        """Return current text alignment."""
        return "right" if self.is_rtl() else "left"

    def get_start_anchor(self) -> str:
        """Return Tk start anchor for the current language direction."""
        return "e" if self.is_rtl() else "w"

    def get_end_anchor(self) -> str:
        """Return Tk end anchor for the current language direction."""
        return "w" if self.is_rtl() else "e"

    def flip_horizontal(self, value: str) -> str:
        """Flip horizontal Tk values when the current language is RTL."""
        if not self.is_rtl():
            return value

        flip_map = {
            "left": "right",
            "right": "left",
            "w": "e",
            "e": "w",
            "nw": "ne",
            "ne": "nw",
            "sw": "se",
            "se": "sw",
        }
        return flip_map.get(value, value)


__all__ = ["I18n"]
