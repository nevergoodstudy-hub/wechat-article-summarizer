"""SSRF 防护模块测试

覆盖 ssrf_protection.py 中的:
- SSRFSafeTransport.is_ip_blocked: IP 黑名单检查
- SSRFSafeTransport.resolve_and_validate: DNS 解析 + 验证
- SSRFSafeTransport.validate_url: URL 完整验证
- safe_fetch: 安全 HTTP 请求 (含重定向)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from wechat_summarizer.shared.utils.ssrf_protection import (
    SSRFBlockedError,
    SSRFSafeSyncTransport,
    SSRFSafeTransport,
    create_safe_async_client,
    safe_fetch,
    safe_fetch_sync,
)

# ── is_ip_blocked ──────────────────────────────────────


class TestIsIpBlocked:
    """IP 黑名单检查测试"""

    @pytest.mark.parametrize(
        "ip",
        [
            "127.0.0.1",
            "127.0.0.2",
            "127.255.255.255",
            "10.0.0.1",
            "10.255.255.255",
            "172.16.0.1",
            "172.31.255.255",
            "192.168.0.1",
            "192.168.255.255",
            "0.0.0.0",
            "169.254.169.254",  # 云元数据端点
            "224.0.0.1",  # 组播
            "255.255.255.255",  # 广播
        ],
    )
    def test_blocks_private_and_reserved_ipv4(self, ip: str):
        """封锁所有 IPv4 私有/保留地址"""
        assert SSRFSafeTransport.is_ip_blocked(ip) is True

    @pytest.mark.parametrize(
        "ip",
        [
            "::1",  # IPv6 回环
            "fc00::1",  # IPv6 ULA
            "fe80::1",  # IPv6 链路本地
            "ff02::1",  # IPv6 组播
        ],
    )
    def test_blocks_private_ipv6(self, ip: str):
        """封锁 IPv6 私有/保留地址"""
        assert SSRFSafeTransport.is_ip_blocked(ip) is True

    def test_blocks_ipv6_mapped_ipv4_private(self):
        """封锁 IPv6-mapped IPv4 私有地址"""
        assert SSRFSafeTransport.is_ip_blocked("::ffff:127.0.0.1") is True
        assert SSRFSafeTransport.is_ip_blocked("::ffff:10.0.0.1") is True
        assert SSRFSafeTransport.is_ip_blocked("::ffff:192.168.1.1") is True

    @pytest.mark.parametrize(
        "ip",
        [
            "8.8.8.8",
            "1.1.1.1",
            "140.82.121.3",  # GitHub
            "93.184.216.34",  # example.com
        ],
    )
    def test_allows_public_ipv4(self, ip: str):
        """允许公网 IPv4 地址"""
        assert SSRFSafeTransport.is_ip_blocked(ip) is False

    def test_blocks_unparseable_ip(self):
        """无法解析的 IP 格式默认阻止"""
        assert SSRFSafeTransport.is_ip_blocked("not-an-ip") is True
        assert SSRFSafeTransport.is_ip_blocked("") is True

    def test_blocks_carrier_grade_nat(self):
        """封锁运营商级 NAT 地址 (100.64.0.0/10)"""
        assert SSRFSafeTransport.is_ip_blocked("100.64.0.1") is True
        assert SSRFSafeTransport.is_ip_blocked("100.127.255.255") is True


# ── resolve_and_validate ───────────────────────────────


class TestResolveAndValidate:
    """DNS 解析 + 验证测试"""

    def test_blocks_localhost_hostname(self):
        """封锁 localhost 主机名"""
        with pytest.raises(SSRFBlockedError, match="Blocked hostname"):
            SSRFSafeTransport.resolve_and_validate("localhost")

    def test_blocks_metadata_hostname(self):
        """封锁云元数据主机名"""
        with pytest.raises(SSRFBlockedError, match="Blocked hostname"):
            SSRFSafeTransport.resolve_and_validate("metadata.google.internal")

    def test_blocks_metadata_ip(self):
        """封锁云元数据 IP"""
        with pytest.raises(SSRFBlockedError, match="Blocked"):
            SSRFSafeTransport.resolve_and_validate("169.254.169.254")

    def test_blocks_private_ip_literal(self):
        """直接输入私有 IP 字面量时阻止"""
        with pytest.raises(SSRFBlockedError, match="Blocked IP"):
            SSRFSafeTransport.resolve_and_validate("127.0.0.1")
        with pytest.raises(SSRFBlockedError, match="Blocked IP"):
            SSRFSafeTransport.resolve_and_validate("10.0.0.1")

    @pytest.mark.parametrize("host", ["2130706433", "0177.0.0.1"])
    def test_blocks_alternative_ip_notation(self, host: str):
        """阻断替代 IP 表示法（十进制整型/前导零）"""
        with pytest.raises(SSRFBlockedError, match="alternative IP notation"):
            SSRFSafeTransport.resolve_and_validate(host)

    def test_allows_public_ip_literal(self):
        """直接输入公网 IP 时允许"""
        ips = SSRFSafeTransport.resolve_and_validate("8.8.8.8")
        assert ips == ["8.8.8.8"]

    def test_dns_resolving_to_private_ip_blocked(self):
        """DNS 解析到私有 IP 时阻止"""
        fake_addrs = [
            (2, 1, 6, "", ("192.168.1.1", 443)),
        ]
        with (
            patch("socket.getaddrinfo", return_value=fake_addrs),
            pytest.raises(SSRFBlockedError, match="blocked IP"),
        ):
            SSRFSafeTransport.resolve_and_validate("evil.example.com")

    def test_dns_resolving_to_public_ip_allowed(self):
        """DNS 解析到公网 IP 时允许"""
        fake_addrs = [
            (2, 1, 6, "", ("93.184.216.34", 443)),
        ]
        with patch("socket.getaddrinfo", return_value=fake_addrs):
            ips = SSRFSafeTransport.resolve_and_validate("example.com")
            assert "93.184.216.34" in ips

    def test_dns_failure_raises(self):
        """DNS 解析失败时抛出异常"""
        import socket

        with (
            patch("socket.getaddrinfo", side_effect=socket.gaierror("DNS failed")),
            pytest.raises(SSRFBlockedError, match="DNS resolution failed"),
        ):
            SSRFSafeTransport.resolve_and_validate("nonexistent.invalid")

    def test_empty_dns_results_raises(self):
        """DNS 返回空结果时抛出异常"""
        with (
            patch("socket.getaddrinfo", return_value=[]),
            pytest.raises(SSRFBlockedError, match="No valid IP"),
        ):
            SSRFSafeTransport.resolve_and_validate("empty.example.com")


# ── validate_url ───────────────────────────────────────


class TestValidateUrl:
    """URL 完整验证测试"""

    def test_rejects_non_http_scheme(self):
        """拒绝非 HTTP/HTTPS 协议"""
        with pytest.raises(SSRFBlockedError, match="Disallowed URL scheme"):
            SSRFSafeTransport.validate_url("ftp://example.com/file")
        with pytest.raises(SSRFBlockedError, match="Disallowed URL scheme"):
            SSRFSafeTransport.validate_url("file:///etc/passwd")
        with pytest.raises(SSRFBlockedError, match="Disallowed URL scheme"):
            SSRFSafeTransport.validate_url("javascript:alert(1)")

    def test_rejects_missing_hostname(self):
        """拒绝缺少主机名的 URL"""
        with pytest.raises(SSRFBlockedError, match="missing hostname"):
            SSRFSafeTransport.validate_url("http://")

    def test_rejects_url_with_private_ip(self):
        """拒绝指向私有 IP 的 URL"""
        with pytest.raises(SSRFBlockedError):
            SSRFSafeTransport.validate_url("http://127.0.0.1/admin")
        with pytest.raises(SSRFBlockedError):
            SSRFSafeTransport.validate_url("https://10.0.0.1/secret")

    def test_accepts_public_url(self):
        """接受公网 URL"""
        fake_addrs = [(2, 1, 6, "", ("93.184.216.34", 443))]
        with patch("socket.getaddrinfo", return_value=fake_addrs):
            result = SSRFSafeTransport.validate_url("https://example.com/article")
            assert result == "https://example.com/article"


# ── create_safe_async_client ───────────────────────────


class TestCreateSafeAsyncClient:
    """安全 HTTP 客户端工厂测试"""

    def test_client_disables_auto_redirects(self):
        """默认禁用自动重定向"""
        client = create_safe_async_client()
        assert client.follow_redirects is False

    def test_client_uses_ssrf_transport(self):
        """使用 SSRFSafeTransport 传输层"""
        client = create_safe_async_client()
        assert isinstance(client._transport, SSRFSafeTransport)


# ── safe_fetch redirect security ───────────────────────


class TestSafeFetchRedirects:
    """safe_fetch 重定向安全测试"""

    @pytest.mark.asyncio
    async def test_resolves_relative_redirect_before_validation(self):
        """相对重定向会先规范化为绝对 URL 再验证"""

        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/start":
                return httpx.Response(status_code=302, headers={"location": "next"})
            if request.url.path == "/next":
                return httpx.Response(status_code=200, text="ok")
            return httpx.Response(status_code=404)

        validated_urls: list[str] = []

        def _validate(url: str) -> str:
            validated_urls.append(url)
            return url

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)
        with (
            patch(
                "wechat_summarizer.shared.utils.ssrf_protection.create_safe_async_client",
                return_value=client,
            ),
            patch(
                "wechat_summarizer.shared.utils.ssrf_protection.SSRFSafeTransport.validate_url",
                side_effect=_validate,
            ),
        ):
            response = await safe_fetch("https://example.com/start")

        assert response.status_code == 200
        assert "https://example.com/next" in validated_urls

    @pytest.mark.asyncio
    async def test_blocks_scheme_relative_redirect_to_metadata_host(self):
        """scheme-relative 重定向到内网/元数据地址会被阻断"""

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=302,
                headers={"location": "//169.254.169.254/latest/meta-data"},
            )

        def _validate(url: str) -> str:
            if "169.254.169.254" in url:
                raise SSRFBlockedError("Blocked metadata redirect")
            return url

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)
        with (
            patch(
                "wechat_summarizer.shared.utils.ssrf_protection.create_safe_async_client",
                return_value=client,
            ),
            patch(
                "wechat_summarizer.shared.utils.ssrf_protection.SSRFSafeTransport.validate_url",
                side_effect=_validate,
            ),
            pytest.raises(SSRFBlockedError, match="Blocked metadata redirect"),
        ):
            await safe_fetch("https://example.com/start")


class TestSafeTransportTLS:
    """SSRF 安全传输层 TLS/SNI 行为测试"""

    def test_sync_transport_preserves_original_hostname_for_tls_sni(self):
        """同步传输层应继续按原始域名做 TLS SNI。"""
        request = httpx.Request("GET", "https://docs.python.org/3/")
        response = httpx.Response(200, request=request)

        with (
            patch.object(
                SSRFSafeSyncTransport,
                "resolve_and_validate",
                return_value=["151.101.0.223"],
            ),
            patch.object(httpx.HTTPTransport, "handle_request", return_value=response) as mock_super,
        ):
            transport = SSRFSafeSyncTransport()
            result = transport.handle_request(request)

        assert result is response
        forwarded_request = mock_super.call_args.args[0]
        assert forwarded_request.url.host == "151.101.0.223"
        assert forwarded_request.headers["Host"] == "docs.python.org"
        assert forwarded_request.extensions["sni_hostname"] == "docs.python.org"

    @pytest.mark.asyncio
    async def test_async_transport_preserves_original_hostname_for_tls_sni(self):
        """异步传输层也应继续按原始域名做 TLS SNI。"""
        request = httpx.Request("GET", "https://docs.python.org/3/")
        response = httpx.Response(200, request=request)

        with (
            patch.object(
                SSRFSafeTransport,
                "resolve_and_validate",
                return_value=["151.101.0.223"],
            ),
            patch.object(
                httpx.AsyncHTTPTransport,
                "handle_async_request",
                new=AsyncMock(return_value=response),
            ) as mock_super,
        ):
            transport = SSRFSafeTransport()
            result = await transport.handle_async_request(request)

        assert result is response
        forwarded_request = mock_super.await_args.args[0]
        assert forwarded_request.url.host == "151.101.0.223"
        assert forwarded_request.headers["Host"] == "docs.python.org"
        assert forwarded_request.extensions["sni_hostname"] == "docs.python.org"


class TestSafeFetchProxyHandling:
    """safe_fetch proxy 参数兼容性测试"""

    def test_safe_fetch_sync_does_not_forward_proxy_to_request(self):
        """proxy 应只在客户端构造阶段消费，不应透传给 request()."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.headers = {}

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response

        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_client
        mock_context.__exit__.return_value = None

        with (
            patch(
                "wechat_summarizer.shared.utils.ssrf_protection.create_safe_client",
                return_value=mock_context,
            ) as mock_factory,
            patch(
                "wechat_summarizer.shared.utils.ssrf_protection.SSRFSafeSyncTransport.validate_url",
                return_value="https://example.com",
            ),
        ):
            response = safe_fetch_sync(
                "https://example.com",
                headers={"User-Agent": "test"},
                proxy="http://127.0.0.1:8080",
            )

        assert response is mock_response
        mock_factory.assert_called_once_with(proxy="http://127.0.0.1:8080")
        mock_client.request.assert_called_once_with(
            "GET",
            "https://example.com",
            headers={"User-Agent": "test"},
        )
        assert "proxy" not in mock_client.request.call_args.kwargs

    @pytest.mark.asyncio
    async def test_safe_fetch_does_not_forward_none_proxy_to_async_request(self):
        """即使显式传入 proxy=None，也不应把它交给 AsyncClient.request()."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.headers = {}

        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "wechat_summarizer.shared.utils.ssrf_protection.create_safe_async_client",
                return_value=mock_context,
            ) as mock_factory,
            patch(
                "wechat_summarizer.shared.utils.ssrf_protection.SSRFSafeTransport.validate_url",
                return_value="https://example.com",
            ),
        ):
            response = await safe_fetch(
                "https://example.com",
                headers={"User-Agent": "test"},
                proxy=None,
            )

        assert response is mock_response
        mock_factory.assert_called_once_with()
        mock_client.request.assert_awaited_once_with(
            "GET",
            "https://example.com",
            headers={"User-Agent": "test"},
        )
        assert "proxy" not in mock_client.request.call_args.kwargs
