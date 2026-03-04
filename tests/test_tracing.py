"""OpenTelemetry Tracing 单元测试

测试追踪装饰器和上下文管理器在 OTel 不可用时的降级行为。
"""

from __future__ import annotations

import pytest

from wechat_summarizer.infrastructure.observability.tracing import (
    TracingConfig,
    TracingManager,
    get_tracing_manager,
    init_tracing,
    trace_span,
    trace_use_case,
    traced,
)


@pytest.fixture(autouse=True)
def reset_tracing():
    """每个测试前重置追踪管理器"""
    TracingManager.reset()
    yield
    TracingManager.reset()


class TestTracingManagerLifecycle:
    """追踪管理器生命周期测试"""

    def test_singleton(self) -> None:
        """单例模式"""
        m1 = TracingManager()
        m2 = TracingManager()
        assert m1 is m2

    def test_disabled_config(self) -> None:
        """禁用配置"""
        config = TracingConfig(enabled=False)
        manager = TracingManager(config)
        assert not manager.is_available

    def test_reset(self) -> None:
        """重置后创建新实例"""
        m1 = TracingManager()
        TracingManager.reset()
        m2 = TracingManager()
        # 重置后不是同一个实例
        assert m1 is not m2

    def test_get_tracing_manager(self) -> None:
        """便捷函数获取管理器"""
        manager = get_tracing_manager()
        assert manager is not None

    def test_init_tracing(self) -> None:
        """初始化追踪系统"""
        manager = init_tracing(TracingConfig(enabled=False))
        assert manager is not None
        assert not manager.is_available


class TestTracedDecorator:
    """@traced 装饰器测试"""

    def test_traced_preserves_function(self) -> None:
        """装饰器不改变函数行为"""

        @traced()
        def add(a: int, b: int) -> int:
            return a + b

        assert add(1, 2) == 3
        assert add.__name__ == "add"

    def test_traced_with_custom_name(self) -> None:
        """自定义 span 名称"""

        @traced("custom-add")
        def add(a: int, b: int) -> int:
            return a + b

        assert add(3, 4) == 7

    def test_traced_with_attributes(self) -> None:
        """附加属性"""

        @traced(attributes={"component": "test"})
        def compute() -> str:
            return "result"

        assert compute() == "result"

    def test_traced_propagates_exception(self) -> None:
        """异常正确传播"""

        @traced()
        def failing():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            failing()

    def test_traced_with_kwargs(self) -> None:
        """支持关键字参数"""

        @traced()
        def greet(name: str = "world") -> str:
            return f"hello {name}"

        assert greet(name="test") == "hello test"


class TestTraceUseCaseDecorator:
    """@trace_use_case 装饰器测试"""

    def test_use_case_decorator(self) -> None:
        """用例装饰器基本功能"""

        class MyUseCase:
            @trace_use_case()
            def execute(self, data: str) -> str:
                return f"processed: {data}"

        uc = MyUseCase()
        assert uc.execute("input") == "processed: input"

    def test_use_case_with_custom_name(self) -> None:
        """自定义用例名称"""

        class MyUseCase:
            @trace_use_case("FetchArticle")
            def execute(self, url: str) -> str:
                return url

        uc = MyUseCase()
        assert uc.execute("https://example.com") == "https://example.com"

    def test_use_case_exception(self) -> None:
        """用例异常传播"""

        class FailingUseCase:
            @trace_use_case()
            def execute(self) -> None:
                raise RuntimeError("use case failed")

        uc = FailingUseCase()
        with pytest.raises(RuntimeError, match="use case failed"):
            uc.execute()


class TestTraceSpanContextManager:
    """trace_span 上下文管理器测试"""

    def test_basic_span(self) -> None:
        """基本 span 创建"""
        with trace_span("test-operation"):
            result = 1 + 1
        assert result == 2

    def test_span_with_attributes(self) -> None:
        """带属性的 span"""
        with trace_span("test-op", attributes={"key": "value"}):
            pass
        # span 可能为 None（如果 OTel 不可用）

    def test_span_exception(self) -> None:
        """span 中的异常"""
        with pytest.raises(ValueError, match="span error"), trace_span("failing-op"):
            raise ValueError("span error")

    def test_span_yields_none_without_otel(self) -> None:
        """OTel 不可用时 yield None"""
        TracingManager.reset()
        manager = TracingManager(TracingConfig(enabled=False))

        with trace_span("test") as span:
            # 当追踪被禁用时，span 为 None
            if not manager.is_available:
                assert span is None


class TestTracingGracefulDegradation:
    """优雅降级测试（当 OTel 不可用时）"""

    def test_all_decorators_work_without_otel(self) -> None:
        """所有装饰器在无 OTel 时正常工作"""
        TracingManager.reset()
        init_tracing(TracingConfig(enabled=False))

        @traced()
        def func1() -> int:
            return 42

        class UC:
            @trace_use_case()
            def execute(self) -> str:
                return "ok"

        assert func1() == 42
        assert UC().execute() == "ok"

        with trace_span("test"):
            pass

    def test_performance_overhead_minimal(self) -> None:
        """装饰器性能开销最小"""
        import time

        @traced()
        def fast_func() -> int:
            return 1

        start = time.perf_counter()
        for _ in range(1000):
            fast_func()
        elapsed = time.perf_counter() - start

        # 1000 次调用应该在合理时间内完成（< 1 秒）
        assert elapsed < 1.0
