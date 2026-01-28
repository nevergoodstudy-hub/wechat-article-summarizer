"""批量获取基础设施组件的单元测试"""

import asyncio
import pytest
import time
import tempfile
from pathlib import Path

from src.wechat_summarizer.infrastructure.adapters.wechat_batch.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    AdaptiveRateLimiter,
)
from src.wechat_summarizer.infrastructure.adapters.wechat_batch.article_cache import (
    ArticleListCache,
)
from src.wechat_summarizer.domain.entities.article_list import (
    ArticleList,
    ArticleListItem,
)


class TestRateLimiter:
    """频率限制器测试"""

    def test_create_limiter(self):
        """测试创建限制器"""
        config = RateLimitConfig(
            requests_per_minute=30,
            min_interval=1.0,
            max_interval=5.0,
        )
        limiter = RateLimiter(config)
        
        assert limiter.config.requests_per_minute == 30
        assert limiter.current_interval == config.base_interval

    def test_default_config(self):
        """测试默认配置"""
        limiter = RateLimiter()
        
        assert limiter.config.requests_per_minute == 20
        assert limiter.config.min_interval == 2.0
        assert limiter.config.max_interval == 5.0

    @pytest.mark.asyncio
    async def test_wait_first_request(self):
        """测试首次请求无需等待"""
        limiter = RateLimiter(RateLimitConfig(min_interval=0.1))
        
        start = time.time()
        await limiter.wait()
        elapsed = time.time() - start
        
        # 首次请求应该几乎不等待
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_wait_enforces_interval(self):
        """测试等待强制执行间隔"""
        limiter = RateLimiter(RateLimitConfig(
            requests_per_minute=600,  # 允许较快
            min_interval=0.1,
            max_interval=0.2,
        ))
        
        await limiter.wait()
        
        start = time.time()
        await limiter.wait()
        elapsed = time.time() - start
        
        # 第二次请求应该等待约 min_interval
        assert elapsed >= 0.09

    def test_report_success(self):
        """测试成功报告"""
        config = RateLimitConfig(min_interval=2.0, max_interval=5.0, adaptive=True)
        limiter = RateLimiter(config)
        limiter._current_interval = 4.0
        
        limiter.report_success()
        
        # 成功后间隔应该减少
        assert limiter.current_interval < 4.0
        assert limiter.current_interval >= 2.0

    def test_report_error_rate_limit(self):
        """测试频率限制错误报告"""
        config = RateLimitConfig(min_interval=2.0, max_interval=10.0, adaptive=True)
        limiter = RateLimiter(config)
        limiter._current_interval = 3.0
        
        limiter.report_error(is_rate_limit=True)
        
        # 频率限制错误后间隔应该翻倍
        assert limiter.current_interval == 6.0

    def test_report_error_other(self):
        """测试其他错误报告"""
        config = RateLimitConfig(min_interval=2.0, max_interval=10.0, adaptive=True)
        limiter = RateLimiter(config)
        limiter._current_interval = 3.0
        
        limiter.report_error(is_rate_limit=False)
        
        # 其他错误后间隔应该小幅增加
        assert limiter.current_interval == pytest.approx(3.6, rel=0.01)

    def test_reset(self):
        """测试重置"""
        limiter = RateLimiter()
        limiter._current_interval = 10.0
        limiter._consecutive_errors = 5
        
        limiter.reset()
        
        assert limiter.current_interval == limiter.config.base_interval
        assert limiter._consecutive_errors == 0

    def test_stats(self):
        """测试统计信息"""
        limiter = RateLimiter()
        limiter._total_requests = 10
        limiter._total_waits = 5.0
        
        stats = limiter.stats
        
        assert stats["total_requests"] == 10
        assert stats["total_wait_time"] == 5.0
        assert stats["avg_wait_time"] == 0.5

    @pytest.mark.asyncio
    async def test_context_manager_success(self):
        """测试上下文管理器成功场景"""
        limiter = RateLimiter(RateLimitConfig(min_interval=0.01, adaptive=True))
        limiter._current_interval = 1.0
        
        async with limiter:
            pass  # 模拟成功请求
        
        # 成功后间隔应该减少
        assert limiter.current_interval < 1.0

    @pytest.mark.asyncio
    async def test_context_manager_error(self):
        """测试上下文管理器错误场景"""
        limiter = RateLimiter(RateLimitConfig(min_interval=0.01, max_interval=10.0, adaptive=True))
        limiter._current_interval = 1.0
        
        try:
            async with limiter:
                raise ValueError("rate limit exceeded")
        except ValueError:
            pass
        
        # 错误后间隔应该增加
        assert limiter.current_interval > 1.0


