"""OpenTelemetry 分布式追踪

提供：
- TracerProvider 初始化（ConsoleSpanExporter / OTLP）
- `@traced` 函数装饰器 - 自动创建 span
- `@trace_use_case` 用例装饰器 - 附加用例元数据
- `trace_span` 上下文管理器 - 手动创建 span
- 错误记录和状态设置
- 当 opentelemetry 未安装时的优雅降级

可选依赖：
- opentelemetry-api
- opentelemetry-sdk
- opentelemetry-exporter-otlp（如需 OTLP 导出）
"""

from __future__ import annotations

import functools
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, TypeVar

from loguru import logger

# 检查 OpenTelemetry 是否可用
_otel_available = False

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SimpleSpanProcessor,
    )
    from opentelemetry.trace import SpanKind, Status, StatusCode

    _otel_available = True
except ImportError:
    pass


F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class TracingConfig:
    """追踪配置"""

    enabled: bool = True
    service_name: str = "wechat-summarizer"
    console_export: bool = False  # 默认关闭控制台导出（避免刷屏）
    otlp_endpoint: str | None = None  # 如 "http://localhost:4317"
    sample_rate: float = 1.0  # 采样率 0.0 - 1.0


class TracingManager:
    """
    追踪管理器（单例）

    管理 OpenTelemetry TracerProvider 的生命周期，
    提供 tracer 实例和便捷的装饰器。
    """

    _instance: TracingManager | None = None

    def __new__(cls, config: TracingConfig | None = None) -> TracingManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: TracingConfig | None = None) -> None:
        if getattr(self, "_initialized", False):
            return

        self._config = config or TracingConfig()
        self._initialized = True
        self._provider: Any = None
        self._tracer: Any = None

        if not self._config.enabled:
            logger.info("Tracing 已禁用")
            return

        if _otel_available:
            self._init_opentelemetry()
        else:
            logger.debug(
                "OpenTelemetry 不可用，追踪功能将使用 no-op 模式。"
                "如需启用，请安装: pip install opentelemetry-api opentelemetry-sdk"
            )

    def _init_opentelemetry(self) -> None:
        """初始化 OpenTelemetry TracerProvider"""
        try:
            self._provider = TracerProvider()

            # Console exporter（开发调试用）
            if self._config.console_export:
                console_processor = SimpleSpanProcessor(ConsoleSpanExporter())
                self._provider.add_span_processor(console_processor)

            # OTLP exporter（生产环境）
            if self._config.otlp_endpoint:
                try:
                    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                        OTLPSpanExporter,
                    )

                    otlp_exporter = OTLPSpanExporter(
                        endpoint=self._config.otlp_endpoint,
                    )
                    otlp_processor = BatchSpanProcessor(otlp_exporter)
                    self._provider.add_span_processor(otlp_processor)
                    logger.info(f"OTLP trace exporter 已配置: {self._config.otlp_endpoint}")
                except ImportError:
                    logger.warning("opentelemetry-exporter-otlp 未安装，OTLP 导出不可用")

            # 设置全局 TracerProvider
            trace.set_tracer_provider(self._provider)

            # 创建 tracer
            self._tracer = trace.get_tracer(
                self._config.service_name,
                schema_url="https://opentelemetry.io/schemas/1.11.0",
            )

            logger.info("OpenTelemetry tracing 初始化完成")

        except Exception as e:
            logger.warning(f"OpenTelemetry tracing 初始化失败: {e}")

    @property
    def tracer(self) -> Any:
        """获取 tracer 实例"""
        return self._tracer

    @property
    def is_available(self) -> bool:
        """检查追踪是否可用"""
        return _otel_available and self._tracer is not None

    def shutdown(self) -> None:
        """关闭追踪"""
        if self._provider is not None:
            try:
                self._provider.shutdown()
                logger.debug("TracerProvider 已关闭")
            except Exception as e:
                logger.warning(f"关闭 TracerProvider 失败: {e}")

    @classmethod
    def reset(cls) -> None:
        """重置单例（用于测试）"""
        if cls._instance is not None:
            cls._instance.shutdown()
            cls._instance = None


