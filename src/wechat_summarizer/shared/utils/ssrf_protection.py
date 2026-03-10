"""SSRF 防护模块 — DNS 重绑定安全传输层

实现"解析一次，验证 IP，连接已验证 IP"的安全模式，
消除 DNS 重绑定 TOCTOU 攻击窗口。

覆盖审计问题:
- P0-3: SSRF 缺少 DNS 重绑定保护
- P1-4: SSRF 无 HTTP 重定向验证
- P1-5: 替代 IP 表示法未被阻止

参考:
- OWASP SSRF Prevention Cheat Sheet
- AutoGPT GHSA-wvjg-9879-3m7w
- BentoML CVE-2025-54381
"""

from __future__ import annotations

import ipaddress
import socket
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from loguru import logger


class SSRFBlockedError(Exception):
    """SSRF 防护拦截异常"""


TRANSPORT_KWARGS: frozenset[str] = frozenset(
    {
        "cert",
        "http1",
        "http2",
        "limits",
        "local_address",
        "proxy",
        "retries",
        "socket_options",
        "trust_env",
        "uds",
        "verify",
    }
)


def _pop_transport_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    """提取需要传递给 transport 的参数。"""
    transport_kwargs: dict[str, Any] = {}
    for key in TRANSPORT_KWARGS:
        if key in kwargs:
            transport_kwargs[key] = kwargs.pop(key)
    return transport_kwargs


def _rewrite_request_to_validated_ip(request: httpx.Request) -> httpx.Request:
    """将请求重写为“直连已验证 IP + 保留 Host/SNI”的形式。"""
    hostname = request.url.host
    if not hostname:
        raise SSRFBlockedError("Request missing hostname")

    validated_ips = SSRFSafeTransport.resolve_and_validate(hostname, request.url.port)
    ip = validated_ips[0]
    host_for_url = f"[{ip}]" if ":" in ip else ip

    new_url = request.url.copy_with(host=host_for_url)
    headers = httpx.Headers(request.headers)
    headers["Host"] = hostname

    extensions = dict(request.extensions)
    extensions["sni_hostname"] = hostname

    return httpx.Request(
        method=request.method,
        url=new_url,
        headers=headers,
        content=request.content,
        extensions=extensions,
    )


