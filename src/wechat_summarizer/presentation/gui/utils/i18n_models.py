"""Shared models and constants for GUI internationalization."""

from __future__ import annotations

from dataclasses import dataclass

MAX_TRANSLATION_FILE_SIZE = 1024 * 1024
MAX_TEXT_LENGTH = 10000
DEFAULT_LANGUAGE = "zh_CN"


@dataclass
class LanguageInfo:
    """Language metadata used by the GUI language picker."""

    code: str
    name: str
    native_name: str
    rtl: bool = False


SUPPORTED_LANGUAGES = [
    LanguageInfo("auto", "Auto", "跟随系统"),
    LanguageInfo("zh_CN", "Simplified Chinese", "简体中文"),
    LanguageInfo("zh_TW", "Traditional Chinese", "繁體中文"),
    LanguageInfo("en", "English", "English"),
    LanguageInfo("ar", "Arabic", "العربية", rtl=True),
    LanguageInfo("he", "Hebrew", "עברית", rtl=True),
]

LANGUAGE_CODES = [lang.code for lang in SUPPORTED_LANGUAGES]
RTL_LANGUAGES = {lang.code for lang in SUPPORTED_LANGUAGES if lang.rtl}


__all__ = [
    "DEFAULT_LANGUAGE",
    "LANGUAGE_CODES",
    "MAX_TEXT_LENGTH",
    "MAX_TRANSLATION_FILE_SIZE",
    "RTL_LANGUAGES",
    "SUPPORTED_LANGUAGES",
    "LanguageInfo",
]
