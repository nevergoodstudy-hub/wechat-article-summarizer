"""GUI 导航事件接线回归测试。"""

from __future__ import annotations

import pytest

from wechat_summarizer.presentation.gui import app as gui_app
from wechat_summarizer.presentation.gui.event_bus import GUIEventBus


@pytest.mark.unit
def test_navigation_event_routes_to_expected_page_switch_method() -> None:
    gui = gui_app.WechatSummarizerGUI.__new__(gui_app.WechatSummarizerGUI)
    gui.event_bus = GUIEventBus()
    gui._event_bus_subscriptions = []
    calls: list[tuple[str, str]] = []
    gui._show_page = lambda page_id: calls.append(("plain", page_id))
    gui._show_page_animated = lambda page_id: calls.append(("animated", page_id))

    gui._bind_event_bus()
    gui.event_bus.publish("navigate", page_id="single", animated=False)
    gui.event_bus.publish("navigate", page_id="settings", animated=True)

    assert calls == [("plain", "single"), ("animated", "settings")]


@pytest.mark.unit
def test_clearing_event_bus_subscriptions_stops_navigation_delivery() -> None:
    gui = gui_app.WechatSummarizerGUI.__new__(gui_app.WechatSummarizerGUI)
    gui.event_bus = GUIEventBus()
    gui._event_bus_subscriptions = []
    calls: list[tuple[str, str]] = []
    gui._show_page = lambda page_id: calls.append(("plain", page_id))
    gui._show_page_animated = lambda page_id: calls.append(("animated", page_id))

    gui._bind_event_bus()
    gui._clear_event_bus_subscriptions()
    gui.event_bus.publish("navigate", page_id="history", animated=True)

    assert calls == []
