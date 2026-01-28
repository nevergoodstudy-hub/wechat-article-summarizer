"""内存缓存层

提供高效的内存缓存，支持 LRU 淘汰策略和 TTL 过期机制。
用于减少重复的 API 请求和磁盘 I/O，提高应用响应速度。

特性：
- LRU (Least Recently Used) 淘汰策略
- TTL (Time To Live) 过期机制
- 线程安全
- 泛型支持
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar

from loguru import logger

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class CacheEntry(Generic[V]):
    """缓存条目"""
    
    value: V
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    ttl: float | None = None  # None 表示永不过期
    
    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def touch(self) -> None:
        """更新访问时间"""
        self.accessed_at = time.time()


class MemoryCache(Generic[K, V]):
    """
    内存缓存
    
    实现 LRU + TTL 的缓存策略，提供高效的内存缓存机制。
    
    使用方法：
        cache = MemoryCache[str, dict](max_size=100, default_ttl=300)
        
        # 设置缓存
        cache.set("key1", {"data": "value"})
        
        # 获取缓存
        value = cache.get("key1")
        
        # 带默认值获取
        value = cache.get("key2", default={"empty": True})
        
        # 使用装饰器
        @cache.cached(ttl=60)
        def expensive_function(arg):
            return compute(arg)
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float | None = 300.0,  # 默认 5 分钟
        cleanup_interval: float = 60.0,  # 清理间隔
    ) -> None:
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认过期时间（秒），None 表示永不过期
            cleanup_interval: 自动清理间隔（秒）
        """
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cleanup_interval = cleanup_interval
        
        self._cache: OrderedDict[K, CacheEntry[V]] = OrderedDict()
        self._lock = threading.RLock()
        self._last_cleanup = time.time()
        
        # 统计信息
        self._hits = 0
        self._misses = 0
    
    @property
    def size(self) -> int:
        """当前缓存大小"""
        return len(self._cache)
    
    @property
    def max_size(self) -> int:
        """最大缓存大小"""
        return self._max_size
    
    @property
    def stats(self) -> dict:
        """缓存统计信息"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "size": self.size,
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
        }
    
    def get(self, key: K, default: V | None = None) -> V | None:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            缓存值或默认值
        """
        with self._lock:
            self._maybe_cleanup()
            
            if key not in self._cache:
                self._misses += 1
                return default
            
            entry = self._cache[key]
            
            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                return default
            
            # LRU: 移动到末尾
            self._cache.move_to_end(key)
            entry.touch()
            
            self._hits += 1
            return entry.value
    
    def set(
        self,
        key: K,
        value: V,
        ttl: float | None = None,
    ) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 使用默认值
        """
        with self._lock:
            self._maybe_cleanup()
            
            # 如果已存在，先删除
            if key in self._cache:
                del self._cache[key]
            
            # LRU: 淘汰最旧的条目
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            
            # 创建新条目
            entry = CacheEntry(
                value=value,
                ttl=ttl if ttl is not None else self._default_ttl,
            )
            self._cache[key] = entry
    
    def delete(self, key: K) -> bool:
        """
        删除缓存条目
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> int:
        """
        清空缓存
        
        Returns:
            清除的条目数量
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            return count
    
    def contains(self, key: K) -> bool:
        """
        检查键是否存在且未过期
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            if entry.is_expired:
                del self._cache[key]
                return False
            
            return True
    
    def get_or_set(
        self,
        key: K,
        factory: Callable[[], V],
        ttl: float | None = None,
    ) -> V:
        """
        获取缓存，如果不存在则使用工厂函数创建并缓存
        
        Args:
            key: 缓存键
            factory: 创建值的工厂函数
            ttl: 过期时间
            
        Returns:
            缓存值或新创建的值
        """
        value = self.get(key)
        if value is not None:
            return value
        
        # 不在锁内调用工厂函数，避免死锁
        new_value = factory()
        self.set(key, new_value, ttl=ttl)
        return new_value
    
    def _maybe_cleanup(self) -> None:
        """可能执行清理（如果距上次清理超过间隔）"""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        self._last_cleanup = now
        self._cleanup_expired()
    
    def _cleanup_expired(self) -> int:
        """清理过期条目"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"缓存清理：移除 {len(expired_keys)} 个过期条目")
        
        return len(expired_keys)
    
    def cached(
        self,
        ttl: float | None = None,
        key_func: Callable[..., K] | None = None,
    ):
        """
        缓存装饰器
        
        Args:
            ttl: 过期时间
            key_func: 自定义键生成函数，默认使用参数元组
            
        Returns:
            装饰器函数
        """
        def decorator(func: Callable[..., V]) -> Callable[..., V]:
            def wrapper(*args, **kwargs) -> V:
                # 生成缓存键
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = (func.__name__, args, tuple(sorted(kwargs.items())))
                
                # 尝试从缓存获取
                cached_value = self.get(cache_key)  # type: ignore
                if cached_value is not None:
                    return cached_value
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 存入缓存
                self.set(cache_key, result, ttl=ttl)  # type: ignore
                
                return result
            
            return wrapper
        return decorator


# 全局缓存实例
_global_cache: MemoryCache[str, Any] | None = None
_global_cache_lock = threading.Lock()


def get_global_cache() -> MemoryCache[str, Any]:
    """获取全局缓存实例"""
    global _global_cache
    
    if _global_cache is None:
        with _global_cache_lock:
            if _global_cache is None:
                _global_cache = MemoryCache(max_size=1000, default_ttl=300)
    
    return _global_cache


def cache_get(key: str, default: Any = None) -> Any:
    """便捷函数：从全局缓存获取"""
    return get_global_cache().get(key, default)


def cache_set(key: str, value: Any, ttl: float | None = None) -> None:
    """便捷函数：设置全局缓存"""
    get_global_cache().set(key, value, ttl=ttl)


def cache_delete(key: str) -> bool:
    """便捷函数：删除全局缓存"""
    return get_global_cache().delete(key)
