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
    assert gui_i18n_guard.find_duplicate_translation_keys() == []


def test_runtime_status_surfaces_are_i18n_extracted() -> None:
    """Recently migrated runtime UI surfaces should stay free of raw literals."""
    gui_i18n_guard = _load_gui_i18n_guard_module()
    repo_root = Path(__file__).resolve().parents[1]
    migrated_files = {
        "src/wechat_summarizer/presentation/gui/app_actions.py",
        "src/wechat_summarizer/presentation/gui/app_layout.py",
        "src/wechat_summarizer/presentation/gui/app_navigation.py",
        "src/wechat_summarizer/presentation/gui/components/contextmenu_demo.py",
        "src/wechat_summarizer/presentation/gui/components/datagrid_demo.py",
        "src/wechat_summarizer/presentation/gui/components/datagrid_toolbar.py",
        "src/wechat_summarizer/presentation/gui/components/graph_viewer.py",
        "src/wechat_summarizer/presentation/gui/components/select_dropdown.py",
        "src/wechat_summarizer/presentation/gui/components/sidebar_demo.py",
        "src/wechat_summarizer/presentation/gui/components/virtuallist_demo.py",
        "src/wechat_summarizer/presentation/gui/dialogs/batch_archive_export.py",
        "src/wechat_summarizer/presentation/gui/dialogs/exit_confirm.py",
        "src/wechat_summarizer/presentation/gui/dialogs/export_dialogs.py",
        "src/wechat_summarizer/presentation/gui/dialogs/settings_dialogs.py",
        "src/wechat_summarizer/presentation/gui/dialogs/word_preview_batch.py",
        "src/wechat_summarizer/presentation/gui/dialogs/word_preview_render.py",
        "src/wechat_summarizer/presentation/gui/dialogs/word_preview_single.py",
        "src/wechat_summarizer/presentation/gui/dialogs/word_preview_window.py",
        "src/wechat_summarizer/presentation/gui/frames/batch_processing.py",
        "src/wechat_summarizer/presentation/gui/frames/history.py",
        "src/wechat_summarizer/presentation/gui/frames/home_dashboard.py",
        "src/wechat_summarizer/presentation/gui/frames/home_info.py",
        "src/wechat_summarizer/presentation/gui/frames/single_article.py",
        "src/wechat_summarizer/presentation/gui/pages/settings_page.py",
        "src/wechat_summarizer/presentation/gui/runtime_batch.py",
        "src/wechat_summarizer/presentation/gui/runtime_export.py",
        "src/wechat_summarizer/presentation/gui/runtime_optimizations.py",
        "src/wechat_summarizer/presentation/gui/settings_api_actions.py",
        "src/wechat_summarizer/presentation/gui/utils/accessibility_demo.py",
        "src/wechat_summarizer/presentation/gui/utils/animation_demo.py",
        "src/wechat_summarizer/presentation/gui/utils/autosave_demo.py",
        "src/wechat_summarizer/presentation/gui/utils/autosave_dialog.py",
        "src/wechat_summarizer/presentation/gui/utils/clipboard_auto.py",
        "src/wechat_summarizer/presentation/gui/utils/lazy_demo.py",
        "src/wechat_summarizer/presentation/gui/utils/microinteractions_demo.py",
        "src/wechat_summarizer/presentation/gui/utils/performance_demo.py",
        "src/wechat_summarizer/presentation/gui/utils/performance_overlay.py",
        "src/wechat_summarizer/presentation/gui/utils/responsive_demo.py",
        "src/wechat_summarizer/presentation/gui/utils/shortcuts_demo.py",
        "src/wechat_summarizer/presentation/gui/utils/shortcuts_models.py",
        "src/wechat_summarizer/presentation/gui/utils/shortcuts_panel.py",
        "src/wechat_summarizer/presentation/gui/utils/transition_demo.py",
        "src/wechat_summarizer/presentation/gui/viewmodels/batch_process_viewmodel.py",
        "src/wechat_summarizer/presentation/gui/viewmodels/single_process_viewmodel.py",
        "src/wechat_summarizer/presentation/gui/widgets/log_panel.py",
        "src/wechat_summarizer/presentation/gui/widgets/sidebar.py",
        "src/wechat_summarizer/presentation/gui/widgets/splash_screen.py",
        "src/wechat_summarizer/presentation/gui/widgets/toast_notification.py",
    }

    hardcoded, _ = gui_i18n_guard.scan_gui_i18n()
    leftovers = [
        violation.format()
        for violation in hardcoded
        if violation.path.relative_to(repo_root).as_posix() in migrated_files
    ]

    assert leftovers == []


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
        "    ctk.CTkLabel(text=f'标题: {ctk}')\n"
        "    ctk.title('窗口标题')\n"
        "    live = type('Live', (), {'announce': lambda self, text: text})()\n"
        "    live.announce('状态已更新')\n"
        "    ctk.CTkLabel(text=tr('已翻译'))\n",
        encoding="utf-8",
    )

    hardcoded, untranslatable = gui_i18n_guard.scan_gui_i18n(
        gui_src=gui_src,
        en_translations=translations / "en.json",
    )

    messages = {violation.message for violation in hardcoded}

    assert len(hardcoded) == 4
    assert any("新增硬编码" in message for message in messages)
    assert any("hardcoded text= f-string" in message for message in messages)
    assert any("hardcoded positional title[0] literal" in message for message in messages)
    assert any("hardcoded positional announce[0] literal" in message for message in messages)
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