class TestAdaptiveRateLimiter:
    """自适应频率限制器测试"""

    def test_create_adaptive_limiter(self):
        """测试创建自适应限制器"""
        limiter = AdaptiveRateLimiter()
        
        assert limiter._response_times is not None

    def test_record_response_time(self):
        """测试记录响应时间"""
        config = RateLimitConfig(min_interval=2.0, max_interval=10.0)
        limiter = AdaptiveRateLimiter(config)
        limiter._current_interval = 3.0
        
        # 记录快速响应
        for _ in range(5):
            limiter.record_response_time(1.0)
        
        # 快速响应应该减少间隔
        assert limiter.current_interval < 3.0

    def test_record_slow_response_time(self):
        """测试记录慢响应时间"""
        config = RateLimitConfig(min_interval=2.0, max_interval=10.0)
        limiter = AdaptiveRateLimiter(config)
        limiter._current_interval = 3.0
        
        # 记录慢响应
        for _ in range(5):
            limiter.record_response_time(6.0)
        
        # 慢响应应该增加间隔
        assert limiter.current_interval > 3.0


class TestArticleListCache:
    """文章列表缓存测试"""

    @pytest.fixture
    def temp_cache_dir(self):
        """创建临时缓存目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_create_cache(self, temp_cache_dir):
        """测试创建缓存"""
        cache = ArticleListCache(
            cache_dir=temp_cache_dir,
            ttl_hours=24,
            enabled=True,
        )
        
        assert cache.enabled is True
        assert cache.ttl_seconds == 24 * 3600

    def test_cache_disabled(self, temp_cache_dir):
        """测试禁用缓存"""
        cache = ArticleListCache(
            cache_dir=temp_cache_dir,
            enabled=False,
        )
        
        article_list = ArticleList(fakeid="test", account_name="测试")
        cache.set("test", article_list)
        
        result = cache.get("test")
        assert result is None

    def test_set_and_get(self, temp_cache_dir):
        """测试设置和获取缓存"""
        cache = ArticleListCache(
            cache_dir=temp_cache_dir,
            ttl_hours=24,
            enabled=True,
        )
        
        article_list = ArticleList(fakeid="test", account_name="测试公众号")
        article_list.add_item(ArticleListItem(aid="1", title="文章1", link="http://1"))
        
        cache.set("test", article_list)
        
        result = cache.get("test")
        
        assert result is not None
        assert result.fakeid == "test"
        assert result.account_name == "测试公众号"
        assert result.count == 1

    def test_get_nonexistent(self, temp_cache_dir):
        """测试获取不存在的缓存"""
        cache = ArticleListCache(cache_dir=temp_cache_dir)
        
        result = cache.get("nonexistent")
        
        assert result is None

    def test_delete(self, temp_cache_dir):
        """测试删除缓存"""
        cache = ArticleListCache(cache_dir=temp_cache_dir)
        
        article_list = ArticleList(fakeid="test", account_name="测试")
        cache.set("test", article_list)
        
        cache.delete("test")
        
        result = cache.get("test")
        assert result is None

    def test_clear(self, temp_cache_dir):
        """测试清除所有缓存"""
        cache = ArticleListCache(cache_dir=temp_cache_dir)
        
        cache.set("test1", ArticleList(fakeid="1", account_name="测试1"))
        cache.set("test2", ArticleList(fakeid="2", account_name="测试2"))
        
        cache.clear()
        
        assert cache.get("test1") is None
        assert cache.get("test2") is None

    def test_get_stats(self, temp_cache_dir):
        """测试获取统计信息"""
        cache = ArticleListCache(cache_dir=temp_cache_dir)
        
        article_list = ArticleList(fakeid="test", account_name="测试")
        article_list.add_item(ArticleListItem(aid="1", title="文章1", link="http://1"))
        cache.set("test", article_list)
        
        stats = cache.get_stats()
        
        assert stats["enabled"] is True
        assert stats["file_cache_count"] >= 1

    def test_list_cached_accounts(self, temp_cache_dir):
        """测试列出缓存的公众号"""
        cache = ArticleListCache(cache_dir=temp_cache_dir)
        
        cache.set("test1", ArticleList(fakeid="1", account_name="公众号1"))
        cache.set("test2", ArticleList(fakeid="2", account_name="公众号2"))
        
        cached = cache.list_cached_accounts()
        
        assert len(cached) == 2
        names = [c["account_name"] for c in cached]
        assert "公众号1" in names
        assert "公众号2" in names

    def test_memory_cache(self, temp_cache_dir):
        """测试内存缓存"""
        cache = ArticleListCache(cache_dir=temp_cache_dir)
        
        article_list = ArticleList(fakeid="test", account_name="测试")
        cache.set("test", article_list)
        
        # 第一次获取会从文件加载到内存
        cache.get("test")
        
        # 检查内存缓存
        assert "test" in cache._memory_cache

    def test_file_persistence(self, temp_cache_dir):
        """测试文件持久化"""
        # 第一个缓存实例
        cache1 = ArticleListCache(cache_dir=temp_cache_dir)
        article_list = ArticleList(fakeid="test", account_name="测试")
        article_list.add_item(ArticleListItem(aid="1", title="文章", link="http://1"))
        cache1.set("test", article_list)
        
        # 第二个缓存实例（模拟重启）
        cache2 = ArticleListCache(cache_dir=temp_cache_dir)
        result = cache2.get("test")
        
        assert result is not None
        assert result.account_name == "测试"
        assert result.count == 1
