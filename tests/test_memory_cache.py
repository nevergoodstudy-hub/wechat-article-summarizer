"""MemoryCache 内存缓存测试

测试 LRU 淘汰、TTL 过期、线程安全、装饰器等核心行为。
"""

from __future__ import annotations

import time

import pytest

from wechat_summarizer.infrastructure.adapters.memory_cache import (
    CacheEntry,
    MemoryCache,
)


class TestCacheEntry:
    """CacheEntry 测试"""

    @pytest.mark.unit
    def test_entry_not_expired_without_ttl(self) -> None:
        """无 TTL 的条目永不过期"""
        entry = CacheEntry(value="test", ttl=None)
        assert entry.is_expired is False

    @pytest.mark.unit
    def test_entry_not_expired_within_ttl(self) -> None:
        """TTL 内的条目未过期"""
        entry = CacheEntry(value="test", ttl=9999)
        assert entry.is_expired is False

    @pytest.mark.unit
    def test_entry_expired_after_ttl(self) -> None:
        """超过 TTL 的条目已过期"""
        entry = CacheEntry(value="test", ttl=0.01)
        # 模拟 created_at 在很久之前
        entry.created_at = time.time() - 100
        assert entry.is_expired is True

    @pytest.mark.unit
    def test_touch_updates_accessed_at(self) -> None:
        """touch 更新访问时间"""
        entry = CacheEntry(value="test")
        old = entry.accessed_at
        time.sleep(0.01)
        entry.touch()
        assert entry.accessed_at >= old


