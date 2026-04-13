"""Composition tests for the thin GUI entrypoint."""

from __future__ import annotations

import pytest

from wechat_summarizer.presentation.gui import app as gui_app


@pytest.mark.unit
def test_run_gui_uses_main_window_coordinator(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}
    sentinel_settings = object()

    class DummyMainWindow:
        def __init__(self, app_factory, *, container=None, settings=None):  # type: ignore[no-untyped-def]
            calls["app_factory"] = app_factory
            calls["container"] = container
            calls["settings"] = settings

        def run(self) -> None:
            calls["ran"] = True

    monkeypatch.setattr(gui_app, "CTK_AVAILABLE", True)
    monkeypatch.setattr(gui_app, "MainWindow", DummyMainWindow)
    monkeypatch.setattr(gui_app, "get_settings", lambda: sentinel_settings)

    gui_app.run_gui()

    assert calls["app_factory"] is gui_app.WechatSummarizerGUI
    assert calls["settings"] is sentinel_settings
    assert calls["ran"] is True


@pytest.mark.unit
def test_run_gui_prints_install_hint_when_customtkinter_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(gui_app, "CTK_AVAILABLE", False)

    gui_app.run_gui()

    captured = capsys.readouterr()
    assert "customtkinter" in captured.out
    assert "pip install customtkinter" in captured.out
