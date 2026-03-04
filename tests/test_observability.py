"""Observability Metrics 单元测试

测试 MetricsCollector：
- 单例模式
- record_fetch, record_summary 方法
- 内存回退计数器
- get_stats() 统计
"""

from __future__ import annotations

import pytest

from wechat_summarizer.infrastructure.observability.metrics import (
    MetricsCollector,
    MetricsConfig,
    get_metrics,
)


@pytest.mark.unit
class TestMetricsConfig:
    """MetricsConfig 测试类"""

    def test_default_config(self) -> None:
        """测试默认配置"""
        config = MetricsConfig()

        assert config.enabled is True
        assert config.export_interval_seconds == 60
        assert config.prometheus_enabled is False
        assert config.prometheus_port == 9090

    def test_custom_config(self) -> None:
        """测试自定义配置"""
        config = MetricsConfig(
            enabled=False,
            export_interval_seconds=30,
            prometheus_enabled=True,
            prometheus_port=8080,
        )

        assert config.enabled is False
        assert config.export_interval_seconds == 30
        assert config.prometheus_enabled is True
        assert config.prometheus_port == 8080


@pytest.mark.unit
class TestMetricsCollectorSingleton:
    """MetricsCollector 单例模式测试"""

    def setup_method(self) -> None:
        """每个测试前重置单例"""
        MetricsCollector.reset()

    def teardown_method(self) -> None:
        """每个测试后重置单例"""
        MetricsCollector.reset()

    def test_singleton_pattern(self) -> None:
        """测试单例模式"""
        config = MetricsConfig(enabled=True)
        collector1 = MetricsCollector(config)
        collector2 = MetricsCollector()

        assert collector1 is collector2

    def test_singleton_same_instance(self) -> None:
        """测试多次调用返回相同实例"""
        collector1 = MetricsCollector()
        collector2 = MetricsCollector()
        collector3 = MetricsCollector()

        assert collector1 is collector2
        assert collector2 is collector3

    def test_reset_creates_new_instance(self) -> None:
        """测试 reset 后创建新实例"""
        collector1 = MetricsCollector()
        MetricsCollector.reset()
        collector2 = MetricsCollector()

        assert collector1 is not collector2

    def test_get_metrics_returns_singleton(self) -> None:
        """测试 get_metrics 函数返回单例"""
        collector1 = get_metrics()
        collector2 = get_metrics()

        assert collector1 is collector2


@pytest.mark.unit
class TestMetricsCollectorRecording:
    """MetricsCollector 记录方法测试"""

    def setup_method(self) -> None:
        """每个测试前重置单例"""
        MetricsCollector.reset()

    def teardown_method(self) -> None:
        """每个测试后重置单例"""
        MetricsCollector.reset()

    @pytest.fixture
    def collector(self) -> MetricsCollector:
        """创建 MetricsCollector 实例（内存回退模式）"""
        config = MetricsConfig(enabled=True, prometheus_enabled=False)
        return MetricsCollector(config)

    def test_record_fetch(self, collector: MetricsCollector) -> None:
        """测试 record_fetch 方法"""
        collector.record_fetch(scraper="wechat_httpx", duration=1.5, success=True)
        collector.record_fetch(scraper="wechat_httpx", duration=2.0, success=True)
        collector.record_fetch(scraper="generic_httpx", duration=0.5, success=False)

        stats = collector.get_stats()
        counters = stats["counters"]

        # 应该有计数器记录
        assert len(counters) > 0
        # 验证计数器包含预期的键
        fetch_keys = [k for k in counters if "articles_fetched" in k]
        assert len(fetch_keys) > 0

    def test_record_summary(self, collector: MetricsCollector) -> None:
        """测试 record_summary 方法"""
        collector.record_summary(model="simple", duration=0.1, tokens=0, success=True)
        collector.record_summary(model="ollama", duration=2.5, tokens=1500, success=True)
        collector.record_summary(model="openai", duration=1.0, tokens=500, success=False)

        stats = collector.get_stats()
        counters = stats["counters"]

        # 验证计数器
        summary_keys = [k for k in counters if "summaries_generated" in k]
        assert len(summary_keys) > 0

    def test_record_export(self, collector: MetricsCollector) -> None:
        """测试 record_export 方法"""
        collector.record_export(target="markdown", success=True)
        collector.record_export(target="html", success=True)
        collector.record_export(target="word", success=False)

        stats = collector.get_stats()
        counters = stats["counters"]

        # 验证计数器
        export_keys = [k for k in counters if "exports_total" in k]
        assert len(export_keys) > 0

    def test_record_cache_hit_miss(self, collector: MetricsCollector) -> None:
        """测试 record_cache_hit 和 record_cache_miss 方法"""
        collector.record_cache_hit()
        collector.record_cache_hit()
        collector.record_cache_miss()

        stats = collector.get_stats()
        counters = stats["counters"]

        # 验证缓存计数器
        assert "cache_hits_total" in counters
        assert counters["cache_hits_total"] == 2
        assert "cache_misses_total" in counters
        assert counters["cache_misses_total"] == 1


