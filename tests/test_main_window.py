"""主窗口协调器回归测试。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from wechat_summarizer.presentation.gui import main_window as main_window_module
from wechat_summarizer.presentation.gui.event_bus import GUIEventBus
from wechat_summarizer.presentation.gui.main_window import MainWindowCoordinator


class _FakeRoot:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.after_calls: list[int] = []

    def deiconify(self) -> None:
        self.calls.append("deiconify")

    def lift(self) -> None:
        self.calls.append("lift")

    def focus_force(self) -> None:
        self.calls.append("focus_force")

    def after(self, delay_ms: int, callback) -> str:
        self.after_calls.append(delay_ms)
        callback()
        return "after-id"


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


class _FakeThemeWidget:
    def __init__(self, children: list[_FakeThemeWidget] | None = None) -> None:
        self.children = children or []
        self.updated_modes: list[str] = []

    def update_theme(self, mode: str) -> None:
        self.updated_modes.append(mode)

    def winfo_children(self) -> list[_FakeThemeWidget]:
        return self.children


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


@pytest.mark.unit
def test_bind_event_bus_handles_theme_events() -> None:
    theme_values: list[str] = []
    gui = SimpleNamespace(
        event_bus=GUIEventBus(),
        _show_page=lambda page_id: None,
        _show_page_animated=lambda page_id: None,
    )
    coordinator = MainWindowCoordinator(gui)
    coordinator.apply_theme = lambda value: theme_values.append(value)  # type: ignore[method-assign]

    unsubscribe = coordinator.bind_event_bus()
    gui.event_bus.publish("theme_changed", value="浅色")
    unsubscribe()
    gui.event_bus.publish("theme_changed", value="深色")

    assert theme_values == ["浅色"]


@pytest.mark.unit
def test_apply_theme_updates_mode_and_broadcasts(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _FakeRoot()
    page_child = _FakeThemeWidget()
    page = _FakeThemeWidget(children=[page_child])
    sidebar = _FakeThemeWidget()
    status_calls: list[tuple[str, object, bool]] = []
    appearance_modes: list[str] = []
    titlebar_updates: list[tuple[object, str]] = []
    gui = SimpleNamespace(
        root=root,
        _appearance_mode="dark",
        _page_frames={"home": page},
        sidebar=sidebar,
        _set_status=lambda text, color, pulse=False: status_calls.append((text, color, pulse)),
    )
    coordinator = MainWindowCoordinator(gui)

    monkeypatch.setattr(main_window_module, "_ctk_available", True)
    monkeypatch.setattr(
        main_window_module,
        "ctk",
        SimpleNamespace(set_appearance_mode=lambda mode: appearance_modes.append(mode)),
        raising=False,
    )
    monkeypatch.setattr(
        main_window_module.Windows11StyleHelper,
        "update_titlebar_color",
        lambda target_root, mode: titlebar_updates.append((target_root, mode)),
    )

    coordinator.apply_theme("浅色")

    assert gui._appearance_mode == "light"
    assert appearance_modes == ["light"]
    assert titlebar_updates == [(root, "light")]
    assert page.updated_modes == ["light"]
    assert page_child.updated_modes == ["light"]
    assert sidebar.updated_modes == ["light"]
    assert status_calls[0][0] == "已切换到浅色主题"
    assert status_calls[-1][0] == "就绪"
    assert root.after_calls == [1500]
