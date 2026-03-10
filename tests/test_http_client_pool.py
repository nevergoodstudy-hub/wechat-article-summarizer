"""HttpClientPool 连接池测试

测试单例模式、客户端配置、获取/关闭客户端。
"""

from __future__ import annotations

import pytest

from wechat_summarizer.infrastructure.adapters.http_client_pool import (
    ClientConfig,
    HttpClientPool,
)
from wechat_summarizer.shared.utils.ssrf_protection import SSRFSafeTransport


@pytest.fixture(autouse=True)
def _reset_pool():
    """每个测试后重置单例"""
    yield
    HttpClientPool.reset()


class TestClientConfig:
    """ClientConfig 测试"""

    @pytest.mark.unit
    def test_default_config(self) -> None:
        """默认配置值"""
        config = ClientConfig()
        assert config.timeout_connect == 5.0
        assert config.timeout_read == 30.0
        assert config.max_connections == 100
        assert config.follow_redirects is False
        assert config.http2 is False

    @pytest.mark.unit
    def test_to_httpx_timeout(self) -> None:
        """转换为 httpx.Timeout"""
        config = ClientConfig(timeout_connect=1.0, timeout_read=2.0)
        timeout = config.to_httpx_timeout()
        assert timeout.connect == 1.0
        assert timeout.read == 2.0

    @pytest.mark.unit
    def test_to_httpx_limits(self) -> None:
        """转换为 httpx.Limits"""
        config = ClientConfig(max_connections=50, max_keepalive_connections=10)
        limits = config.to_httpx_limits()
        assert limits.max_connections == 50
        assert limits.max_keepalive_connections == 10


class TestHttpClientPool:
    """HttpClientPool 测试"""

    @pytest.mark.unit
    def test_singleton(self) -> None:
        """单例模式：两次创建返回相同实例"""
        pool1 = HttpClientPool()
        pool2 = HttpClientPool()
        assert pool1 is pool2

    @pytest.mark.unit
    def test_reset_clears_singleton(self) -> None:
        """reset 清除单例"""
        pool1 = HttpClientPool()
        HttpClientPool.reset()
        pool2 = HttpClientPool()
        assert pool1 is not pool2

    @pytest.mark.unit
    def test_configure_domain(self) -> None:
        """为域名配置客户端参数"""
        pool = HttpClientPool()
        config = ClientConfig(timeout_read=60.0)
        pool.configure("example.com", config)
        # 配置已存储
        assert "example.com" in pool._configs

    @pytest.mark.unit
    def test_set_default_config(self) -> None:
        """设置默认配置"""
        pool = HttpClientPool()
        config = ClientConfig(timeout_read=99.0)
        pool.set_default_config(config)
        assert pool._default_config.timeout_read == 99.0

    @pytest.mark.unit
    def test_active_clients_initially_zero(self) -> None:
        """初始无活跃客户端"""
        pool = HttpClientPool()
        assert pool.active_clients == 0

    @pytest.mark.asyncio
    async def test_get_client_creates_client(self) -> None:
        """get_client 创建新客户端"""
        pool = HttpClientPool()
        client = await pool.get_client("test.com")

        assert client is not None
        assert isinstance(client._transport, SSRFSafeTransport)
        assert client.follow_redirects is False
        assert pool.active_clients == 1

        await pool.close_all()

    @pytest.mark.asyncio
    async def test_get_client_reuses_existing(self) -> None:
        """同域名多次获取返回相同客户端"""
        pool = HttpClientPool()
        client1 = await pool.get_client("test.com")
        client2 = await pool.get_client("test.com")

        assert client1 is client2
        assert pool.active_clients == 1

        await pool.close_all()

    @pytest.mark.asyncio
    async def test_get_default_client(self) -> None:
        """不指定域名获取默认客户端"""
        pool = HttpClientPool()
        client = await pool.get_client()

        assert client is not None
        assert pool.active_clients == 1

        await pool.close_all()

    @pytest.mark.asyncio
    async def test_different_domains_different_clients(self) -> None:
        """不同域名获取不同客户端"""
        pool = HttpClientPool()
        c1 = await pool.get_client("a.com")
        c2 = await pool.get_client("b.com")

        assert c1 is not c2
        assert pool.active_clients == 2

        await pool.close_all()

    @pytest.mark.asyncio
    async def test_close_client(self) -> None:
        """关闭指定域名的客户端"""
        pool = HttpClientPool()
        await pool.get_client("test.com")
        assert pool.active_clients == 1

        await pool.close_client("test.com")
        assert pool.active_clients == 0

    @pytest.mark.asyncio
    async def test_close_all(self) -> None:
        """关闭所有客户端"""
        pool = HttpClientPool()
        await pool.get_client("a.com")
        await pool.get_client("b.com")
        assert pool.active_clients == 2

        await pool.close_all()
        assert pool.active_clients == 0

    @pytest.mark.asyncio
    async def test_close_nonexistent_client(self) -> None:
        """关闭不存在的客户端不报错"""
        pool = HttpClientPool()
        await pool.close_client("nonexistent.com")  # 不应抛出
