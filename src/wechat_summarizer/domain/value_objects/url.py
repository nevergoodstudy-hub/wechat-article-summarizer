"""URL值对象 - 带验证"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

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
        if not parsed.scheme or not parsed.netloc:
            raise InvalidURLError(f"无效的URL格式: {self.value}")

        # 协议白名单
        if parsed.scheme.lower() not in ALLOWED_SCHEMES:
            raise InvalidURLError(f"不支持的协议: {parsed.scheme}（仅支持 http/https）")

        # SSRF 防护：禁止访问内网地址
        if self._is_private_address(parsed.netloc):
            raise InvalidURLError("不允许访问内网地址")

    @staticmethod
    def _is_private_address(netloc: str) -> bool:
        """检查是否为内网/私有地址"""
        # 移除端口号
        host = netloc.split(":")[0]

        # 检查特殊域名
        # NOTE: These addresses are used for VALIDATION (blocking), not for binding
        private_domains = {
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
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

        # 对于域名，尝试DNS解析（可选，仅在需要严格防护时启用）
        # 这里不做DNS解析以避免网络请求，仅做基础检查
        return False

    @property
    def is_wechat(self) -> bool:
        """是否为微信公众号链接"""
        return "mp.weixin.qq.com" in self.value

    @property
    def is_rss(self) -> bool:
        """是否为RSS链接"""
        return self.value.endswith((".xml", ".rss", "/feed", "/rss"))

    @property
    def domain(self) -> str:
        """获取域名"""
        parsed = urlparse(self.value)
        return parsed.netloc

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
