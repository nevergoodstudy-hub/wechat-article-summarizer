"""System language detection for the GUI."""

from __future__ import annotations

import locale
import os
import platform

from loguru import logger

from .i18n_models import DEFAULT_LANGUAGE

_LOCALE_ENV_KEYS = ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")


def detect_system_language(default_language: str = DEFAULT_LANGUAGE) -> str:
    """Detect the current platform UI language."""
    if platform.system() == "Windows":
        return detect_windows_language(default_language)
    return detect_posix_language(default_language)


def detect_windows_language(default_language: str = DEFAULT_LANGUAGE) -> str:
    """Detect Windows UI language through GetUserDefaultUILanguage."""
    try:
        import ctypes

        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        locale_name = locale.windows_locale.get(lang_id)
        if locale_name:
            logger.debug(f"Windows UI 语言: LANGID={lang_id}, locale={locale_name}")
            return _map_locale_to_language(locale_name, default_language)

        logger.debug(f"未知 Windows LANGID: {lang_id}, 使用默认语言")
    except Exception as exc:
        logger.debug(f"Windows 语言检测失败: {exc}")
    return default_language


def detect_posix_language(default_language: str = DEFAULT_LANGUAGE) -> str:
    """Detect POSIX locale without relying only on deprecated getdefaultlocale()."""
    try:
        lang, _encoding = locale.getlocale()
        mapped = _map_locale_to_language(lang, default_language)
        if mapped != default_language:
            return mapped

        for candidate in _iter_env_locale_candidates():
            mapped = _map_locale_to_language(candidate, default_language)
            if mapped != default_language:
                return mapped
    except Exception as exc:
        logger.debug(f"POSIX 语言检测失败: {exc}")
    return default_language


def _iter_env_locale_candidates() -> list[str]:
    candidates: list[str] = []
    for key in _LOCALE_ENV_KEYS:
        raw_value = os.environ.get(key, "")
        for value in raw_value.split(":"):
            if value:
                candidates.append(value)
    return candidates


def _map_locale_to_language(locale_name: str | None, default_language: str) -> str:
    if not locale_name:
        return default_language

    normalized = locale_name.replace("-", "_").lower()
    if normalized.startswith("zh"):
        return "zh_CN"
    if normalized.startswith("en"):
        return "en"
    return default_language


__all__ = [
    "detect_posix_language",
    "detect_system_language",
    "detect_windows_language",
]
