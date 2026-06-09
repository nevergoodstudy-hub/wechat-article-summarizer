"""Translation file loading for GUI internationalization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from loguru import logger

from .i18n_models import MAX_TEXT_LENGTH, MAX_TRANSLATION_FILE_SIZE
from .i18n_sanitizer import sanitize_translation_text


def get_translations_dir() -> Path:
    """Return the GUI translations directory."""
    return Path(__file__).parent.parent / "translations"


def load_translations(cache_hash: dict[str, str]) -> dict[str, dict[str, str]]:
    """Load all JSON translation files into a language keyed mapping."""
    translations_dir = get_translations_dir()

    if not translations_dir.exists():
        translations_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"创建翻译文件目录: {translations_dir}")

    translations: dict[str, dict[str, str]] = {}
    for lang_file in translations_dir.glob("*.json"):
        loaded = load_single_translation(lang_file, lang_file.stem, cache_hash)
        if loaded is not None:
            translations[lang_file.stem] = loaded
    return translations


def load_single_translation(
    lang_file: Path,
    lang_code: str,
    cache_hash: dict[str, str],
) -> dict[str, str] | None:
    """Load and sanitize a single translation file."""
    try:
        if lang_file.stat().st_size > MAX_TRANSLATION_FILE_SIZE:
            logger.warning(f"翻译文件过大: {lang_file}")
            return None

        content = lang_file.read_text(encoding="utf-8")
        content_hash = hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()
        if cache_hash.get(lang_code) == content_hash:
            return None

        cache_hash[lang_code] = content_hash
        raw_translations: Any = json.loads(content)
        if not isinstance(raw_translations, dict):
            logger.warning(f"翻译文件格式无效: {lang_file}")
            return None

        safe_translations: dict[str, str] = {}
        for key, value in raw_translations.items():
            if isinstance(key, str) and isinstance(value, str):
                text = value[:MAX_TEXT_LENGTH]
                safe_translations[key] = sanitize_translation_text(text)

        logger.debug(f"已加载翻译: {lang_code} ({len(safe_translations)} 条)")
        return safe_translations
    except Exception as exc:
        logger.warning(f"加载翻译文件失败 {lang_file}: {exc}")
        return None


__all__ = [
    "get_translations_dir",
    "load_single_translation",
    "load_translations",
]
