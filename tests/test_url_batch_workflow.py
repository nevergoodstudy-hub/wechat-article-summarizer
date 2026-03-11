"""URL 批处理工作流协调器测试。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from wechat_summarizer.presentation.gui import url_batch_workflow as workflow_module
from wechat_summarizer.presentation.gui.url_batch_workflow import UrlBatchWorkflowCoordinator


class _FakeTextBox:
    def __init__(self, content: str) -> None:
        self.content = content

    def get(self, start: str, end: str) -> str:
        assert start == "1.0"
        assert end == "end"
        return self.content


class _FakeButton:
    def __init__(self) -> None:
        self.configure_calls: list[dict[str, object]] = []

    def configure(self, **kwargs) -> None:
        self.configure_calls.append(kwargs)


class _FakeProgress:
    def __init__(self) -> None:
        self.values: list[float] = []

    def set(self, value: float) -> None:
        self.values.append(value)


class _FakeLabel:
    def __init__(self) -> None:
        self.configure_calls: list[dict[str, object]] = []

    def configure(self, **kwargs) -> None:
        self.configure_calls.append(kwargs)


class _FakeBatchPage:
    def __init__(self) -> None:
        self.processing_states: list[bool] = []

    def set_processing_state(self, processing: bool) -> None:
        self.processing_states.append(processing)


@pytest.mark.unit
def test_on_batch_process_warns_when_input_is_blank(monkeypatch: pytest.MonkeyPatch) -> None:
    warnings: list[tuple[str, str]] = []
    gui = SimpleNamespace(batch_url_text=_FakeTextBox("   "))
    coordinator = UrlBatchWorkflowCoordinator(gui)

    monkeypatch.setattr(
        workflow_module.messagebox,
        "showwarning",
        lambda title, message: warnings.append((title, message)),
    )

    coordinator.on_batch_process()

    assert warnings == [("提示", "请输入URL")]


@pytest.mark.unit
def test_on_batch_process_parses_urls_and_starts_workflow(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_urls: list[list[str]] = []
    gui = SimpleNamespace(batch_url_text=_FakeTextBox("https://a\n\n https://b \n"))
    coordinator = UrlBatchWorkflowCoordinator(gui)

    monkeypatch.setattr(
        workflow_module.messagebox,
        "showwarning",
        lambda title, message: pytest.fail(f"unexpected warning: {title} {message}"),
    )
    coordinator.start_batch_processing = lambda urls: captured_urls.append(urls)  # type: ignore[method-assign]

    coordinator.on_batch_process()

    assert captured_urls == [["https://a", "https://b"]]


@pytest.mark.unit
def test_batch_process_complete_restores_state_and_enables_export_buttons() -> None:
    batch_page = _FakeBatchPage()
    gui = SimpleNamespace(
        batch_page=batch_page,
        batch_start_btn=_FakeButton(),
        batch_progress=_FakeProgress(),
        batch_status_label=_FakeLabel(),
        batch_export_btn=_FakeButton(),
        batch_export_md_btn=_FakeButton(),
        batch_export_word_btn=_FakeButton(),
        batch_export_html_btn=_FakeButton(),
        batch_results=[object(), object()],
        batch_urls=["u1", "u2", "u3"],
        _batch_processing_active=True,
        _batch_cancel_requested=True,
    )
    coordinator = UrlBatchWorkflowCoordinator(gui)

    coordinator.batch_process_complete()

    assert gui._batch_processing_active is False
    assert gui._batch_cancel_requested is False
    assert batch_page.processing_states == [False]
    assert gui.batch_progress.values == [1.0]
    assert gui.batch_status_label.configure_calls[-1]["text"] == "完成: 2/3 篇成功"
    assert gui.batch_export_btn.configure_calls[-1]["state"] == "normal"
    assert gui.batch_export_md_btn.configure_calls[-1]["state"] == "normal"
    assert gui.batch_export_word_btn.configure_calls[-1]["state"] == "normal"
    assert gui.batch_export_html_btn.configure_calls[-1]["state"] == "normal"
