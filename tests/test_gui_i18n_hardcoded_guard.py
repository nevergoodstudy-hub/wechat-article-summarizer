"""GUI i18n hardcoded-string baseline guard tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_gui_i18n_guard_module() -> ModuleType:
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "check_gui_i18n_hardcoded.py"
    spec = importlib.util.spec_from_file_location("check_gui_i18n_hardcoded", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Failed to load GUI i18n guard module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_current_gui_i18n_baseline_does_not_regress() -> None:
    """Current hardcoded GUI string baseline must not grow."""
    gui_i18n_guard = _load_gui_i18n_guard_module()

    assert gui_i18n_guard.check_gui_i18n() == []


def test_gui_i18n_guard_detects_user_visible_literal(tmp_path: Path) -> None:
    """Visible widget literals should count toward the hardcoded baseline."""
    gui_i18n_guard = _load_gui_i18n_guard_module()
    gui_src = tmp_path / "gui"
    translations = gui_src / "translations"
    translations.mkdir(parents=True)
    (translations / "en.json").write_text('{"已翻译": "Translated"}', encoding="utf-8")
    (gui_src / "page.py").write_text(
        "from .utils.i18n import tr\n"
        "def build(ctk):\n"
        "    ctk.CTkLabel(text='新增硬编码')\n"
        "    ctk.CTkLabel(text=tr('已翻译'))\n",
        encoding="utf-8",
    )

    hardcoded, untranslatable = gui_i18n_guard.scan_gui_i18n(
        gui_src=gui_src,
        en_translations=translations / "en.json",
    )

    assert len(hardcoded) == 1
    assert "新增硬编码" in hardcoded[0].message
    assert untranslatable == []


def test_gui_i18n_guard_detects_missing_and_dynamic_tr_keys(tmp_path: Path) -> None:
    """Literal tr keys must exist in en.json and dynamic keys stay visible."""
    gui_i18n_guard = _load_gui_i18n_guard_module()
    gui_src = tmp_path / "gui"
    translations = gui_src / "translations"
    translations.mkdir(parents=True)
    (translations / "en.json").write_text('{"已翻译": "Translated"}', encoding="utf-8")
    (gui_src / "page.py").write_text(
        "from .utils.i18n import tr\ndef build(name):\n    tr('缺失翻译')\n    tr(f'动态{name}')\n",
        encoding="utf-8",
    )

    _, untranslatable = gui_i18n_guard.scan_gui_i18n(
        gui_src=gui_src,
        en_translations=translations / "en.json",
    )

    assert {violation.message for violation in untranslatable} == {
        "tr literal missing from en.json: '缺失翻译'",
        "dynamic tr(...) key",
    }
