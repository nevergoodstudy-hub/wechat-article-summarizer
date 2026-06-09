"""Tests for export dialog helper composition."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from wechat_summarizer.presentation.gui import runtime_export
from wechat_summarizer.presentation.gui.dialogs import (
    choose_batch_output_directory,
    choose_export_file_path,
    export_dialogs,
    show_batch_export_success,
    show_export_error,
    show_export_options_dialog,
    show_export_success,
)


class RecordingFileDialog:
    def __init__(self, save_result: str = "", directory_result: str = "") -> None:
        self.save_result = save_result
        self.directory_result = directory_result
        self.save_calls: list[dict[str, object]] = []
        self.directory_calls: list[dict[str, str]] = []

    def asksaveasfilename(self, **kwargs: object) -> str:
        self.save_calls.append(kwargs)
        return self.save_result

    def askdirectory(self, **kwargs: str) -> str:
        self.directory_calls.append(kwargs)
        return self.directory_result


class RecordingMessageBox:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[str, str]]] = []

    def showinfo(self, title: str, message: str) -> None:
        self.calls.append(("showinfo", (title, message)))

    def showerror(self, title: str, message: str) -> None:
        self.calls.append(("showerror", (title, message)))


class FakeWidget:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args = args
        self.kwargs = kwargs
        self.packed: list[dict[str, object]] = []

    def pack(self, **kwargs: object) -> None:
        self.packed.append(kwargs)


class FakeButton(FakeWidget):
    instances: list[FakeButton] = []

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.command = kwargs.get("command")
        FakeButton.instances.append(self)


class FakeWindow:
    def __init__(self, _parent: object) -> None:
        self.destroyed = False
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def title(self, value: str) -> None:
        self.calls.append(("title", (value,)))

    def geometry(self, value: str) -> None:
        self.calls.append(("geometry", (value,)))

    def transient(self, parent: object) -> None:
        self.calls.append(("transient", (parent,)))

    def destroy(self) -> None:
        self.destroyed = True


class FakeFont:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs


@pytest.mark.unit
def test_export_dialog_helpers_are_reexported_from_dialogs_package() -> None:
    assert choose_batch_output_directory is export_dialogs.choose_batch_output_directory
    assert choose_export_file_path is export_dialogs.choose_export_file_path
    assert show_batch_export_success is export_dialogs.show_batch_export_success
    assert show_export_error is export_dialogs.show_export_error
    assert show_export_options_dialog is export_dialogs.show_export_options_dialog
    assert show_export_success is export_dialogs.show_export_success


@pytest.mark.unit
def test_choose_export_file_path_preserves_dialog_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    filedialog = RecordingFileDialog(save_result="D:/out/article.md")
    monkeypatch.setattr(export_dialogs, "filedialog", filedialog)

    assert (
        export_dialogs.choose_export_file_path(
            extension=".md",
            filetype_name="Markdown文件",
            filetype_pattern="*.md",
            article_title="A" * 40,
            initial_dir="D:/out",
        )
        == "D:/out/article.md"
    )
    assert filedialog.save_calls == [
        {
            "defaultextension": ".md",
            "filetypes": [("Markdown文件", "*.md")],
            "initialfile": f"{'A' * 30}.md",
            "initialdir": "D:/out",
        }
    ]


@pytest.mark.unit
def test_choose_batch_output_directory_and_messages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    filedialog = RecordingFileDialog(directory_result="D:/batch")
    messagebox = RecordingMessageBox()
    monkeypatch.setattr(export_dialogs, "filedialog", filedialog)
    monkeypatch.setattr(export_dialogs, "messagebox", messagebox)

    assert export_dialogs.choose_batch_output_directory() == "D:/batch"
    export_dialogs.show_export_success("D:/article.md")
    export_dialogs.show_export_error("boom")
    export_dialogs.show_batch_export_success(3, 4, "D:/batch")

    assert filedialog.directory_calls == [{"title": "选择输出目录"}]
    assert messagebox.calls == [
        ("showinfo", ("成功", "导出成功: D:/article.md")),
        ("showerror", ("错误", "导出失败: boom")),
        ("showinfo", ("成功", "导出完成: 3/4 篇\n输出目录: D:/batch")),
    ]


@pytest.mark.unit
def test_export_options_dialog_creates_buttons_and_invokes_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakeButton.instances = []
    window = FakeWindow(object())
    selected: list[str] = []
    fake_ctk = SimpleNamespace(
        CTkToplevel=lambda parent: window,
        CTkLabel=FakeWidget,
        CTkButton=FakeButton,
        CTkFont=FakeFont,
    )
    monkeypatch.setattr(export_dialogs, "ctk", fake_ctk)

    export_dialogs.show_export_options_dialog(
        object(),
        {
            "word": SimpleNamespace(available=True, reason=""),
            "html": SimpleNamespace(available=False, reason="缺少依赖"),
        },
        selected.append,
    )
    FakeButton.instances[0].command()

    assert [button.kwargs["state"] for button in FakeButton.instances] == ["normal", "disabled"]
    assert FakeButton.instances[0].kwargs["text"] == "✓ WORD (预览)"
    assert FakeButton.instances[1].kwargs["text"] == "✗ HTML"
    assert selected == ["word"]
    assert window.destroyed is True


@pytest.mark.unit
def test_runtime_export_delegates_dialog_surfaces() -> None:
    globals_ = runtime_export.do_export.__globals__

    assert "filedialog" not in globals_
    assert "messagebox" not in globals_
    assert "ctk" not in runtime_export.on_export.__globals__
    assert "choose_export_file_path" in globals_
    assert "show_export_options_dialog" in runtime_export.on_export.__globals__
    assert "choose_batch_output_directory" in runtime_export.on_batch_export_format.__globals__


@pytest.mark.unit
def test_export_dialog_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/dialogs/export_dialogs.py",
        repo_root / "src/wechat_summarizer/presentation/gui/runtime_export.py",
        repo_root / "src/wechat_summarizer/presentation/gui/dialogs/__init__.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target
