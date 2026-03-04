"""GUIEventBus 事件总线测试

测试发布/订阅模式的核心行为。
"""

from __future__ import annotations

import pytest

from wechat_summarizer.presentation.gui.event_bus import GUIEventBus


class TestGUIEventBus:
    """GUIEventBus 测试"""

    @pytest.fixture
    def bus(self) -> GUIEventBus:
        return GUIEventBus()

    # ---- subscribe / publish ----

    @pytest.mark.unit
    def test_subscribe_and_publish(self, bus: GUIEventBus) -> None:
        """订阅后可以收到发布的事件"""
        received: list[dict] = []
        bus.subscribe("test_event", lambda **data: received.append(data))

        bus.publish("test_event", key="value")

        assert len(received) == 1
        assert received[0] == {"key": "value"}

    @pytest.mark.unit
    def test_multiple_subscribers(self, bus: GUIEventBus) -> None:
        """同一事件支持多个订阅者"""
        calls: list[str] = []
        bus.subscribe("evt", lambda **_: calls.append("a"))
        bus.subscribe("evt", lambda **_: calls.append("b"))

        bus.publish("evt")

        assert calls == ["a", "b"]

    @pytest.mark.unit
    def test_publish_without_subscribers(self, bus: GUIEventBus) -> None:
        """无订阅者时发布不报错"""
        bus.publish("no_listeners", foo="bar")  # 不应抛出

    @pytest.mark.unit
    def test_publish_with_no_data(self, bus: GUIEventBus) -> None:
        """发布事件可以不携带数据"""
        called = []
        bus.subscribe("ping", lambda **_: called.append(True))
        bus.publish("ping")
        assert called == [True]

    @pytest.mark.unit
    def test_different_events_isolated(self, bus: GUIEventBus) -> None:
        """不同事件之间隔离"""
        a_calls: list[str] = []
        b_calls: list[str] = []
        bus.subscribe("a", lambda **_: a_calls.append("a"))
        bus.subscribe("b", lambda **_: b_calls.append("b"))

        bus.publish("a")

        assert a_calls == ["a"]
        assert b_calls == []

    # ---- unsubscribe ----

    @pytest.mark.unit
    def test_unsubscribe_via_returned_function(self, bus: GUIEventBus) -> None:
        """subscribe 返回的函数可以取消订阅"""
        calls: list[int] = []
        unsub = bus.subscribe("evt", lambda **_: calls.append(1))

        bus.publish("evt")
        assert len(calls) == 1

        unsub()
        bus.publish("evt")
        assert len(calls) == 1  # 不再收到

    @pytest.mark.unit
    def test_unsubscribe_directly(self, bus: GUIEventBus) -> None:
        """直接调用 unsubscribe 取消订阅"""
        calls: list[int] = []

        def handler(**_):
            calls.append(1)

        bus.subscribe("evt", handler)
        bus.publish("evt")
        assert len(calls) == 1

        bus.unsubscribe("evt", handler)
        bus.publish("evt")
        assert len(calls) == 1

    @pytest.mark.unit
    def test_unsubscribe_nonexistent_handler(self, bus: GUIEventBus) -> None:
        """取消未注册的处理器不报错"""
        bus.unsubscribe("evt", lambda: None)  # 不应抛出

    @pytest.mark.unit
    def test_unsubscribe_nonexistent_event(self, bus: GUIEventBus) -> None:
        """取消不存在事件的处理器不报错"""
        bus.unsubscribe("nonexistent", lambda: None)

    # ---- clear ----

    @pytest.mark.unit
    def test_clear_removes_all_subscriptions(self, bus: GUIEventBus) -> None:
        """clear 清除所有订阅"""
        calls: list[str] = []
        bus.subscribe("a", lambda **_: calls.append("a"))
        bus.subscribe("b", lambda **_: calls.append("b"))

        bus.clear()
        bus.publish("a")
        bus.publish("b")

        assert calls == []

    # ---- error resilience ----

    @pytest.mark.unit
    def test_handler_exception_does_not_stop_others(self, bus: GUIEventBus) -> None:
        """某个处理器抛出异常不影响其他处理器"""
        calls: list[str] = []

        def bad_handler(**_):
            raise RuntimeError("oops")

        bus.subscribe("evt", bad_handler)
        bus.subscribe("evt", lambda **_: calls.append("ok"))

        bus.publish("evt")

        assert calls == ["ok"]

    @pytest.mark.unit
    def test_publish_passes_keyword_args(self, bus: GUIEventBus) -> None:
        """发布事件正确传递关键字参数"""
        received = {}

        def handler(**data):
            received.update(data)

        bus.subscribe("update", handler)
        bus.publish("update", status="ok", count=42)

        assert received == {"status": "ok", "count": 42}
