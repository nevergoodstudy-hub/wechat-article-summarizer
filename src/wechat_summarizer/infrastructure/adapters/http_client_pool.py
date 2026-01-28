"""HTTP 连接池管理器

提供 httpx.AsyncClient 的单例管理，复用连接池以提高性能。
支持不同域名使用不同配置。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import httpx
from loguru import logger


@dataclass
class ClientConfig:
    """客户端配置
    
    优化后的默认参数：
    - max_keepalive_connections: 30 (提高连接复用率)
    - keepalive_expiry: 60.0 (延长连接保活时间)
    - http2: 启用 HTTP/2 支持 (更高效的多路复用)
    """

    timeout_connect: float = 5.0
    timeout_read: float = 30.0
    timeout_write: float = 30.0
    timeout_pool: float = 5.0
    max_connections: int = 100
    max_keepalive_connections: int = 30  # 优化：增加保活连接数
    keepalive_expiry: float = 60.0  # 优化：延长保活时间
    follow_redirects: bool = True
    http2: bool = False  # 默认关闭，需要 pip install httpx[http2] 才能启用
    proxy: str | None = None
    headers: dict[str, str] = field(default_factory=dict)

    def to_httpx_timeout(self) -> httpx.Timeout:
        """转换为 httpx.Timeout"""
        return httpx.Timeout(
            connect=self.timeout_connect,
            read=self.timeout_read,
            write=self.timeout_write,
            pool=self.timeout_pool,
        )

    def to_httpx_limits(self) -> httpx.Limits:
        """转换为 httpx.Limits"""
        return httpx.Limits(
            max_connections=self.max_connections,
            max_keepalive_connections=self.max_keepalive_connections,
            keepalive_expiry=self.keepalive_expiry,
        )


class HttpClientPool:
    """
    HTTP 连接池管理器（单例）

    管理多个 httpx.AsyncClient 实例，支持按域名配置。
    """

    _instance: HttpClientPool | None = None
    _lock: asyncio.Lock | None = None

    def __new__(cls) -> HttpClientPool:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self._clients: dict[str, httpx.AsyncClient] = {}
        self._configs: dict[str, ClientConfig] = {}
        self._default_config = ClientConfig()
        self._initialized = True
        logger.debug("HttpClientPool 初始化完成")

    @classmethod
    async def get_lock(cls) -> asyncio.Lock:
        """获取异步锁"""
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock

    def configure(self, domain: str, config: ClientConfig) -> None:
        """
        为特定域名配置客户端参数

        Args:
            domain: 域名（如 'mp.weixin.qq.com'）
            config: 客户端配置
        """
        self._configs[domain] = config
        logger.debug(f"已配置域名 {domain} 的客户端参数")

    def set_default_config(self, config: ClientConfig) -> None:
        """设置默认配置"""
        self._default_config = config

    async def get_client(self, domain: str | None = None) -> httpx.AsyncClient:
        """
        获取指定域名的客户端

        Args:
            domain: 域名（可选，None 使用默认配置）

        Returns:
            httpx.AsyncClient 实例
        """
        key = domain or "_default"
        lock = await self.get_lock()

        async with lock:
            if key not in self._clients:
                config = self._configs.get(key, self._default_config) if domain else self._default_config
                self._clients[key] = self._create_client(config)
                logger.debug(f"创建新的 HTTP 客户端: {key}")

            return self._clients[key]

    def _create_client(self, config: ClientConfig) -> httpx.AsyncClient:
        """创建客户端实例
        
        优化特性：
        - 启用 HTTP/2 以支持多路复用
        - 配置连接池参数以提高复用率
        """
        kwargs: dict[str, Any] = {
            "timeout": config.to_httpx_timeout(),
            "limits": config.to_httpx_limits(),
            "follow_redirects": config.follow_redirects,
            "headers": config.headers,
            "http2": config.http2,
        }

        if config.proxy:
            kwargs["proxy"] = config.proxy

        return httpx.AsyncClient(**kwargs)

    async def close_client(self, domain: str | None = None) -> None:
        """
        关闭指定域名的客户端

        Args:
            domain: 域名（可选，None 关闭默认客户端）
        """
        key = domain or "_default"
        lock = await self.get_lock()

        async with lock:
            if key in self._clients:
                await self._clients[key].aclose()
                del self._clients[key]
                logger.debug(f"已关闭 HTTP 客户端: {key}")

    async def close_all(self) -> None:
        """关闭所有客户端"""
        lock = await self.get_lock()

        async with lock:
            for key, client in list(self._clients.items()):
                try:
                    await client.aclose()
                    logger.debug(f"已关闭 HTTP 客户端: {key}")
                except Exception as e:
                    logger.warning(f"关闭客户端 {key} 失败: {e}")

            self._clients.clear()
            logger.info("所有 HTTP 客户端已关闭")

    @property
    def active_clients(self) -> int:
        """活跃客户端数量"""
        return len(self._clients)

    @classmethod
    def reset(cls) -> None:
        """重置单例（用于测试）"""
        if cls._instance is not None:
            # 同步重置，不关闭连接
            cls._instance._clients.clear()
            cls._instance._configs.clear()
            cls._instance = None
            cls._lock = None


# 便捷函数
def get_http_pool() -> HttpClientPool:
    """获取全局连接池实例"""
    return HttpClientPool()


async def get_async_client(domain: str | None = None) -> httpx.AsyncClient:
    """快捷获取异步客户端"""
    return await get_http_pool().get_client(domain)
