"""Composition tests for the thin GUI entrypoint."""

from __future__ import annotations

import pytest

from wechat_summarizer.bootstrap import gui as gui_bootstrap
from wechat_summarizer.presentation.gui import app as gui_app


@pytest.mark.unit
def test_run_gui_uses_injected_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}
    sentinel_container = object()
    sentinel_settings = object()

    class DummyMainWindow:
        def __init__(self, app_factory, *, container, settings):  # type: ignore[no-untyped-def]
            calls["app_factory"] = app_factory
            calls["container"] = container
            calls["settings"] = settings

        def run(self) -> None:
            calls["ran"] = True

    monkeypatch.setattr(gui_app, "CTK_AVAILABLE", True)
    monkeypatch.setattr(gui_app, "MainWindow", DummyMainWindow)

    gui_app.run_gui(container=sentinel_container, settings=sentinel_settings)

    assert calls["app_factory"] is gui_app.WechatSummarizerGUI
    assert calls["container"] is sentinel_container
    assert calls["settings"] is sentinel_settings
    assert calls["ran"] is True


@pytest.mark.unit
def test_run_gui_prints_install_hint_when_customtkinter_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(gui_app, "CTK_AVAILABLE", False)

    gui_app.run_gui(container=object(), settings=object())

    captured = capsys.readouterr()
    assert "customtkinter" in captured.out
    assert "pip install customtkinter" in captured.out


@pytest.mark.unit
def test_bootstrap_run_gui_assembles_infrastructure_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, object] = {}
    sentinel_container = object()
    sentinel_settings = object()

    monkeypatch.setattr(gui_bootstrap, "get_container", lambda: sentinel_container)
    monkeypatch.setattr(gui_bootstrap, "get_settings", lambda: sentinel_settings)
    monkeypatch.setattr(
        gui_bootstrap,
        "run_gui_with_dependencies",
        lambda *, container, settings: calls.update({"container": container, "settings": settings}),
    )

    gui_bootstrap.run_gui()

    assert calls == {"container": sentinel_container, "settings": sentinel_settings}
