"""两级缓存：内存 LRU (L1) + 磁盘持久化 (L2)

将 MemoryCache 和 LocalJsonStorage 组合为统一的两级缓存，提供：
- L1 (内存)：基于 LRU + TTL 的快速内存缓存
- L2 (磁盘)：基于 JSON 的持久化磁盘缓存
- 自动提升：磁盘命中后自动提升到内存
- 统一接口：对外暴露简单的 get / set / delete
- 线程安全：两级缓存均通过锁保护
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger

from .memory_cache import MemoryCache


@dataclass
class TwoLevelCacheConfig:
    """两级缓存配置"""

    # L1 内存缓存
    memory_max_size: int = 200
    memory_default_ttl: float | None = 300.0  # 5 分钟

    # L2 磁盘缓存
    disk_max_age_hours: int = 24 * 7  # 7 天
    disk_max_entries: int = 2000
    disk_dir: Path | None = None  # None 使用默认路径


@dataclass
class TwoLevelCacheStats:
    """两级缓存统计"""

    l1_hits: int
    l1_misses: int
    l1_size: int
    l1_max_size: int
    l2_hits: int
    l2_misses: int
    l2_size: int
    promotions: int  # 从 L2 提升到 L1 的次数
    total_hits: int
    total_misses: int
    hit_rate: float


class TwoLevelCache:
    """
    两级缓存

    L1 (内存) → L2 (磁盘)

    读取顺序：
    1. 检查 L1 内存缓存
    2. 如果 L1 未命中，检查 L2 磁盘缓存
    3. 如果 L2 命中，提升到 L1（promotion）
    4. 如果都未命中，返回 None

    写入：
    - 同时写入 L1 和 L2

    使用方法：
        cache = TwoLevelCache(config)

        # 写入
        cache.set("key", {"data": "value"})

        # 读取
        value = cache.get("key")

        # 删除
        cache.delete("key")

        # 统计
        stats = cache.stats
    """

    def __init__(self, config: TwoLevelCacheConfig | None = None) -> None:
        self._config = config or TwoLevelCacheConfig()
        self._lock = threading.RLock()

        # L1 内存缓存
        self._l1 = MemoryCache[str, Any](
            max_size=self._config.memory_max_size,
            default_ttl=self._config.memory_default_ttl,
        )

        # L2 磁盘缓存
        self._disk_dir = self._config.disk_dir or self._default_disk_dir()
        self._disk_dir.mkdir(parents=True, exist_ok=True)

        # 统计
        self._l2_hits = 0
        self._l2_misses = 0
        self._promotions = 0

        logger.debug(
            f"TwoLevelCache 初始化完成 "
            f"(L1: max_size={self._config.memory_max_size}, "
            f"L2: dir={self._disk_dir})"
        )

    @staticmethod
    def _default_disk_dir() -> Path:
        """默认磁盘缓存目录"""
        return Path.home() / ".wechat_summarizer" / "cache" / "two_level"

    # -------------------- 核心操作 --------------------

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值

        查找顺序: L1 内存 → L2 磁盘

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        # 1. 检查 L1
        value = self._l1.get(key)
        if value is not None:
            return value

        # 2. 检查 L2 磁盘
        with self._lock:
            disk_value = self._disk_get(key)

            if disk_value is not None:
                self._l2_hits += 1
                self._promotions += 1

                # 提升到 L1
                self._l1.set(key, disk_value)
                logger.debug(f"L2 命中并提升到 L1: {key[:32]}...")
                return disk_value

            self._l2_misses += 1
            return default

    def set(
        self,
        key: str,
        value: Any,
        memory_ttl: float | None = None,
    ) -> None:
        """
        设置缓存值（同时写入 L1 和 L2）

        Args:
            key: 缓存键
            value: 缓存值（必须是 JSON 可序列化的）
            memory_ttl: L1 内存缓存 TTL（秒），None 使用默认值
        """
        # 写入 L1
        self._l1.set(key, value, ttl=memory_ttl)

        # 写入 L2
        with self._lock:
            self._disk_set(key, value)

    def delete(self, key: str) -> bool:
        """
        删除缓存条目（从 L1 和 L2 都删除）

        Args:
            key: 缓存键

        Returns:
            是否至少从一级中删除成功
        """
        l1_deleted = self._l1.delete(key)

        with self._lock:
            l2_deleted = self._disk_delete(key)

        return l1_deleted or l2_deleted

    def contains(self, key: str) -> bool:
        """检查键是否存在于任一级缓存"""
        if self._l1.contains(key):
            return True

        with self._lock:
            return self._disk_exists(key)

    def clear(self) -> int:
        """
        清空所有缓存

        Returns:
            清除的总条目数
        """
        l1_count = self._l1.clear()

        with self._lock:
            l2_count = self._disk_clear()
            self._l2_hits = 0
            self._l2_misses = 0
            self._promotions = 0

        return l1_count + l2_count

    def cleanup_expired(self) -> int:
        """
        清理过期条目

        Returns:
            清理的条目数
        """
        # L1 内部自动清理（通过 TTL）
        # L2 手动清理过期文件
        with self._lock:
            return self._disk_cleanup_expired()

    # -------------------- 统计 --------------------

    @property
    def stats(self) -> TwoLevelCacheStats:
        """获取缓存统计信息"""
        l1_stats = self._l1.stats

        total_hits = l1_stats["hits"] + self._l2_hits
        total_misses = self._l2_misses  # L1 miss 但 L2 miss 才是真正的 miss
        total_requests = total_hits + total_misses
        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0

        with self._lock:
            l2_size = sum(1 for _ in self._disk_dir.glob("*.json"))

        return TwoLevelCacheStats(
            l1_hits=l1_stats["hits"],
            l1_misses=l1_stats["misses"],
            l1_size=l1_stats["size"],
            l1_max_size=l1_stats["max_size"],
            l2_hits=self._l2_hits,
            l2_misses=self._l2_misses,
            l2_size=l2_size,
            promotions=self._promotions,
            total_hits=total_hits,
            total_misses=total_misses,
            hit_rate=round(hit_rate, 2),
        )

    # -------------------- L2 磁盘操作 --------------------

    def _key_to_path(self, key: str) -> Path:
        """将缓存键转换为磁盘路径"""
        import hashlib

        safe_name = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
        return self._disk_dir / f"{safe_name}.json"

    def _disk_get(self, key: str) -> Any | None:
        """从磁盘获取"""
        path = self._key_to_path(key)
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))

            # 检查过期
            created_at = data.get("_created_at")
            if created_at:
                created = datetime.fromisoformat(created_at)
                max_age = timedelta(hours=self._config.disk_max_age_hours)
                if datetime.now() - created > max_age:
                    path.unlink(missing_ok=True)
                    return None

            return data.get("value")

        except Exception as e:
            logger.warning(f"磁盘缓存读取失败: {key[:32]}... - {e}")
            return None

    def _disk_set(self, key: str, value: Any) -> None:
        """写入磁盘"""
        path = self._key_to_path(key)

        try:
            data = {
                "key": key,
                "value": value,
                "_created_at": datetime.now().isoformat(),
            }

            # 原子写入
            tmp_path = path.with_suffix(".tmp")
            tmp_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )

            import os

            os.replace(tmp_path, path)

        except Exception as e:
            logger.warning(f"磁盘缓存写入失败: {key[:32]}... - {e}")

    def _disk_delete(self, key: str) -> bool:
        """从磁盘删除"""
        path = self._key_to_path(key)
        if path.exists():
            try:
                path.unlink()
                return True
            except Exception as e:
                logger.warning(f"磁盘缓存删除失败: {key[:32]}... - {e}")
        return False

    def _disk_exists(self, key: str) -> bool:
        """检查磁盘中是否存在"""
        return self._key_to_path(key).exists()

    def _disk_clear(self) -> int:
        """清空磁盘缓存"""
        count = 0
        for f in self._disk_dir.glob("*.json"):
            try:
                f.unlink()
                count += 1
            except Exception:
                pass
        return count

    def _disk_cleanup_expired(self) -> int:
        """清理过期的磁盘缓存"""
        cleaned = 0
        cutoff = datetime.now() - timedelta(hours=self._config.disk_max_age_hours)

        for cache_file in self._disk_dir.glob("*.json"):
            try:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                created_at = data.get("_created_at")

                if created_at:
                    created = datetime.fromisoformat(created_at)
                    if created < cutoff:
                        cache_file.unlink()
                        cleaned += 1
                else:
                    # 没有时间戳，使用文件修改时间
                    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if mtime < cutoff:
                        cache_file.unlink()
                        cleaned += 1

            except Exception as e:
                logger.warning(f"清理磁盘缓存失败 {cache_file}: {e}")

        if cleaned > 0:
            logger.info(f"已清理 {cleaned} 条过期磁盘缓存")

        return cleaned


# -------------------- 全局实例 --------------------

_global_two_level_cache: TwoLevelCache | None = None
_global_lock = threading.Lock()


def get_two_level_cache(
    config: TwoLevelCacheConfig | None = None,
) -> TwoLevelCache:
    """获取全局两级缓存实例"""
    global _global_two_level_cache

    if _global_two_level_cache is None:
        with _global_lock:
            if _global_two_level_cache is None:
                _global_two_level_cache = TwoLevelCache(config)

    return _global_two_level_cache
