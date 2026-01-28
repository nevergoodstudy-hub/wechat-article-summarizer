"""OpenTelemetry Metrics 收集器

收集应用运行时的关键指标：
- 文章抓取计数和耗时
- 摘要生成计数、耗时和 Token 使用量
- 导出计数
- 缓存命中/未命中

可选依赖：
- opentelemetry-api
- opentelemetry-sdk
- prometheus-client（如需暴露 Prometheus 端点）
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator

from loguru import logger

# 检查 OpenTelemetry 是否可用
_otel_available = False
_prometheus_available = False

try:
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )

    _otel_available = True
except ImportError:
    pass

try:
    from prometheus_client import Counter, Histogram, start_http_server

    _prometheus_available = True
except ImportError:
    pass


@dataclass
class MetricsConfig:
    """Metrics 配置"""

    enabled: bool = True
    export_interval_seconds: int = 60
    prometheus_enabled: bool = False
    prometheus_port: int = 9090


class MetricsCollector:
    """
    Metrics 收集器

    支持 OpenTelemetry 和 Prometheus 两种导出方式。
    """

    _instance: MetricsCollector | None = None

    def __new__(cls, config: MetricsConfig | None = None) -> MetricsCollector:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: MetricsConfig | None = None) -> None:
        if getattr(self, "_initialized", False):
            return

        self._config = config or MetricsConfig()
        self._initialized = True

        # 内存计数器（备用）
        self._counters: dict[str, int] = {}
        self._histograms: dict[str, list[float]] = {}

        if not self._config.enabled:
            logger.info("Metrics 已禁用")
            return

        # 初始化 OpenTelemetry
        if _otel_available:
            self._init_opentelemetry()
        else:
            logger.warning("OpenTelemetry 不可用，使用内存计数器")

        # 初始化 Prometheus
        if self._config.prometheus_enabled and _prometheus_available:
            self._init_prometheus()

    def _init_opentelemetry(self) -> None:
        """初始化 OpenTelemetry"""
        try:
            reader = PeriodicExportingMetricReader(
                ConsoleMetricExporter(),
                export_interval_millis=self._config.export_interval_seconds * 1000,
            )
            provider = MeterProvider(metric_readers=[reader])
            metrics.set_meter_provider(provider)

            self._meter = metrics.get_meter("wechat_summarizer")

            # 创建 instruments
            self._articles_fetched = self._meter.create_counter(
                "articles_fetched_total",
                description="Total number of articles fetched",
            )
            self._fetch_duration = self._meter.create_histogram(
                "articles_fetch_duration_seconds",
                description="Time spent fetching articles",
            )
            self._summaries_generated = self._meter.create_counter(
                "summaries_generated_total",
                description="Total number of summaries generated",
            )
            self._summary_duration = self._meter.create_histogram(
                "summary_duration_seconds",
                description="Time spent generating summaries",
            )
            self._summary_tokens = self._meter.create_counter(
                "summary_tokens_total",
                description="Total tokens used for summarization",
            )
            self._exports_total = self._meter.create_counter(
                "exports_total",
                description="Total number of exports",
            )
            self._cache_hits = self._meter.create_counter(
                "cache_hits_total",
                description="Total cache hits",
            )
            self._cache_misses = self._meter.create_counter(
                "cache_misses_total",
                description="Total cache misses",
            )

            logger.info("OpenTelemetry metrics 初始化完成")

        except Exception as e:
            logger.warning(f"OpenTelemetry 初始化失败: {e}")

    def _init_prometheus(self) -> None:
        """初始化 Prometheus"""
        try:
            # Prometheus metrics
            self._prom_articles_fetched = Counter(
                "articles_fetched_total",
                "Total number of articles fetched",
                ["scraper"],
            )
            self._prom_fetch_duration = Histogram(
                "articles_fetch_duration_seconds",
                "Time spent fetching articles",
                ["scraper"],
            )
            self._prom_summaries_generated = Counter(
                "summaries_generated_total",
                "Total number of summaries generated",
                ["model"],
            )
            self._prom_summary_duration = Histogram(
                "summary_duration_seconds",
                "Time spent generating summaries",
                ["model"],
            )
            self._prom_exports_total = Counter(
                "exports_total",
                "Total number of exports",
                ["target"],
            )
            self._prom_cache_hits = Counter(
                "cache_hits_total",
                "Total cache hits",
            )
            self._prom_cache_misses = Counter(
                "cache_misses_total",
                "Total cache misses",
            )

            # 启动 HTTP server
            start_http_server(self._config.prometheus_port)
            logger.info(f"Prometheus metrics 端点已启动: http://localhost:{self._config.prometheus_port}")

        except Exception as e:
            logger.warning(f"Prometheus 初始化失败: {e}")

    # -------------------- 记录方法 --------------------

    def record_fetch(self, scraper: str, duration: float, success: bool = True) -> None:
        """记录文章抓取"""
        if not self._config.enabled:
            return

        labels = {"scraper": scraper, "success": str(success).lower()}

        if _otel_available and hasattr(self, "_articles_fetched"):
            self._articles_fetched.add(1, labels)
            self._fetch_duration.record(duration, labels)

        if _prometheus_available and hasattr(self, "_prom_articles_fetched"):
            self._prom_articles_fetched.labels(scraper=scraper).inc()
            self._prom_fetch_duration.labels(scraper=scraper).observe(duration)

        # 内存计数器
        self._increment_counter("articles_fetched_total", labels)
        self._record_histogram("articles_fetch_duration_seconds", duration, labels)

    def record_summary(
        self,
        model: str,
        duration: float,
        tokens: int = 0,
        success: bool = True,
    ) -> None:
        """记录摘要生成"""
        if not self._config.enabled:
            return

        labels = {"model": model, "success": str(success).lower()}

        if _otel_available and hasattr(self, "_summaries_generated"):
            self._summaries_generated.add(1, labels)
            self._summary_duration.record(duration, labels)
            if tokens > 0:
                self._summary_tokens.add(tokens, {"model": model})

        if _prometheus_available and hasattr(self, "_prom_summaries_generated"):
            self._prom_summaries_generated.labels(model=model).inc()
            self._prom_summary_duration.labels(model=model).observe(duration)

        self._increment_counter("summaries_generated_total", labels)
        self._record_histogram("summary_duration_seconds", duration, labels)

    def record_export(self, target: str, success: bool = True) -> None:
        """记录导出"""
        if not self._config.enabled:
            return

        labels = {"target": target, "success": str(success).lower()}

        if _otel_available and hasattr(self, "_exports_total"):
            self._exports_total.add(1, labels)

        if _prometheus_available and hasattr(self, "_prom_exports_total"):
            self._prom_exports_total.labels(target=target).inc()

        self._increment_counter("exports_total", labels)

    def record_cache_hit(self) -> None:
        """记录缓存命中"""
        if not self._config.enabled:
            return

        if _otel_available and hasattr(self, "_cache_hits"):
            self._cache_hits.add(1)

        if _prometheus_available and hasattr(self, "_prom_cache_hits"):
            self._prom_cache_hits.inc()

        self._increment_counter("cache_hits_total")

    def record_cache_miss(self) -> None:
        """记录缓存未命中"""
        if not self._config.enabled:
            return

        if _otel_available and hasattr(self, "_cache_misses"):
            self._cache_misses.add(1)

        if _prometheus_available and hasattr(self, "_prom_cache_misses"):
            self._prom_cache_misses.inc()

        self._increment_counter("cache_misses_total")

    # -------------------- 上下文管理器 --------------------

    @contextmanager
    def measure_fetch(self, scraper: str) -> Generator[None, None, None]:
        """测量抓取耗时的上下文管理器"""
        start = time.perf_counter()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration = time.perf_counter() - start
            self.record_fetch(scraper, duration, success)

    @contextmanager
    def measure_summary(self, model: str) -> Generator[None, None, None]:
        """测量摘要生成耗时的上下文管理器"""
        start = time.perf_counter()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration = time.perf_counter() - start
            self.record_summary(model, duration, success=success)

    # -------------------- 内存计数器 --------------------

    def _increment_counter(self, name: str, labels: dict[str, str] | None = None) -> None:
        """增加内存计数器"""
        key = f"{name}:{labels}" if labels else name
        self._counters[key] = self._counters.get(key, 0) + 1

    def _record_histogram(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> None:
        """记录直方图值"""
        key = f"{name}:{labels}" if labels else name
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)

    def get_stats(self) -> dict[str, Any]:
        """获取内存计数器统计"""
        stats = {"counters": dict(self._counters)}

        # 计算直方图统计
        histogram_stats = {}
        for key, values in self._histograms.items():
            if values:
                histogram_stats[key] = {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                }
        stats["histograms"] = histogram_stats

        return stats

    @classmethod
    def reset(cls) -> None:
        """重置单例（用于测试）"""
        cls._instance = None


# 便捷函数
def get_metrics(config: MetricsConfig | None = None) -> MetricsCollector:
    """获取全局 metrics 收集器"""
    return MetricsCollector(config)
