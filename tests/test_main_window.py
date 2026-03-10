"""主窗口协调器回归测试。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from wechat_summarizer.presentation.gui.main_window import MainWindowCoordinator


class _FakeRoot:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def deiconify(self) -> None:
        self.calls.append("deiconify")

    def lift(self) -> None:
        self.calls.append("lift")

    def focus_force(self) -> None:
        self.calls.append("focus_force")


class _FakeFrame:
    def __init__(self) -> None:
        self.grid_forget_calls = 0
        self.grid_calls: list[dict[str, str | int]] = []
        self.page_shown_calls = 0

    def grid_forget(self) -> None:
        self.grid_forget_calls += 1

    def grid(self, **kwargs) -> None:
        self.grid_calls.append(kwargs)

    def on_page_shown(self) -> None:
        self.page_shown_calls += 1


class _FakeButton:
    def __init__(self) -> None:
        self.configure_calls: list[dict[str, object]] = []

    def configure(self, **kwargs) -> None:
        self.configure_calls.append(kwargs)


@pytest.mark.unit
def test_show_main_window_restores_window_and_plays_animation() -> None:
    root = _FakeRoot()
    played: list[bool] = []
    coordinator = MainWindowCoordinator(
        SimpleNamespace(
            root=root,
            _play_welcome_animation=lambda: played.append(True),
        )
    )

    coordinator.show_main_window()

    assert root.calls == ["deiconify", "lift", "focus_force"]
    assert played == [True]


@pytest.mark.unit
def test_show_page_updates_page_visibility_and_nav_button_state() -> None:
    home_frame = _FakeFrame()
    settings_frame = _FakeFrame()
    home_button = _FakeButton()
    settings_button = _FakeButton()
    gui = SimpleNamespace(
        _page_frames={"home": home_frame, "settings": settings_frame},
        _nav_buttons={"home": home_button, "settings": settings_button},
        _current_page="home",
    )
    coordinator = MainWindowCoordinator(gui)

    coordinator.show_page("settings")

    assert home_frame.grid_forget_calls == 1
    assert settings_frame.grid_calls == [{"row": 0, "column": 0, "sticky": "nsew"}]
    assert settings_frame.page_shown_calls == 1
    assert gui._current_page == "settings"
    assert settings_button.configure_calls[-1]["text_color"] == "white"
    assert home_button.configure_calls[-1]["fg_color"] == "transparent"


@pytest.mark.unit
def test_show_page_animated_uses_plain_switch_in_low_memory_mode() -> None:
    calls: list[str] = []
    gui = SimpleNamespace(
        _current_page="home",
        _page_frames={"home": _FakeFrame(), "settings": _FakeFrame()},
        _is_low_memory_mode=lambda: True,
        _show_page=lambda page_id: calls.append(page_id),
    )
    coordinator = MainWindowCoordinator(gui)

    coordinator.show_page_animated("settings")

    assert calls == ["settings"]
