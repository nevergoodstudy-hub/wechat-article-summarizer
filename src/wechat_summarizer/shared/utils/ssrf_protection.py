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

from .network_policy import (
    DEFAULT_BLOCKED_HOSTNAMES,
    DEFAULT_BLOCKED_NETWORKS,
    DEFAULT_NETWORK_POLICY,
    NetworkPolicyError,
)


class SSRFBlockedError(Exception):
    """SSRF 防护拦截异常"""


class _SSRFSafeBase:
    """SSRF 安全传输层共享逻辑"""

    # 封锁的 IP 范围（包括 IPv4 和 IPv6）
    BLOCKED_NETWORKS: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...] = (
        DEFAULT_BLOCKED_NETWORKS
    )
    BLOCKED_HOSTNAMES: frozenset[str] = DEFAULT_BLOCKED_HOSTNAMES
    NETWORK_POLICY = DEFAULT_NETWORK_POLICY

    @classmethod
    def is_ip_blocked(cls, ip_str: str) -> bool:
        return cls.NETWORK_POLICY.is_ip_blocked(ip_str)

    @classmethod
    def _looks_like_alt_ip_notation(cls, hostname: str) -> bool:
        return cls.NETWORK_POLICY.looks_like_alternative_ip_notation(hostname)

    @classmethod
    def resolve_and_validate(cls, hostname: str, port: int | None = None) -> list[str]:
        try:
            cls.NETWORK_POLICY.require_host_allowed(hostname)
        except ValueError as e:
            raise SSRFBlockedError(str(e)) from e

        try:
            ip = cls.NETWORK_POLICY.canonicalize_ip(hostname)
        except ValueError:
            pass
        else:
            try:
                cls.NETWORK_POLICY.require_ip_allowed(str(ip))
            except NetworkPolicyError as e:
                raise SSRFBlockedError(str(e)) from e
            return [str(ip)]

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
            if cls.NETWORK_POLICY.is_ip_blocked(ip_str):
                raise SSRFBlockedError(f"DNS resolved {hostname} to blocked IP: {ip_str}")
            canonical_ip = str(cls.NETWORK_POLICY.canonicalize_ip(ip_str))
            if canonical_ip not in validated_ips:
                validated_ips.append(canonical_ip)

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
        extensions = dict(request.extensions)
        extensions["sni_hostname"] = hostname

        ip_request = httpx.Request(
            method=request.method,
            url=new_url,
            headers=headers,
            content=request.content,
            extensions=extensions,
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
        extensions = dict(request.extensions)
        extensions["sni_hostname"] = hostname

        ip_request = httpx.Request(
            method=request.method,
            url=new_url,
            headers=headers,
            content=request.content,
            extensions=extensions,
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


def _extract_client_kwargs(request_kwargs: dict[str, Any]) -> dict[str, Any]:
    """Split client-only kwargs from request kwargs.

    `httpx` 0.28 accepts `proxy` on the client constructor, but not on
    `Client.request()` / `AsyncClient.request()`. Generic scrapers pass
    `proxy=None` by default, so we consume it here before issuing requests.
    """

    client_kwargs: dict[str, Any] = {}

    if "proxy" in request_kwargs:
        proxy = request_kwargs.pop("proxy")
        if proxy is not None:
            client_kwargs["proxy"] = proxy

    return client_kwargs


async def safe_fetch(
    url: str,
    *,
    method: str = "GET",
    max_redirects: int = 5,
    **kwargs: Any,
) -> httpx.Response:
    request_kwargs = dict(kwargs)
    client_kwargs = _extract_client_kwargs(request_kwargs)

    async with create_safe_async_client(**client_kwargs) as client:
        current_url = url
        current_method = method
        for redirect_count in range(max_redirects + 1):
            SSRFSafeTransport.validate_url(current_url)
            response = await client.request(current_method, current_url, **request_kwargs)

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
    request_kwargs = dict(kwargs)
    client_kwargs = _extract_client_kwargs(request_kwargs)

    with create_safe_client(**client_kwargs) as client:
        current_url = url
        current_method = method
        for redirect_count in range(max_redirects + 1):
            SSRFSafeSyncTransport.validate_url(current_url)
            response = client.request(current_method, current_url, **request_kwargs)

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