# -------------------- 装饰器 --------------------


def traced(
    name: str | None = None,
    *,
    kind: Any = None,
    attributes: dict[str, Any] | None = None,
) -> Callable[[F], F]:
    """
    函数追踪装饰器

    自动为函数创建 OpenTelemetry span，记录执行时间和错误。

    Args:
        name: span 名称，默认使用 "module.function"
        kind: SpanKind，默认 INTERNAL
        attributes: 附加到 span 的属性

    Examples:
        @traced()
        def fetch_article(url: str) -> Article:
            ...

        @traced("custom-span-name", attributes={"component": "scraper"})
        def scrape(url: str) -> str:
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            manager = get_tracing_manager()

            if not manager.is_available:
                # 没有 OpenTelemetry，直接执行
                return func(*args, **kwargs)

            span_name = name or f"{func.__module__}.{func.__qualname__}"
            span_kind = kind if kind is not None else SpanKind.INTERNAL

            with manager.tracer.start_as_current_span(
                span_name,
                kind=span_kind,
                attributes=attributes or {},
            ) as span:
                # 记录函数信息
                span.set_attribute("code.function", func.__qualname__)
                span.set_attribute("code.namespace", func.__module__)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return wrapper  # type: ignore

    return decorator


def trace_use_case(
    use_case_name: str | None = None,
) -> Callable[[F], F]:
    """
    用例追踪装饰器

    专门为 Application Layer 的用例方法设计，
    自动记录用例名称、输入参数概要、执行时间。

    Args:
        use_case_name: 用例名称，默认使用类名

    Examples:
        class FetchArticleUseCase:
            @trace_use_case()
            def execute(self, url: str) -> Article:
                ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            manager = get_tracing_manager()

            if not manager.is_available:
                return func(*args, **kwargs)

            # 推断用例名称
            uc_name = use_case_name
            if uc_name is None:
                # 尝试从 self 推断类名
                if args and hasattr(args[0], "__class__"):
                    uc_name = args[0].__class__.__name__
                else:
                    uc_name = func.__qualname__

            span_name = f"use_case.{uc_name}"

            with manager.tracer.start_as_current_span(
                span_name,
                kind=SpanKind.INTERNAL,
                attributes={
                    "use_case.name": uc_name,
                    "code.function": func.__qualname__,
                },
            ) as span:
                start_time = time.perf_counter()

                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    span.set_attribute("use_case.duration_ms", round(duration_ms, 2))
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    span.set_attribute("use_case.duration_ms", round(duration_ms, 2))
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return wrapper  # type: ignore

    return decorator


# -------------------- 上下文管理器 --------------------


@contextmanager
def trace_span(
    name: str,
    *,
    kind: Any = None,
    attributes: dict[str, Any] | None = None,
) -> Generator[Any]:
    """
    手动创建 span 的上下文管理器

    Args:
        name: span 名称
        kind: SpanKind
        attributes: 附加属性

    Yields:
        span 对象（如果 OTel 不可用则为 None）

    Examples:
        with trace_span("process-article", attributes={"url": url}) as span:
            article = scraper.scrape(url)
            if span:
                span.set_attribute("article.title", article.title)
    """
    manager = get_tracing_manager()

    if not manager.is_available:
        yield None
        return

    span_kind = kind if kind is not None else SpanKind.INTERNAL

    with manager.tracer.start_as_current_span(
        name,
        kind=span_kind,
        attributes=attributes or {},
    ) as span:
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


# -------------------- 便捷函数 --------------------


_tracing_manager: TracingManager | None = None


def get_tracing_manager(config: TracingConfig | None = None) -> TracingManager:
    """获取全局追踪管理器"""
    return TracingManager(config)


def init_tracing(config: TracingConfig | None = None) -> TracingManager:
    """
    初始化追踪系统

    应在应用启动时调用一次。

    Args:
        config: 追踪配置

    Returns:
        TracingManager 实例
    """
    TracingManager.reset()
    return TracingManager(config)