@pytest.mark.unit
class TestMetricsCollectorDisabled:
    """MetricsCollector 禁用状态测试"""

    def setup_method(self) -> None:
        """每个测试前重置单例"""
        MetricsCollector.reset()

    def teardown_method(self) -> None:
        """每个测试后重置单例"""
        MetricsCollector.reset()

    def test_disabled_collector_no_recording(self) -> None:
        """测试禁用状态不记录数据"""
        config = MetricsConfig(enabled=False)
        collector = MetricsCollector(config)

        # 调用各种记录方法
        collector.record_fetch(scraper="test", duration=1.0, success=True)
        collector.record_summary(model="test", duration=1.0, tokens=100, success=True)
        collector.record_export(target="test", success=True)
        collector.record_cache_hit()
        collector.record_cache_miss()

        stats = collector.get_stats()

        # 禁用状态下计数器应为空
        assert len(stats["counters"]) == 0
        assert len(stats["histograms"]) == 0


@pytest.mark.unit
class TestMetricsCollectorStats:
    """MetricsCollector 统计功能测试"""

    def setup_method(self) -> None:
        """每个测试前重置单例"""
        MetricsCollector.reset()

    def teardown_method(self) -> None:
        """每个测试后重置单例"""
        MetricsCollector.reset()

    @pytest.fixture
    def collector(self) -> MetricsCollector:
        """创建 MetricsCollector 实例"""
        config = MetricsConfig(enabled=True, prometheus_enabled=False)
        return MetricsCollector(config)

    def test_get_stats_structure(self, collector: MetricsCollector) -> None:
        """测试 get_stats 返回结构"""
        stats = collector.get_stats()

        assert "counters" in stats
        assert "histograms" in stats
        assert isinstance(stats["counters"], dict)
        assert isinstance(stats["histograms"], dict)

    def test_histogram_stats_calculation(self, collector: MetricsCollector) -> None:
        """测试直方图统计计算"""
        # 记录多个时长值
        collector.record_fetch(scraper="test", duration=1.0, success=True)
        collector.record_fetch(scraper="test", duration=2.0, success=True)
        collector.record_fetch(scraper="test", duration=3.0, success=True)

        stats = collector.get_stats()
        histograms = stats["histograms"]

        # 应该有直方图记录
        assert len(histograms) > 0

        # 验证直方图统计（找到 fetch 相关的直方图）
        for key, value in histograms.items():
            if "fetch_duration" in key:
                assert "count" in value
                assert value["count"] == 3
                assert "sum" in value
                assert "avg" in value
                assert "min" in value
                assert "max" in value
                # 验证计算正确
                assert value["min"] == 1.0
                assert value["max"] == 3.0
                break