class SSRFSafeTransport(httpx.AsyncHTTPTransport):
    """自定义 httpx 传输层，防止 DNS 重绑定攻击

    核心原理:
    1. 在请求前解析 DNS，获取所有 IP 地址
    2. 验证所有 IP 均不在私有/保留范围内
    3. 使用已验证的 IP 直接连接（绕过二次 DNS 解析）
    """

    # 封锁的 IP 范围（包括 IPv4 和 IPv6）
    BLOCKED_NETWORKS: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...] = (
        # IPv4 私有与保留
        ipaddress.ip_network("0.0.0.0/8"),  # "This" network
        ipaddress.ip_network("10.0.0.0/8"),  # RFC1918
        ipaddress.ip_network("100.64.0.0/10"),  # Carrier-grade NAT
        ipaddress.ip_network("127.0.0.0/8"),  # Loopback
        ipaddress.ip_network("169.254.0.0/16"),  # Link-local
        ipaddress.ip_network("172.16.0.0/12"),  # RFC1918
        ipaddress.ip_network("192.0.0.0/24"),  # IETF Protocol Assignments
        ipaddress.ip_network("192.0.2.0/24"),  # TEST-NET-1
        ipaddress.ip_network("192.88.99.0/24"),  # 6to4 relay
        ipaddress.ip_network("192.168.0.0/16"),  # RFC1918
        ipaddress.ip_network("198.18.0.0/15"),  # Benchmarking
        ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2
        ipaddress.ip_network("203.0.113.0/24"),  # TEST-NET-3
        ipaddress.ip_network("224.0.0.0/4"),  # Multicast
        ipaddress.ip_network("240.0.0.0/4"),  # Reserved
        ipaddress.ip_network("255.255.255.255/32"),  # Broadcast
        # IPv6 私有与保留
        ipaddress.ip_network("::1/128"),  # Loopback
        ipaddress.ip_network("fc00::/7"),  # Unique Local Address
        ipaddress.ip_network("fe80::/10"),  # Link-local
        ipaddress.ip_network("ff00::/8"),  # Multicast
        # IPv6-mapped IPv4 私有地址
        ipaddress.ip_network("::ffff:0.0.0.0/96"),  # IPv4-mapped (全范围，后续单独检查)
    )

    # 封锁的主机名（云元数据端点等）
    BLOCKED_HOSTNAMES: frozenset[str] = frozenset(
        {
            "localhost",
            "instance-data",
            "metadata.google.internal",
            "metadata.internal",
            "169.254.169.254",  # AWS/GCP/Azure 元数据
            "fd00:ec2::254",  # AWS IMDSv2 IPv6
        }
    )

    # 最大重定向次数
    MAX_REDIRECTS: int = 5

    @classmethod
    def is_ip_blocked(cls, ip_str: str) -> bool:
        """检查 IP 是否在封锁范围内

        使用 ipaddress 模块自动规范化所有格式:
        - 十进制表示 (2130706433)
        - 八进制表示 (0177.0.0.1)
        - IPv6-mapped IPv4 (::ffff:127.0.0.1)

        Args:
            ip_str: IP 地址字符串

        Returns:
            True 如果 IP 被封锁
        """
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            # 无法解析的 IP 格式默认阻止
            return True

        # 快速检查: 标准库内置属性
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return True

        # IPv6-mapped IPv4: 提取内嵌的 IPv4 地址并递归检查
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            return cls.is_ip_blocked(str(ip.ipv4_mapped))

        # 精确范围匹配
        return any(ip in network for network in cls.BLOCKED_NETWORKS)

    @classmethod
    def resolve_and_validate(cls, hostname: str, port: int | None = None) -> list[str]:
        """解析 DNS 并验证所有返回的 IP 地址

        Args:
            hostname: 主机名或 IP 地址
            port: 端口号

        Returns:
            经过验证的 IP 地址列表

        Raises:
            SSRFBlockedError: 如果主机名被封锁或解析到私有 IP
        """
        # 1) 主机名黑名单检查
        if hostname.lower() in cls.BLOCKED_HOSTNAMES:
            raise SSRFBlockedError(f"Blocked hostname: {hostname}")

        # 2) 尝试直接解析为 IP（处理替代表示法: 十进制、八进制等）
        try:
            ip = ipaddress.ip_address(hostname)
            if cls.is_ip_blocked(str(ip)):
                raise SSRFBlockedError(f"Blocked IP address: {ip}")
            return [str(ip)]
        except ValueError:
            pass  # 不是 IP 字面量，继续 DNS 解析

        # 3) DNS 解析
        try:
            addr_infos = socket.getaddrinfo(
                hostname,
                port or 443,
                socket.AF_UNSPEC,
                socket.SOCK_STREAM,
            )
        except socket.gaierror as e:
            raise SSRFBlockedError(f"DNS resolution failed for {hostname}: {e}") from e

        # 4) 验证所有解析结果
        validated_ips: list[str] = []
        for _family, _type, _proto, _canonname, sockaddr in addr_infos:
            ip_str = str(sockaddr[0])
            if cls.is_ip_blocked(ip_str):
                raise SSRFBlockedError(f"DNS resolved {hostname} to blocked IP: {ip_str}")
            if ip_str not in validated_ips:
                validated_ips.append(ip_str)

        if not validated_ips:
            raise SSRFBlockedError(f"No valid IP addresses for: {hostname}")

        return validated_ips

    @classmethod
    def validate_url(cls, url: str) -> str:
        """验证 URL 安全性（scheme + 主机名 + IP 检查）

        Args:
            url: 待验证的 URL

        Returns:
            验证通过的 URL

        Raises:
            SSRFBlockedError: 如果 URL 不安全
        """
        parsed = urlparse(url)

        # Scheme 检查
        if parsed.scheme not in ("http", "https"):
            raise SSRFBlockedError(f"Disallowed URL scheme: {parsed.scheme!r}")

        # 主机名检查
        if not parsed.hostname:
            raise SSRFBlockedError("URL missing hostname")

        # DNS 解析 + IP 验证
        cls.resolve_and_validate(parsed.hostname, parsed.port)

        return url

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """拦截请求，使用已验证的 IP 直接连接

        重写 httpx 传输层的异步请求处理方法。
        """
        return await super().handle_async_request(_rewrite_request_to_validated_ip(request))


