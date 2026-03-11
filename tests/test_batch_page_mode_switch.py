"""BatchPage 模式切换壳层测试。"""

from __future__ import annotations

import pytest

from wechat_summarizer.presentation.gui.pages.batch_page import BatchPage


class _FakePanel:
    def __init__(self) -> None:
        self.pack_calls: list[dict] = []
        self.pack_forget_calls = 0
        self.page_shown_calls = 0
        self.processing_states: list[bool] = []

    def pack(self, **kwargs) -> None:
        self.pack_calls.append(kwargs)

    def pack_forget(self) -> None:
        self.pack_forget_calls += 1

    def on_page_shown(self) -> None:
        self.page_shown_calls += 1

    def set_processing_state(self, processing: bool) -> None:
        self.processing_states.append(processing)


class _FakeVar:
    def __init__(self, value: str) -> None:
        self._value = value

    def get(self) -> str:
        return self._value

    def set(self, value: str) -> None:
        self._value = value


@pytest.mark.unit
def test_switch_mode_hides_inactive_panel_and_shows_selected_panel() -> None:
    page = BatchPage.__new__(BatchPage)
    page._mode_var = _FakeVar(BatchPage.MODE_OFFICIAL_ACCOUNT)
    page.url_batch_panel = _FakePanel()
    page.official_account_workflow_panel = _FakePanel()

    BatchPage._show_active_panel(page)

    assert page.url_batch_panel.pack_forget_calls == 1
    assert page.official_account_workflow_panel.pack_calls == [
        {"fill": "both", "expand": True}
    ]


@pytest.mark.unit
def test_on_page_shown_delegates_to_active_panel() -> None:
    page = BatchPage.__new__(BatchPage)
    page._mode_var = _FakeVar(BatchPage.MODE_URL_BATCH)
    page.url_batch_panel = _FakePanel()
    page.official_account_workflow_panel = _FakePanel()

    BatchPage.on_page_shown(page)

    assert page.url_batch_panel.page_shown_calls == 1
    assert page.official_account_workflow_panel.page_shown_calls == 0


@pytest.mark.unit
def test_set_processing_state_delegates_to_url_batch_panel() -> None:
    page = BatchPage.__new__(BatchPage)
    page.url_batch_panel = _FakePanel()

    BatchPage.set_processing_state(page, True)
    BatchPage.set_processing_state(page, False)

    assert page.url_batch_panel.processing_states == [True, False]