class TestMemoryCache:
    """MemoryCache 测试"""

    @pytest.fixture
    def cache(self) -> MemoryCache[str, str]:
        return MemoryCache(max_size=5, default_ttl=None, cleanup_interval=9999)

    # ---- get / set ----

    @pytest.mark.unit
    def test_set_and_get(self, cache: MemoryCache) -> None:
        """基本 set/get"""
        cache.set("k1", "v1")
        assert cache.get("k1") == "v1"

    @pytest.mark.unit
    def test_get_missing_returns_default(self, cache: MemoryCache) -> None:
        """不存在的 key 返回默认值"""
        assert cache.get("missing") is None
        assert cache.get("missing", "fallback") == "fallback"

    @pytest.mark.unit
    def test_set_overwrites_existing(self, cache: MemoryCache) -> None:
        """重复 set 覆盖旧值"""
        cache.set("k1", "old")
        cache.set("k1", "new")
        assert cache.get("k1") == "new"
        assert cache.size == 1

    # ---- delete ----

    @pytest.mark.unit
    def test_delete_existing_key(self, cache: MemoryCache) -> None:
        """删除已存在的 key"""
        cache.set("k1", "v1")
        assert cache.delete("k1") is True
        assert cache.get("k1") is None

    @pytest.mark.unit
    def test_delete_missing_key(self, cache: MemoryCache) -> None:
        """删除不存在的 key 返回 False"""
        assert cache.delete("nope") is False

    # ---- clear ----

    @pytest.mark.unit
    def test_clear(self, cache: MemoryCache) -> None:
        """清空缓存"""
        cache.set("a", "1")
        cache.set("b", "2")
        count = cache.clear()
        assert count == 2
        assert cache.size == 0

    # ---- contains ----

    @pytest.mark.unit
    def test_contains_existing(self, cache: MemoryCache) -> None:
        cache.set("k1", "v1")
        assert cache.contains("k1") is True

    @pytest.mark.unit
    def test_contains_missing(self, cache: MemoryCache) -> None:
        assert cache.contains("nope") is False

    # ---- LRU eviction ----

    @pytest.mark.unit
    def test_lru_eviction(self) -> None:
        """超出 max_size 时淘汰最旧条目"""
        cache: MemoryCache[str, int] = MemoryCache(
            max_size=3, default_ttl=None, cleanup_interval=9999
        )
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        # 访问 a 使其变为最近使用
        cache.get("a")
        # 添加 d，应淘汰 b（最久未使用）
        cache.set("d", 4)

        assert cache.contains("a") is True
        assert cache.contains("b") is False
        assert cache.contains("c") is True
        assert cache.contains("d") is True

    @pytest.mark.unit
    def test_max_size_respected(self) -> None:
        """缓存大小不超过 max_size"""
        cache: MemoryCache[str, int] = MemoryCache(
            max_size=3, default_ttl=None, cleanup_interval=9999
        )
        for i in range(10):
            cache.set(f"k{i}", i)
        assert cache.size <= 3

    # ---- TTL expiry ----

    @pytest.mark.unit
    def test_ttl_expiry_on_get(self) -> None:
        """过期条目在 get 时被淘汰"""
        cache: MemoryCache[str, str] = MemoryCache(
            max_size=10, default_ttl=0.01, cleanup_interval=9999
        )
        cache.set("k1", "v1")
        # 手动将 created_at 设为过去
        cache._cache["k1"].created_at = time.time() - 100
        assert cache.get("k1") is None

    @pytest.mark.unit
    def test_ttl_expiry_on_contains(self) -> None:
        """过期条目在 contains 时被清除"""
        cache: MemoryCache[str, str] = MemoryCache(
            max_size=10, default_ttl=0.01, cleanup_interval=9999
        )
        cache.set("k1", "v1")
        cache._cache["k1"].created_at = time.time() - 100
        assert cache.contains("k1") is False

    @pytest.mark.unit
    def test_custom_ttl_per_item(self, cache: MemoryCache) -> None:
        """每个条目可以有独立 TTL"""
        cache.set("short", "val", ttl=0.01)
        cache.set("long", "val", ttl=9999)
        cache._cache["short"].created_at = time.time() - 100
        assert cache.get("short") is None
        assert cache.get("long") == "val"

    # ---- stats ----

    @pytest.mark.unit
    def test_stats_tracking(self, cache: MemoryCache) -> None:
        """统计信息正确"""
        cache.set("k1", "v1")
        cache.get("k1")  # hit
        cache.get("missing")  # miss

        stats = cache.stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["hit_rate"] == 50.0

    @pytest.mark.unit
    def test_stats_after_clear(self, cache: MemoryCache) -> None:
        """clear 后统计信息重置"""
        cache.set("k1", "v1")
        cache.get("k1")
        cache.clear()

        stats = cache.stats
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    # ---- get_or_set ----

    @pytest.mark.unit
    def test_get_or_set_creates_value(self, cache: MemoryCache) -> None:
        """get_or_set 在缓存 miss 时调用工厂函数"""
        result = cache.get_or_set("k1", lambda: "created")
        assert result == "created"
        assert cache.get("k1") == "created"

    @pytest.mark.unit
    def test_get_or_set_returns_cached(self, cache: MemoryCache) -> None:
        """get_or_set 在缓存 hit 时不调用工厂函数"""
        cache.set("k1", "existing")
        factory_called = []
        result = cache.get_or_set("k1", lambda: factory_called.append(1) or "new")
        assert result == "existing"
        assert factory_called == []

    # ---- cached decorator ----

    @pytest.mark.unit
    def test_cached_decorator(self) -> None:
        """cached 装饰器缓存函数结果"""
        cache: MemoryCache = MemoryCache(max_size=100, default_ttl=None, cleanup_interval=9999)
        call_count = 0

        @cache.cached(ttl=None)
        def expensive(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        assert expensive(5) == 10
        assert expensive(5) == 10  # 从缓存获取
        assert call_count == 1

        assert expensive(3) == 6  # 不同参数，重新计算
        assert call_count == 2

    # ---- properties ----

    @pytest.mark.unit
    def test_size_and_max_size(self, cache: MemoryCache) -> None:
        """size 和 max_size 属性"""
        assert cache.size == 0
        assert cache.max_size == 5
        cache.set("k1", "v1")
        assert cache.size == 1