class SSRFSafeSyncTransport(httpx.HTTPTransport):
    """同步版本的 SSRF 安全传输层。"""

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """拦截同步请求并重写到已验证的 IP。"""
        return super().handle_request(_rewrite_request_to_validated_ip(request))


def create_safe_client(**kwargs: Any) -> httpx.Client:
    """创建带有 SSRF 防护的 httpx 同步客户端。"""
    kwargs.setdefault("follow_redirects", False)
    kwargs.setdefault("timeout", httpx.Timeout(30.0))
    transport_kwargs = _pop_transport_kwargs(kwargs)

    return httpx.Client(
        transport=SSRFSafeSyncTransport(**transport_kwargs),
        **kwargs,
    )


def create_safe_async_client(**kwargs: Any) -> httpx.AsyncClient:
    """创建带有 SSRF 防护的 httpx 异步客户端

    用法:
        async with create_safe_async_client() as client:
            response = await client.get("https://example.com")

    Args:
        **kwargs: 传递给 httpx.AsyncClient 的额外参数

    Returns:
        配置了 SSRFSafeTransport 的 httpx.AsyncClient
    """
    # 强制禁用自动重定向（手动处理以验证每个重定向目标）
    kwargs.setdefault("follow_redirects", False)
    kwargs.setdefault("timeout", httpx.Timeout(30.0))
    transport_kwargs = _pop_transport_kwargs(kwargs)

    return httpx.AsyncClient(
        transport=SSRFSafeTransport(**transport_kwargs),
        **kwargs,
    )


async def safe_fetch(
    url: str,
    *,
    method: str = "GET",
    max_redirects: int = 5,
    **kwargs: Any,
) -> httpx.Response:
    """执行带有 SSRF 防护的 HTTP 请求（含安全重定向处理）

    Args:
        url: 请求 URL
        method: HTTP 方法
        max_redirects: 最大重定向次数
        **kwargs: 传递给 httpx.Request 的额外参数

    Returns:
        httpx.Response

    Raises:
        SSRFBlockedError: 如果请求目标不安全
        httpx.TooManyRedirects: 超过重定向限制
    """
    async with create_safe_async_client() as client:
        current_url = url
        for redirect_count in range(max_redirects + 1):
            # 验证当前 URL
            SSRFSafeTransport.validate_url(current_url)

            response = await client.request(method, current_url, **kwargs)

            # 非重定向响应，直接返回
            if response.status_code not in (301, 302, 303, 307, 308):
                return response

            # 处理重定向
            redirect_url = response.headers.get("location")
            if not redirect_url:
                return response
            redirect_url = urljoin(current_url, redirect_url)

            logger.debug(
                f"SSRF safe redirect [{redirect_count + 1}/{max_redirects}]: "
                f"{current_url} → {redirect_url}"
            )

            # 验证重定向目标（关键！防止重定向到内部地址）
            SSRFSafeTransport.validate_url(redirect_url)
            current_url = redirect_url

            # 303 重定向强制使用 GET
            if response.status_code == 303:
                method = "GET"

        raise httpx.TooManyRedirects(
            f"Exceeded max redirects ({max_redirects})",
            request=httpx.Request(method, url),
        )
