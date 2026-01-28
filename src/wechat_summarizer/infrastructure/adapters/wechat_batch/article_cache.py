"""文章列表缓存

缓存已获取的公众号文章列表，减少重复请求。
支持内存缓存和文件持久化。
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger

from ....domain.entities.article_list import ArticleList
from ....infrastructure.config.settings import get_settings


class ArticleListCache:
    """
    文章列表缓存
    
    缓存公众号的文章列表，支持：
    - 内存缓存（快速访问）
    - 文件持久化（跨会话保持）
    - TTL过期机制
    
    使用方法:
        cache = ArticleListCache()
        
        # 保存到缓存
        cache.set(fakeid, article_list)
        
        # 从缓存获取
        cached = cache.get(fakeid)
        if cached:
            print(f"命中缓存: {len(cached)} 篇文章")
    """

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        ttl_hours: int | None = None,
        enabled: bool | None = None,
    ) -> None:
        """初始化缓存
        
        Args:
            cache_dir: 缓存目录（默认使用配置）
            ttl_hours: 缓存有效期（小时）
            enabled: 是否启用缓存
        """
        settings = get_settings()
        
        self._enabled = enabled if enabled is not None else settings.batch.cache_enabled
        self._ttl_hours = ttl_hours or settings.batch.cache_ttl_hours
        
        if cache_dir:
            self._cache_dir = Path(cache_dir)
        else:
            self._cache_dir = Path(settings.batch.cache_dir)
        
        # 内存缓存
        self._memory_cache: dict[str, tuple[ArticleList, float]] = {}
        
        # 确保缓存目录存在
        if self._enabled:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def enabled(self) -> bool:
        """是否启用缓存"""
        return self._enabled

    @property
    def ttl_seconds(self) -> float:
        """TTL（秒）"""
        return self._ttl_hours * 3600

    def _get_cache_path(self, fakeid: str) -> Path:
        """获取缓存文件路径"""
        # 使用fakeid的哈希作为文件名（避免特殊字符问题）
        safe_name = f"articles_{fakeid}.json"
        return self._cache_dir / safe_name

    def get(self, fakeid: str) -> ArticleList | None:
        """获取缓存的文章列表
        
        Args:
            fakeid: 公众号ID
            
        Returns:
            缓存的文章列表，如果不存在或已过期则返回None
        """
        if not self._enabled:
            return None
        
        # 先检查内存缓存
        if fakeid in self._memory_cache:
            article_list, cached_at = self._memory_cache[fakeid]
            if time.time() - cached_at < self.ttl_seconds:
                logger.debug(f"内存缓存命中: {fakeid}")
                return article_list
            else:
                # 已过期，删除
                del self._memory_cache[fakeid]
        
        # 检查文件缓存
        cache_path = self._get_cache_path(fakeid)
        if cache_path.exists():
            try:
                data = json.loads(cache_path.read_text(encoding="utf-8"))
                
                # 检查是否过期
                cached_at = data.get("cached_at", 0)
                if time.time() - cached_at < self.ttl_seconds:
                    article_list = ArticleList.from_dict(data["article_list"])
                    
                    # 加载到内存缓存
                    self._memory_cache[fakeid] = (article_list, cached_at)
                    
                    logger.debug(f"文件缓存命中: {fakeid}")
                    return article_list
                else:
                    # 已过期，删除文件
                    cache_path.unlink()
                    logger.debug(f"缓存已过期: {fakeid}")
                    
            except Exception as e:
                logger.warning(f"读取缓存失败: {e}")
        
        return None

    def set(self, fakeid: str, article_list: ArticleList) -> None:
        """保存文章列表到缓存
        
        Args:
            fakeid: 公众号ID
            article_list: 文章列表
        """
        if not self._enabled:
            return
        
        cached_at = time.time()
        
        # 保存到内存缓存
        self._memory_cache[fakeid] = (article_list, cached_at)
        
        # 保存到文件
        try:
            cache_path = self._get_cache_path(fakeid)
            data = {
                "cached_at": cached_at,
                "article_list": article_list.to_dict(),
            }
            cache_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.debug(f"缓存已保存: {fakeid} ({article_list.count} 篇)")
            
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")

    def delete(self, fakeid: str) -> None:
        """删除指定的缓存
        
        Args:
            fakeid: 公众号ID
        """
        # 删除内存缓存
        if fakeid in self._memory_cache:
            del self._memory_cache[fakeid]
        
        # 删除文件缓存
        cache_path = self._get_cache_path(fakeid)
        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"缓存已删除: {fakeid}")

    def clear(self) -> None:
        """清除所有缓存"""
        # 清除内存缓存
        self._memory_cache.clear()
        
        # 清除文件缓存
        if self._cache_dir.exists():
            for cache_file in self._cache_dir.glob("articles_*.json"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning(f"删除缓存文件失败: {e}")
        
        logger.info("所有缓存已清除")

    def cleanup_expired(self) -> int:
        """清理过期缓存
        
        Returns:
            清理的缓存数量
        """
        cleaned = 0
        
        # 清理内存缓存
        expired_keys = [
            key for key, (_, cached_at) in self._memory_cache.items()
            if time.time() - cached_at >= self.ttl_seconds
        ]
        for key in expired_keys:
            del self._memory_cache[key]
            cleaned += 1
        
        # 清理文件缓存
        if self._cache_dir.exists():
            for cache_file in self._cache_dir.glob("articles_*.json"):
                try:
                    data = json.loads(cache_file.read_text(encoding="utf-8"))
                    cached_at = data.get("cached_at", 0)
                    
                    if time.time() - cached_at >= self.ttl_seconds:
                        cache_file.unlink()
                        cleaned += 1
                        
                except Exception:
                    # 读取失败的文件也删除
                    cache_file.unlink()
                    cleaned += 1
        
        if cleaned > 0:
            logger.info(f"已清理 {cleaned} 个过期缓存")
        
        return cleaned

    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        memory_count = len(self._memory_cache)
        
        file_count = 0
        total_articles = 0
        total_size = 0
        
        if self._cache_dir.exists():
            for cache_file in self._cache_dir.glob("articles_*.json"):
                file_count += 1
                total_size += cache_file.stat().st_size
                
                try:
                    data = json.loads(cache_file.read_text(encoding="utf-8"))
                    article_list_data = data.get("article_list", {})
                    total_articles += article_list_data.get("fetched_count", 0)
                except Exception:
                    pass
        
        return {
            "enabled": self._enabled,
            "ttl_hours": self._ttl_hours,
            "memory_cache_count": memory_count,
            "file_cache_count": file_count,
            "total_articles": total_articles,
            "total_size_kb": round(total_size / 1024, 2),
            "cache_dir": str(self._cache_dir),
        }

    def list_cached_accounts(self) -> list[dict]:
        """列出所有缓存的公众号
        
        Returns:
            缓存信息列表
        """
        cached_accounts = []
        
        if self._cache_dir.exists():
            for cache_file in self._cache_dir.glob("articles_*.json"):
                try:
                    data = json.loads(cache_file.read_text(encoding="utf-8"))
                    article_list_data = data.get("article_list", {})
                    cached_at = data.get("cached_at", 0)
                    
                    # 计算是否过期
                    is_expired = time.time() - cached_at >= self.ttl_seconds
                    
                    cached_accounts.append({
                        "fakeid": article_list_data.get("fakeid", ""),
                        "account_name": article_list_data.get("account_name", ""),
                        "article_count": article_list_data.get("fetched_count", 0),
                        "total_count": article_list_data.get("total_count", 0),
                        "cached_at": datetime.fromtimestamp(cached_at).isoformat(),
                        "is_expired": is_expired,
                    })
                    
                except Exception as e:
                    logger.warning(f"读取缓存文件失败: {cache_file}, {e}")
        
        return cached_accounts
