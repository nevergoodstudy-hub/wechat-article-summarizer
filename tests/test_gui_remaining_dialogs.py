"""Tests for remaining GUI dialog boundary helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from wechat_summarizer.presentation.gui import app_actions, runtime_batch
from wechat_summarizer.presentation.gui.dialogs import (
    app_dialogs,
    batch_dialogs,
    choose_url_text_file,
    confirm_clear_cache,
    confirm_delete_history_article,
    confirm_export_without_configured_directory,
    confirm_process_non_wechat_url,
    history_dialogs,
    show_clear_cache_error,
    show_clear_cache_success,
    show_clipboard_empty_warning,
    show_delete_history_error,
    show_duplicate_urls_removed,
    show_empty_article_url_warning,
    show_empty_batch_url_warning,
    show_no_valid_url_warning,
    show_single_fetch_error,
    show_url_file_read_error,
)
from wechat_summarizer.presentation.gui.pages import history_page


class RecordingMessageBox:
    def __init__(self, answer: bool = True) -> None:
        self.answer = answer
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def askyesno(self, *args: object, **kwargs: object) -> bool:
        self.calls.append(("askyesno", args, kwargs))
        return self.answer

    def showinfo(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("showinfo", args, kwargs))

    def showwarning(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("showwarning", args, kwargs))

    def showerror(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("showerror", args, kwargs))


class RecordingFileDialog:
    def __init__(self, result: str = "") -> None:
        self.result = result
        self.calls: list[dict[str, object]] = []

    def askopenfilename(self, **kwargs: object) -> str:
        self.calls.append(kwargs)
        return self.result


@pytest.mark.unit
def test_remaining_dialog_helpers_are_reexported_from_dialogs_package() -> None:
    assert show_duplicate_urls_removed is app_dialogs.show_duplicate_urls_removed
    assert show_empty_article_url_warning is app_dialogs.show_empty_article_url_warning
    assert confirm_process_non_wechat_url is app_dialogs.confirm_process_non_wechat_url
    assert show_single_fetch_error is app_dialogs.show_single_fetch_error
    assert (
        confirm_export_without_configured_directory
        is app_dialogs.confirm_export_without_configured_directory
    )
    assert choose_url_text_file is batch_dialogs.choose_url_text_file
    assert show_url_file_read_error is batch_dialogs.show_url_file_read_error
    assert show_clipboard_empty_warning is batch_dialogs.show_clipboard_empty_warning
    assert show_empty_batch_url_warning is batch_dialogs.show_empty_batch_url_warning
    assert show_no_valid_url_warning is batch_dialogs.show_no_valid_url_warning
    assert confirm_delete_history_article is history_dialogs.confirm_delete_history_article
    assert show_delete_history_error is history_dialogs.show_delete_history_error
    assert confirm_clear_cache is history_dialogs.confirm_clear_cache
    assert show_clear_cache_success is history_dialogs.show_clear_cache_success
    assert show_clear_cache_error is history_dialogs.show_clear_cache_error


@pytest.mark.unit
def test_app_dialog_helpers_preserve_prompts(monkeypatch: pytest.MonkeyPatch) -> None:
    messagebox = RecordingMessageBox(answer=True)
    monkeypatch.setattr(app_dialogs, "messagebox", messagebox)

    app_dialogs.show_duplicate_urls_removed(2)
    app_dialogs.show_empty_article_url_warning()
    assert app_dialogs.confirm_process_non_wechat_url() is True
    app_dialogs.show_single_fetch_error("boom")
    assert app_dialogs.confirm_export_without_configured_directory() is True

    assert messagebox.calls == [
        ("showinfo", ("已自动去重", "检测到 2 个重复链接\n已自动删除重复项"), {}),
        ("showwarning", ("提示", "请输入文章URL"), {}),
        ("askyesno", ("提示", "输入的链接可能不是有效的微信公众号链接\n\n是否继续处理？"), {}),
        ("showerror", ("错误", "boom"), {}),
        (
            "askyesno",
            (
                "导出目录未设置",
                "您尚未设置默认导出目录。\n\n"
                "建议在「设置」页面配置导出目录，这样每次导出时会自动定位到该目录。\n\n"
                "是否继续导出？\n"
                "\n· 点击「是」继续导出（每次需手动选择位置）"
                "\n· 点击「否」前往设置页配置导出目录",
            ),
            {"icon": "warning"},
        ),
    ]


@pytest.mark.unit
def test_batch_dialog_helpers_preserve_prompts(monkeypatch: pytest.MonkeyPatch) -> None:
    filedialog = RecordingFileDialog(result="D:/urls.txt")
    messagebox = RecordingMessageBox()
    monkeypatch.setattr(batch_dialogs, "filedialog", filedialog)
    monkeypatch.setattr(batch_dialogs, "messagebox", messagebox)

    assert batch_dialogs.choose_url_text_file() == "D:/urls.txt"
    batch_dialogs.show_url_file_read_error("nope")
    batch_dialogs.show_clipboard_empty_warning()
    batch_dialogs.show_empty_batch_url_warning()
    batch_dialogs.show_no_valid_url_warning()

    assert filedialog.calls == [{"filetypes": [("Text files", "*.txt"), ("All files", "*.*")]}]
    assert messagebox.calls == [
        ("showerror", ("错误", "读取失败: nope"), {}),
        ("showwarning", ("提示", "剪贴板为空"), {}),
        ("showwarning", ("提示", "请输入URL"), {}),
        ("showwarning", ("提示", "未找到有效URL"), {}),
    ]


@pytest.mark.unit
def test_history_dialog_helpers_preserve_prompts(monkeypatch: pytest.MonkeyPatch) -> None:
    messagebox = RecordingMessageBox(answer=True)
    monkeypatch.setattr(history_dialogs, "messagebox", messagebox)

    assert (
        history_dialogs.confirm_delete_history_article("A very long cached article title") is True
    )
    history_dialogs.show_delete_history_error("delete failed")
    assert history_dialogs.confirm_clear_cache() is True
    history_dialogs.show_clear_cache_success(3)
    history_dialogs.show_clear_cache_error("clear failed")

    assert messagebox.calls == [
        ("askyesno", ("确认", '删除 "A very long cached articl..." ?'), {}),
        ("showerror", ("错误", "删除失败: delete failed"), {}),
        ("askyesno", ("确认", "确定清空所有缓存？此操作不可撤销。"), {}),
        ("showinfo", ("成功", "已清空 3 条缓存"), {}),
        ("showerror", ("错误", "清空失败: clear failed"), {}),
    ]


@pytest.mark.unit
def test_non_dialog_gui_modules_delegate_dialogs() -> None:
    assert "messagebox" not in app_actions.GUIActionsMixin._on_fetch.__globals__
    assert "messagebox" not in app_actions.GUIActionsMixin._show_error.__globals__
    assert "messagebox" not in app_actions.GUIActionsMixin._check_export_dir_configured.__globals__
    assert "filedialog" not in runtime_batch.on_import_urls.__globals__
    assert "messagebox" not in runtime_batch.on_import_urls.__globals__
    assert "messagebox" not in runtime_batch.on_paste_urls.__globals__
    assert "messagebox" not in runtime_batch.on_batch_process.__globals__
    assert "messagebox" not in history_page.HistoryPage._delete_history_article.__globals__
    assert "messagebox" not in history_page.HistoryPage._on_clear_cache.__globals__


@pytest.mark.unit
def test_remaining_dialog_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/dialogs/app_dialogs.py",
        repo_root / "src/wechat_summarizer/presentation/gui/dialogs/batch_dialogs.py",
        repo_root / "src/wechat_summarizer/presentation/gui/dialogs/history_dialogs.py",
        repo_root / "src/wechat_summarizer/presentation/gui/app_actions.py",
        repo_root / "src/wechat_summarizer/presentation/gui/runtime_batch.py",
        repo_root / "src/wechat_summarizer/presentation/gui/pages/history_page.py",
        repo_root / "src/wechat_summarizer/presentation/gui/dialogs/__init__.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target
