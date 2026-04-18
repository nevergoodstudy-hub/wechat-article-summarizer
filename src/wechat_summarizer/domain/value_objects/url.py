"""URL值对象 - 带验证"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

from ...shared.constants import WECHAT_DOMAIN
from ...shared.exceptions import InvalidURLError

# URL 最大长度限制
MAX_URL_LENGTH = 2048

# 允许的协议白名单
ALLOWED_SCHEMES = frozenset({"http", "https"})


@dataclass(frozen=True)
class ArticleURL:
    """
    文章URL值对象

    值对象是不可变的，包含URL验证逻辑。
    包含安全防护：URL长度限制、协议白名单、SSRF防护。
    """

    value: str

    def __post_init__(self) -> None:
        """验证URL格式和安全性"""
        if not self.value:
            raise InvalidURLError("URL不能为空")

        # 长度限制
        if len(self.value) > MAX_URL_LENGTH:
            raise InvalidURLError(f"URL长度超出限制（最大{MAX_URL_LENGTH}字符）")

        parsed = urlparse(self.value)
        if not parsed.scheme or not parsed.hostname:
            raise InvalidURLError(f"无效的URL格式: {self.value}")

        if parsed.username or parsed.password:
            raise InvalidURLError("URL中不允许包含用户信息")

        # 协议白名单
        if parsed.scheme.lower() not in ALLOWED_SCHEMES:
            raise InvalidURLError(f"不支持的协议: {parsed.scheme}（仅支持 http/https）")

        # SSRF 防护：禁止访问内网地址
        if self._is_private_address(parsed.hostname):
            raise InvalidURLError("不允许访问内网地址")

    @staticmethod
    def _is_private_address(host: str) -> bool:
        """检查是否为内网/私有地址"""
        # 检查特殊域名
        # NOTE: These addresses are used for VALIDATION (blocking), not for binding
        private_domains = {
            "localhost",
            "127.0.0.1",
            "0.0.0.0",  # nosec B104 - validation blacklist entry, not a bind target
            "::1",
            "[::1]",
        }
        if host.lower() in private_domains:
            return True

        # 检查 .local 域名
        if host.lower().endswith(".local"):
            return True

        # 尝试解析为 IP 地址并检查是否为私有地址
        try:
            # 尝试直接解析为IP
            ip = ipaddress.ip_address(host)
            return ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local
        except ValueError:
            pass

        # NOTE: DNS rebinding protection limitation
        # This method only checks hostnames, not resolved IPs. A malicious DNS
        # server could initially return a public IP and later rebind to a private IP.
        # For full DNS rebinding protection, use validate_resolved_ip() at the
        # connection layer to verify the actual IP address before making requests.
        return False

    @property
    def is_wechat(self) -> bool:
        """是否为微信公众号链接"""
        parsed = urlparse(self.value)
        return (parsed.hostname or "").lower() == WECHAT_DOMAIN

    @property
    def is_rss(self) -> bool:
        """是否为RSS链接"""
        return self.value.endswith((".xml", ".rss", "/feed", "/rss"))

    @property
    def domain(self) -> str:
        """获取域名"""
        parsed = urlparse(self.value)
        return parsed.hostname or parsed.netloc

    @property
    def scheme(self) -> str:
        """获取协议"""
        parsed = urlparse(self.value)
        return parsed.scheme

    @classmethod
    def from_string(cls, url: str) -> ArticleURL:
        """从字符串创建URL对象"""
        # 自动补全协议
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return cls(value=url)

    @classmethod
    def wechat(cls, url: str) -> ArticleURL:
        """创建微信公众号URL，带额外验证"""
        article_url = cls.from_string(url)
        if not article_url.is_wechat:
            raise InvalidURLError(f"不是有效的微信公众号链接: {url}")
        return article_url

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"ArticleURL({self.value!r})"


def validate_resolved_ip(ip_string: str) -> bool:
    """验证解析后的IP地址是否安全（用于SSRF DNS rebinding防护）

    此函数应在HTTP客户端层进行DNS解析后调用，用于验证实际解析的IP地址
    是否为安全的公网地址。这可以防止DNS rebinding攻击，其中攻击者的DNS
    服务器初始返回公网IP，随后重新绑定到内网IP。

    Usage example:
        ```python
        import socket
        from wechat_summarizer.domain.value_objects.url import validate_resolved_ip

        def safe_request(url: str):
            parsed = urlparse(url)
            host = parsed.netloc.split(":")[0]

            # Resolve DNS and validate the IP
            resolved_ip = socket.gethostbyname(host)
            if not validate_resolved_ip(resolved_ip):
                raise SecurityError(f"Blocked request to private IP: {resolved_ip}")

            # Proceed with the actual request using the resolved IP
            # ...
        ```

    Args:
        ip_string: 解析后的IP地址字符串

    Returns:
        True 如果IP地址安全（公网地址），False 如果为内网/保留地址
    """
    try:
        ip = ipaddress.ip_address(ip_string)
    except ValueError:
        # Invalid IP address format
        return False

    # Block private, loopback, reserved, and link-local addresses
    if ip.is_private:
        return False
    if ip.is_loopback:
        return False
    if ip.is_reserved:
        return False
    if ip.is_link_local:
        return False

    # For IPv6, also check multicast and unspecified
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.is_multicast:
            return False
        # Unspecified address (::)
        if ip == ipaddress.IPv6Address("::"):
            return False

    # For IPv4, check for 0.0.0.0
    return not (
        isinstance(ip, ipaddress.IPv4Address) and ip == ipaddress.IPv4Address("0.0.0.0")  # nosec B104 - explicit deny rule
    )


def resolve_and_validate_host(hostname: str) -> tuple[bool, str | None]:
    """解析主机名并验证解析后的IP是否安全

    此函数结合DNS解析和IP验证，提供完整的DNS rebinding防护。

    Args:
        hostname: 主机名（不包含端口号）

    Returns:
        (是否安全, 解析的IP地址或None)
    """
    try:
        resolved_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        # DNS resolution failed
        return False, None

    is_safe = validate_resolved_ip(resolved_ip)
    return is_safe, resolved_ip if is_safe else None