@pytest.mark.unit
class TestMetricsCollectorContextManagers:
    """MetricsCollector 上下文管理器测试"""

    def setup_method(self) -> None:
        """每个测试前重置单例"""
        MetricsCollector.reset()

    def teardown_method(self) -> None:
        """每个测试后重置单例"""
        MetricsCollector.reset()

    @pytest.fixture
    def collector(self) -> MetricsCollector:
        """创建 MetricsCollector 实例"""
        config = MetricsConfig(enabled=True, prometheus_enabled=False)
        return MetricsCollector(config)

    def test_measure_fetch_success(self, collector: MetricsCollector) -> None:
        """测试 measure_fetch 上下文管理器（成功）"""
        with collector.measure_fetch("test_scraper"):
            # 模拟抓取操作
            pass

        stats = collector.get_stats()
        counters = stats["counters"]

        # 应该记录成功
        success_keys = [k for k in counters if "success" in k.lower()]
        assert len(success_keys) > 0

    def test_measure_fetch_failure(self, collector: MetricsCollector) -> None:
        """测试 measure_fetch 上下文管理器（失败）"""
        with pytest.raises(ValueError), collector.measure_fetch("test_scraper"):
            raise ValueError("测试错误")

        stats = collector.get_stats()
        counters = stats["counters"]

        # 应该有失败记录
        assert len(counters) > 0

    def test_measure_summary_success(self, collector: MetricsCollector) -> None:
        """测试 measure_summary 上下文管理器（成功）"""
        with collector.measure_summary("simple"):
            # 模拟摘要生成
            pass

        stats = collector.get_stats()
        counters = stats["counters"]

        # 应该有记录
        assert len(counters) > 0

    def test_measure_summary_failure(self, collector: MetricsCollector) -> None:
        """测试 measure_summary 上下文管理器（失败）"""
        with pytest.raises(RuntimeError), collector.measure_summary("ollama"):
            raise RuntimeError("API 错误")

        stats = collector.get_stats()
        counters = stats["counters"]

        # 应该有失败记录
        assert len(counters) > 0


@pytest.mark.unit
class TestMemoryFallbackCounters:
    """内存回退计数器测试"""

    def setup_method(self) -> None:
        """每个测试前重置单例"""
        MetricsCollector.reset()

    def teardown_method(self) -> None:
        """每个测试后重置单例"""
        MetricsCollector.reset()

    @pytest.fixture
    def collector(self) -> MetricsCollector:
        """创建 MetricsCollector 实例（无 OpenTelemetry）"""
        config = MetricsConfig(enabled=True, prometheus_enabled=False)
        return MetricsCollector(config)

    def test_increment_counter_basic(self, collector: MetricsCollector) -> None:
        """测试基本计数器增加"""
        collector._increment_counter("test_counter")
        collector._increment_counter("test_counter")
        collector._increment_counter("test_counter")

        stats = collector.get_stats()
        assert stats["counters"]["test_counter"] == 3

    def test_increment_counter_with_labels(self, collector: MetricsCollector) -> None:
        """测试带标签的计数器增加"""
        labels1 = {"scraper": "wechat", "success": "true"}
        labels2 = {"scraper": "wechat", "success": "false"}

        collector._increment_counter("fetch_total", labels1)
        collector._increment_counter("fetch_total", labels1)
        collector._increment_counter("fetch_total", labels2)

        stats = collector.get_stats()
        counters = stats["counters"]

        # 不同标签应该是不同的计数器
        assert len([k for k in counters if "fetch_total" in k]) == 2

    def test_record_histogram_basic(self, collector: MetricsCollector) -> None:
        """测试基本直方图记录"""
        collector._record_histogram("test_duration", 1.5)
        collector._record_histogram("test_duration", 2.5)
        collector._record_histogram("test_duration", 0.5)

        stats = collector.get_stats()
        histogram = stats["histograms"]["test_duration"]

        assert histogram["count"] == 3
        assert histogram["sum"] == 4.5
        assert histogram["avg"] == 1.5
        assert histogram["min"] == 0.5
        assert histogram["max"] == 2.5

    def test_record_histogram_with_labels(self, collector: MetricsCollector) -> None:
        """测试带标签的直方图记录"""
        labels = {"model": "simple"}

        collector._record_histogram("summary_duration", 1.0, labels)
        collector._record_histogram("summary_duration", 2.0, labels)

        stats = collector.get_stats()
        histograms = stats["histograms"]

        # 应该有带标签的直方图
        assert len(histograms) > 0

    def test_empty_histogram_stats(self, collector: MetricsCollector) -> None:
        """测试空直方图统计"""
        stats = collector.get_stats()

        # 空状态下直方图应为空字典
        assert stats["histograms"] == {}
