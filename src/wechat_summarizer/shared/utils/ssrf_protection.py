"""SSRF 防护模块 — DNS 重绑定安全传输层

实现"解析一次，验证 IP，连接已验证 IP"的安全模式，
消除 DNS 重绑定 TOCTOU 攻击窗口。

覆盖审计问题:
- P0-3: SSRF 缺少 DNS 重绑定保护
- P1-4: SSRF 无 HTTP 重定向验证
- P1-5: 替代 IP 表示法未被阻止
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


class _SSRFSafeBase:
    """SSRF 安全传输层共享逻辑"""

    # 封锁的 IP 范围（包括 IPv4 和 IPv6）
    BLOCKED_NETWORKS: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...] = (
        ipaddress.ip_network("0.0.0.0/8"),
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("100.64.0.0/10"),
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("169.254.0.0/16"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.0.0.0/24"),
        ipaddress.ip_network("192.0.2.0/24"),
        ipaddress.ip_network("192.88.99.0/24"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("198.18.0.0/15"),
        ipaddress.ip_network("198.51.100.0/24"),
        ipaddress.ip_network("203.0.113.0/24"),
        ipaddress.ip_network("224.0.0.0/4"),
        ipaddress.ip_network("240.0.0.0/4"),
        ipaddress.ip_network("255.255.255.255/32"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
        ipaddress.ip_network("fe80::/10"),
        ipaddress.ip_network("ff00::/8"),
        ipaddress.ip_network("::ffff:0.0.0.0/96"),
    )

    BLOCKED_HOSTNAMES: frozenset[str] = frozenset(
        {
            "localhost",
            "instance-data",
            "metadata.google.internal",
            "metadata.internal",
            "169.254.169.254",
            "fd00:ec2::254",
        }
    )

    @classmethod
    def is_ip_blocked(cls, ip_str: str) -> bool:
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return True

        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return True

        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            return cls.is_ip_blocked(str(ip.ipv4_mapped))

        return any(ip in network for network in cls.BLOCKED_NETWORKS)

    @classmethod
    def _looks_like_alt_ip_notation(cls, hostname: str) -> bool:
        # 纯数字（十进制整型 IPv4）
        if hostname.isdigit():
            return True

        # 可疑点分十进制表示（如 0177.0.0.1）
        parts = hostname.split(".")
        if len(parts) == 4 and all(part.isdigit() for part in parts):
            return any(len(part) > 1 and part.startswith("0") for part in parts)

        return False

    @classmethod
    def resolve_and_validate(cls, hostname: str, port: int | None = None) -> list[str]:
        if hostname.lower() in cls.BLOCKED_HOSTNAMES:
            raise SSRFBlockedError(f"Blocked hostname: {hostname}")

        if cls._looks_like_alt_ip_notation(hostname):
            raise SSRFBlockedError(f"Blocked alternative IP notation: {hostname}")

        try:
            ip = ipaddress.ip_address(hostname)
            if cls.is_ip_blocked(str(ip)):
                raise SSRFBlockedError(f"Blocked IP address: {ip}")
            return [str(ip)]
        except ValueError:
            pass

        try:
            addr_infos = socket.getaddrinfo(
                hostname,
                port or 443,
                socket.AF_UNSPEC,
                socket.SOCK_STREAM,
            )
        except socket.gaierror as e:
            raise SSRFBlockedError(f"DNS resolution failed for {hostname}: {e}") from e

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
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise SSRFBlockedError(f"Disallowed URL scheme: {parsed.scheme!r}")
        if not parsed.hostname:
            raise SSRFBlockedError("URL missing hostname")
        cls.resolve_and_validate(parsed.hostname, parsed.port)
        return url


class SSRFSafeTransport(_SSRFSafeBase, httpx.AsyncHTTPTransport):
    """异步安全传输层（固定已校验 IP）"""

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        hostname = request.url.host
        if not hostname:
            raise SSRFBlockedError("Request missing hostname")

        validated_ips = self.resolve_and_validate(hostname, request.url.port)
        ip = validated_ips[0]
        host_for_url = f"[{ip}]" if ":" in ip else ip

        new_url = request.url.copy_with(host=host_for_url)
        headers = httpx.Headers(request.headers)
        headers["Host"] = hostname

        ip_request = httpx.Request(
            method=request.method,
            url=new_url,
            headers=headers,
            content=request.content,
        )
        return await super().handle_async_request(ip_request)


class SSRFSafeSyncTransport(_SSRFSafeBase, httpx.HTTPTransport):
    """同步安全传输层（固定已校验 IP）"""

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        hostname = request.url.host
        if not hostname:
            raise SSRFBlockedError("Request missing hostname")

        validated_ips = self.resolve_and_validate(hostname, request.url.port)
        ip = validated_ips[0]
        host_for_url = f"[{ip}]" if ":" in ip else ip

        new_url = request.url.copy_with(host=host_for_url)
        headers = httpx.Headers(request.headers)
        headers["Host"] = hostname

        ip_request = httpx.Request(
            method=request.method,
            url=new_url,
            headers=headers,
            content=request.content,
        )
        return super().handle_request(ip_request)


def create_safe_async_client(**kwargs: Any) -> httpx.AsyncClient:
    kwargs.setdefault("follow_redirects", False)
    kwargs.setdefault("timeout", httpx.Timeout(30.0))
    return httpx.AsyncClient(transport=SSRFSafeTransport(), **kwargs)


def create_safe_client(**kwargs: Any) -> httpx.Client:
    kwargs.setdefault("follow_redirects", False)
    kwargs.setdefault("timeout", 30.0)
    return httpx.Client(transport=SSRFSafeSyncTransport(), **kwargs)


async def safe_fetch(
    url: str,
    *,
    method: str = "GET",
    max_redirects: int = 5,
    **kwargs: Any,
) -> httpx.Response:
    async with create_safe_async_client() as client:
        current_url = url
        current_method = method
        for redirect_count in range(max_redirects + 1):
            SSRFSafeTransport.validate_url(current_url)
            response = await client.request(current_method, current_url, **kwargs)

            if response.status_code not in (301, 302, 303, 307, 308):
                return response

            redirect_url = response.headers.get("location")
            if not redirect_url:
                return response
            redirect_url = urljoin(current_url, redirect_url)

            logger.debug(
                f"SSRF safe redirect [{redirect_count + 1}/{max_redirects}]: "
                f"{current_url} → {redirect_url}"
            )

            SSRFSafeTransport.validate_url(redirect_url)
            current_url = redirect_url
            if response.status_code == 303:
                current_method = "GET"

        raise httpx.TooManyRedirects(
            f"Exceeded max redirects ({max_redirects})",
            request=httpx.Request(current_method, url),
        )


def safe_fetch_sync(
    url: str,
    *,
    method: str = "GET",
    max_redirects: int = 5,
    **kwargs: Any,
) -> httpx.Response:
    with create_safe_client() as client:
        current_url = url
        current_method = method
        for redirect_count in range(max_redirects + 1):
            SSRFSafeSyncTransport.validate_url(current_url)
            response = client.request(current_method, current_url, **kwargs)

            if response.status_code not in (301, 302, 303, 307, 308):
                return response

            redirect_url = response.headers.get("location")
            if not redirect_url:
                return response
            redirect_url = urljoin(current_url, redirect_url)

            logger.debug(
                f"SSRF safe redirect [{redirect_count + 1}/{max_redirects}]: "
                f"{current_url} → {redirect_url}"
            )

            SSRFSafeSyncTransport.validate_url(redirect_url)
            current_url = redirect_url
            if response.status_code == 303:
                current_method = "GET"

        raise httpx.TooManyRedirects(
            f"Exceeded max redirects ({max_redirects})",
            request=httpx.Request(current_method, url),
        )
