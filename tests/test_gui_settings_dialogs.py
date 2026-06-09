"""Tests for settings dialog helper composition."""

from __future__ import annotations

from pathlib import Path

import pytest

from wechat_summarizer.presentation.gui import settings_api_actions
from wechat_summarizer.presentation.gui.dialogs import (
    choose_export_directory,
    confirm_clear_api_keys,
    confirm_create_missing_directory,
    confirm_reset_export_settings,
    settings_dialogs,
    show_create_directory_error,
    show_export_directory_not_configured,
    show_missing_export_directory,
    show_startup_error,
)
from wechat_summarizer.presentation.gui.pages import settings_page


class RecordingFileDialog:
    def __init__(self, result: str = "") -> None:
        self.result = result
        self.calls: list[dict[str, str]] = []

    def askdirectory(self, **kwargs: str) -> str:
        self.calls.append(kwargs)
        return self.result


class RecordingMessageBox:
    def __init__(self, answer: bool = True) -> None:
        self.answer = answer
        self.calls: list[tuple[str, tuple[str, ...]]] = []

    def askyesno(self, title: str, message: str) -> bool:
        self.calls.append(("askyesno", (title, message)))
        return self.answer

    def showwarning(self, title: str, message: str) -> None:
        self.calls.append(("showwarning", (title, message)))

    def showinfo(self, title: str, message: str) -> None:
        self.calls.append(("showinfo", (title, message)))

    def showerror(self, title: str, message: str) -> None:
        self.calls.append(("showerror", (title, message)))


@pytest.mark.unit
def test_settings_dialog_helpers_are_reexported_from_dialogs_package() -> None:
    assert choose_export_directory is settings_dialogs.choose_export_directory
    assert confirm_clear_api_keys is settings_dialogs.confirm_clear_api_keys
    assert confirm_create_missing_directory is settings_dialogs.confirm_create_missing_directory
    assert confirm_reset_export_settings is settings_dialogs.confirm_reset_export_settings
    assert show_create_directory_error is settings_dialogs.show_create_directory_error
    assert (
        show_export_directory_not_configured
        is settings_dialogs.show_export_directory_not_configured
    )
    assert show_missing_export_directory is settings_dialogs.show_missing_export_directory
    assert show_startup_error is settings_dialogs.show_startup_error


@pytest.mark.unit
def test_choose_export_directory_uses_existing_current_dir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    filedialog = RecordingFileDialog(result=str(tmp_path))
    monkeypatch.setattr(settings_dialogs, "filedialog", filedialog)

    assert settings_dialogs.choose_export_directory(str(tmp_path)) == str(tmp_path)
    assert filedialog.calls == [{"title": "选择默认导出目录", "initialdir": str(tmp_path)}]


@pytest.mark.unit
def test_choose_export_directory_falls_back_to_home(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    filedialog = RecordingFileDialog()
    monkeypatch.setattr(settings_dialogs, "filedialog", filedialog)
    monkeypatch.setattr(settings_dialogs.Path, "home", lambda: tmp_path)

    assert settings_dialogs.choose_export_directory("missing-dir") is None
    assert filedialog.calls == [{"title": "选择默认导出目录", "initialdir": str(tmp_path)}]


@pytest.mark.unit
def test_settings_dialog_confirm_and_message_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messagebox = RecordingMessageBox(answer=True)
    monkeypatch.setattr(settings_dialogs, "messagebox", messagebox)

    assert settings_dialogs.confirm_clear_api_keys() is True
    assert settings_dialogs.confirm_reset_export_settings() is True
    assert settings_dialogs.confirm_create_missing_directory("D:/out") is True
    settings_dialogs.show_missing_export_directory("D:/missing")
    settings_dialogs.show_export_directory_not_configured()
    settings_dialogs.show_startup_error("启动失败")
    settings_dialogs.show_create_directory_error("创建失败")

    assert messagebox.calls == [
        ("askyesno", ("确认", "确定要清除所有API密钥吗？")),
        ("askyesno", ("确认", "确定要重置所有导出设置吗？")),
        ("askyesno", ("确认", "目录不存在\nD:/out\n\n是否创建？")),
        ("showwarning", ("提示", "目录不存在: D:/missing")),
        ("showinfo", ("提示", "请先设置导出目录")),
        ("showerror", ("错误", "启动失败")),
        ("showerror", ("错误", "创建失败")),
    ]


@pytest.mark.unit
def test_settings_page_and_api_actions_delegate_dialogs() -> None:
    assert "filedialog" not in settings_page.SettingsPage._browse_export_dir.__globals__
    assert "messagebox" not in settings_page.SettingsPage._reset_export_settings.__globals__
    assert "messagebox" not in settings_page.SettingsPage._save_settings.__globals__
    assert (
        "messagebox" not in settings_api_actions.SettingsApiActionsMixin._clear_api_keys.__globals__
    )


@pytest.mark.unit
def test_settings_dialog_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/dialogs/settings_dialogs.py",
        repo_root / "src/wechat_summarizer/presentation/gui/dialogs/__init__.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target
