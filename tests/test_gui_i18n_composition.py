"""Composition tests for split GUI i18n utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from wechat_summarizer.presentation.gui.utils import i18n as i18n_module
from wechat_summarizer.presentation.gui.utils.i18n import (
    DEFAULT_LANGUAGE,
    LANGUAGE_CODES,
    MAX_TEXT_LENGTH,
    MAX_TRANSLATION_FILE_SIZE,
    RTL_LANGUAGES,
    SUPPORTED_LANGUAGES,
    I18n,
    LanguageInfo,
    detect_system_language,
    get_i18n,
    get_language,
    set_language,
    tr,
)
from wechat_summarizer.presentation.gui.utils.i18n_detection import (
    detect_posix_language,
    detect_windows_language,
)
from wechat_summarizer.presentation.gui.utils.i18n_facade import (
    detect_system_language as facade_detect_system_language,
)
from wechat_summarizer.presentation.gui.utils.i18n_facade import (
    get_i18n as split_get_i18n,
)
from wechat_summarizer.presentation.gui.utils.i18n_facade import (
    get_language as split_get_language,
)
from wechat_summarizer.presentation.gui.utils.i18n_facade import (
    set_language as split_set_language,
)
from wechat_summarizer.presentation.gui.utils.i18n_facade import tr as split_tr
from wechat_summarizer.presentation.gui.utils.i18n_manager import I18n as SplitI18n
from wechat_summarizer.presentation.gui.utils.i18n_models import (
    DEFAULT_LANGUAGE as SPLIT_DEFAULT_LANGUAGE,
)
from wechat_summarizer.presentation.gui.utils.i18n_models import (
    LANGUAGE_CODES as SPLIT_LANGUAGE_CODES,
)
from wechat_summarizer.presentation.gui.utils.i18n_models import (
    MAX_TEXT_LENGTH as SPLIT_MAX_TEXT_LENGTH,
)
from wechat_summarizer.presentation.gui.utils.i18n_models import (
    MAX_TRANSLATION_FILE_SIZE as SPLIT_MAX_TRANSLATION_FILE_SIZE,
)
from wechat_summarizer.presentation.gui.utils.i18n_models import (
    RTL_LANGUAGES as SPLIT_RTL_LANGUAGES,
)
from wechat_summarizer.presentation.gui.utils.i18n_models import (
    SUPPORTED_LANGUAGES as SPLIT_SUPPORTED_LANGUAGES,
)
from wechat_summarizer.presentation.gui.utils.i18n_models import (
    LanguageInfo as SplitLanguageInfo,
)
from wechat_summarizer.presentation.gui.utils.i18n_sanitizer import (
    sanitize_translation_text,
)


@pytest.mark.unit
def test_i18n_module_keeps_compatibility_exports() -> None:
    assert i18n_module.I18n is SplitI18n
    assert i18n_module.LanguageInfo is SplitLanguageInfo
    assert I18n is SplitI18n
    assert LanguageInfo is SplitLanguageInfo
    assert tr is split_tr
    assert set_language is split_set_language
    assert get_language is split_get_language
    assert get_i18n is split_get_i18n
    assert i18n_module.detect_system_language is facade_detect_system_language
    assert detect_system_language is facade_detect_system_language
    assert i18n_module.detect_posix_language is detect_posix_language
    assert i18n_module.detect_windows_language is detect_windows_language

    assert DEFAULT_LANGUAGE == SPLIT_DEFAULT_LANGUAGE == "zh_CN"
    assert MAX_TRANSLATION_FILE_SIZE == SPLIT_MAX_TRANSLATION_FILE_SIZE
    assert MAX_TEXT_LENGTH == SPLIT_MAX_TEXT_LENGTH
    assert SUPPORTED_LANGUAGES is SPLIT_SUPPORTED_LANGUAGES
    assert LANGUAGE_CODES == SPLIT_LANGUAGE_CODES
    assert RTL_LANGUAGES == SPLIT_RTL_LANGUAGES == {"ar", "he"}
    assert I18n.DEFAULT_LANGUAGE == "zh_CN"
    assert I18n.LANGUAGE_CODES == ["auto", "zh_CN", "zh_TW", "en", "ar", "he"]


@pytest.mark.unit
def test_i18n_manager_accepts_supported_language_codes() -> None:
    manager = object.__new__(I18n)
    manager._initialized = True
    manager._translations = {"en": {"首页": "Home"}}
    manager._current_language = "zh_CN"
    manager._observers = []
    manager._cache_hash = {}

    manager.set_language("en")

    assert manager.get_language() == "en"
    assert manager.tr("首页") == "Home"


@pytest.mark.unit
def test_i18n_manager_preserves_rtl_helpers() -> None:
    manager = object.__new__(I18n)
    manager._initialized = True
    manager._translations = {}
    manager._current_language = "ar"
    manager._observers = []
    manager._cache_hash = {}

    assert manager.is_rtl()
    assert manager.get_text_direction() == "rtl"
    assert manager.get_text_align() == "right"
    assert manager.get_start_anchor() == "e"
    assert manager.get_end_anchor() == "w"
    assert manager.flip_horizontal("left") == "right"
    assert manager.flip_horizontal("nw") == "ne"


@pytest.mark.unit
def test_i18n_sanitizer_escapes_markup_and_event_handlers() -> None:
    sanitized = sanitize_translation_text('<script>alert(1)</script>按钮 onclick=bad')

    assert "<script" not in sanitized.lower()
    assert "onclick=" not in sanitized.lower()
    assert "按钮" in sanitized


@pytest.mark.unit
def test_i18n_posix_detection_uses_locale_and_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "wechat_summarizer.presentation.gui.utils.i18n_detection.locale.getlocale",
        lambda: ("en_US", "UTF-8"),
    )
    assert detect_posix_language() == "en"

    monkeypatch.setattr(
        "wechat_summarizer.presentation.gui.utils.i18n_detection.locale.getlocale",
        lambda: (None, None),
    )
    monkeypatch.setenv("LANGUAGE", "")
    monkeypatch.setenv("LC_ALL", "")
    monkeypatch.setenv("LC_MESSAGES", "")
    monkeypatch.setenv("LANG", "zh_CN.UTF-8")
    assert detect_posix_language() == "zh_CN"


@pytest.mark.unit
def test_i18n_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/utils/i18n.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/i18n_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/i18n_sanitizer.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/i18n_detection.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/i18n_loader.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/i18n_manager.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/i18n_facade.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target
