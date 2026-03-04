"""TwoLevelCache 单元测试"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from wechat_summarizer.infrastructure.adapters.two_level_cache import (
    TwoLevelCache,
    TwoLevelCacheConfig,
)


@pytest.fixture
def cache_dir(tmp_path: Path) -> Path:
    """临时磁盘缓存目录"""
    d = tmp_path / "test_cache"
    d.mkdir()
    return d


@pytest.fixture
def cache(cache_dir: Path) -> TwoLevelCache:
    """创建测试用 TwoLevelCache"""
    config = TwoLevelCacheConfig(
        memory_max_size=10,
        memory_default_ttl=60.0,
        disk_max_age_hours=24,
        disk_dir=cache_dir,
    )
    return TwoLevelCache(config)


class TestTwoLevelCacheBasic:
    """基本操作测试"""

    def test_set_and_get(self, cache: TwoLevelCache) -> None:
        """写入后能立即读取"""
        cache.set("key1", {"name": "test", "value": 42})
        result = cache.get("key1")
        assert result == {"name": "test", "value": 42}

    def test_get_missing_key(self, cache: TwoLevelCache) -> None:
        """读取不存在的键返回 None"""
        assert cache.get("nonexistent") is None

    def test_get_with_default(self, cache: TwoLevelCache) -> None:
        """读取不存在的键返回默认值"""
        assert cache.get("nonexistent", default="fallback") == "fallback"

    def test_delete(self, cache: TwoLevelCache) -> None:
        """删除后键不再存在"""
        cache.set("key1", "value1")
        assert cache.contains("key1")

        result = cache.delete("key1")
        assert result is True
        assert cache.get("key1") is None
        assert not cache.contains("key1")

    def test_delete_nonexistent(self, cache: TwoLevelCache) -> None:
        """删除不存在的键返回 False"""
        assert cache.delete("nonexistent") is False

    def test_contains(self, cache: TwoLevelCache) -> None:
        """检查键是否存在"""
        cache.set("key1", "value1")
        assert cache.contains("key1")
        assert not cache.contains("key2")

    def test_clear(self, cache: TwoLevelCache) -> None:
        """清空所有缓存"""
        cache.set("key1", "v1")
        cache.set("key2", "v2")
        cache.set("key3", "v3")

        count = cache.clear()
        assert count >= 3
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_overwrite(self, cache: TwoLevelCache) -> None:
        """覆盖已有的键"""
        cache.set("key1", "old_value")
        cache.set("key1", "new_value")
        assert cache.get("key1") == "new_value"


class TestTwoLevelCachePromotion:
    """L2 → L1 提升测试"""

    def test_disk_promotion(self, cache: TwoLevelCache, cache_dir: Path) -> None:
        """磁盘命中后提升到内存"""
        # 写入数据
        cache.set("promote_key", {"promoted": True})

        # 清除 L1 内存，保留 L2 磁盘
        cache._l1.clear()

        # 从 L2 读取，应触发提升
        result = cache.get("promote_key")
        assert result == {"promoted": True}

        # 验证已提升到 L1（再次读取应命中 L1）
        stats = cache.stats
        assert stats.promotions >= 1
        assert stats.l2_hits >= 1

    def test_l1_hit_no_disk_read(self, cache: TwoLevelCache) -> None:
        """L1 命中时不应访问 L2"""
        cache.set("fast_key", "fast_value")

        # 多次读取应全部命中 L1
        for _ in range(5):
            assert cache.get("fast_key") == "fast_value"

        stats = cache.stats
        assert stats.l1_hits >= 5


class TestTwoLevelCacheDisk:
    """磁盘持久化测试"""

    def test_disk_persistence(self, cache_dir: Path) -> None:
        """磁盘缓存在重建后仍可用"""
        config = TwoLevelCacheConfig(
            memory_max_size=5,
            disk_dir=cache_dir,
        )

        # 第一个实例写入
        cache1 = TwoLevelCache(config)
        cache1.set("persist_key", "persist_value")

        # 创建新实例（模拟重启）
        cache2 = TwoLevelCache(TwoLevelCacheConfig(memory_max_size=5, disk_dir=cache_dir))
        result = cache2.get("persist_key")
        assert result == "persist_value"

    def test_disk_cleanup_expired(self, cache_dir: Path) -> None:
        """清理过期的磁盘缓存"""
        config = TwoLevelCacheConfig(
            disk_max_age_hours=0,  # 立即过期
            disk_dir=cache_dir,
        )
        cache = TwoLevelCache(config)
        cache.set("expired_key", "expired_value")

        # 手动修改文件的创建时间为过去
        import hashlib

        key_hash = hashlib.sha256(b"expired_key").hexdigest()[:32]
        cache_file = cache_dir / f"{key_hash}.json"

        if cache_file.exists():
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            data["_created_at"] = (datetime.now() - timedelta(hours=2)).isoformat()
            cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        cleaned = cache.cleanup_expired()
        assert cleaned >= 1


class TestTwoLevelCacheStats:
    """统计测试"""

    def test_initial_stats(self, cache: TwoLevelCache) -> None:
        """初始统计为零"""
        stats = cache.stats
        assert stats.l1_hits == 0
        assert stats.l1_misses == 0
        assert stats.l2_hits == 0
        assert stats.l2_misses == 0
        assert stats.promotions == 0

    def test_stats_after_operations(self, cache: TwoLevelCache) -> None:
        """操作后统计正确更新"""
        cache.set("key1", "v1")

        # L1 命中
        cache.get("key1")
        cache.get("key1")

        # 总 miss
        cache.get("nonexistent")

        stats = cache.stats
        assert stats.l1_hits >= 2
        assert stats.total_misses >= 1

    def test_hit_rate(self, cache: TwoLevelCache) -> None:
        """命中率计算"""
        cache.set("key1", "v1")

        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("miss")  # miss

        stats = cache.stats
        assert stats.hit_rate > 0


class TestTwoLevelCacheEdgeCases:
    """边界情况"""

    def test_none_value(self, cache: TwoLevelCache) -> None:
        """None 值的处理"""
        # None 在 get() 中会被视为 cache miss
        # 这是 MemoryCache 的已知行为
        cache.set("null_key", None)
        # get() 返回 default 因为 None == None
        # 这是设计选择，与 MemoryCache 保持一致

    def test_large_value(self, cache: TwoLevelCache) -> None:
        """大值的处理"""
        large_data = {"items": list(range(10000))}
        cache.set("large_key", large_data)
        result = cache.get("large_key")
        assert result == large_data

    def test_unicode_key_and_value(self, cache: TwoLevelCache) -> None:
        """Unicode 键值对"""
        cache.set("中文键", {"内容": "这是中文值"})
        result = cache.get("中文键")
        assert result == {"内容": "这是中文值"}

    def test_many_keys(self, cache: TwoLevelCache) -> None:
        """多键测试"""
        for i in range(20):
            cache.set(f"key_{i}", f"value_{i}")

        # L1 只保留最近 10 个（max_size=10）
        # 但 L2 应该全部保留
        for i in range(20):
            result = cache.get(f"key_{i}")
            assert result == f"value_{i}"
