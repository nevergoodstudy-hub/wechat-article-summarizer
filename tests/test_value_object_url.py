import socket

import pytest

from wechat_summarizer.domain.value_objects import ArticleURL
from wechat_summarizer.domain.value_objects.url import (
    resolve_and_validate_host,
    validate_resolved_ip,
)
from wechat_summarizer.shared.exceptions import InvalidURLError


class TestArticleURLBasic:
    """ArticleURL 基本功能测试"""

    def test_from_string_adds_scheme_and_detects_wechat(self) -> None:
        url = ArticleURL.from_string("mp.weixin.qq.com/s/abc")
        assert str(url).startswith("https://")
        assert url.is_wechat

    def test_invalid_url_raises(self) -> None:
        with pytest.raises(InvalidURLError):
            ArticleURL.from_string("http://")

    def test_domain_property(self) -> None:
        url = ArticleURL.from_string("https://example.com/path")
        assert url.domain == "example.com"

    def test_scheme_property(self) -> None:
        url = ArticleURL.from_string("https://example.com")
        assert url.scheme == "https"


class TestArticleURLSecurity:
    """ArticleURL 安全验证测试"""

    def test_url_length_limit(self) -> None:
        """测试URL长度限制"""
        long_url = "https://example.com/" + "a" * 3000
        with pytest.raises(InvalidURLError, match="长度超出限制"):
            ArticleURL(long_url)

    def test_disallow_ftp_protocol(self) -> None:
        """测试禁止FTP协议"""
        with pytest.raises(InvalidURLError, match="不支持的协议"):
            ArticleURL("ftp://example.com/file")

    def test_disallow_file_protocol(self) -> None:
        """测试禁止file协议"""
        # file:/// 缺少 netloc，会先触发无效URL格式错误
        with pytest.raises(InvalidURLError):
            ArticleURL("file:///etc/passwd")

    def test_disallow_javascript_protocol(self) -> None:
        """测试禁止javascript协议"""
        # javascript: 缺少 netloc，会先触发无效URL格式错误
        with pytest.raises(InvalidURLError):
            ArticleURL("javascript:alert(1)")

    def test_disallow_localhost(self) -> None:
        """测试禁止localhost - SSRF防护"""
        with pytest.raises(InvalidURLError, match="内网地址"):
            ArticleURL("http://localhost/admin")

    def test_disallow_127_0_0_1(self) -> None:
        """测试禁止127.0.0.1 - SSRF防护"""
        with pytest.raises(InvalidURLError, match="内网地址"):
            ArticleURL("http://127.0.0.1:8080/admin")

    def test_disallow_private_ip_10_x(self) -> None:
        """测试禁止10.x.x.x私有IP - SSRF防护"""
        with pytest.raises(InvalidURLError, match="内网地址"):
            ArticleURL("http://10.0.0.1/internal")

    def test_disallow_private_ip_192_168(self) -> None:
        """测试禁止192.168.x.x私有IP - SSRF防护"""
        with pytest.raises(InvalidURLError, match="内网地址"):
            ArticleURL("http://192.168.1.1/router")

    def test_disallow_private_ip_172_16(self) -> None:
        """测试禁止172.16.x.x私有IP - SSRF防护"""
        with pytest.raises(InvalidURLError, match="内网地址"):
            ArticleURL("http://172.16.0.1/internal")

    def test_disallow_local_domain(self) -> None:
        """测试禁止.local域名 - SSRF防护"""
        with pytest.raises(InvalidURLError, match="内网地址"):
            ArticleURL("http://myserver.local/api")

    def test_allow_public_url(self) -> None:
        """测试允许公网URL"""
        url = ArticleURL("https://mp.weixin.qq.com/s/test123")
        assert url.is_wechat
        assert str(url) == "https://mp.weixin.qq.com/s/test123"

    def test_disallow_userinfo_in_url(self) -> None:
        """测试拒绝带用户信息的 URL，防止 host confusion。"""
        with pytest.raises(InvalidURLError, match="用户信息"):
            ArticleURL("https://mp.weixin.qq.com@127.0.0.1/private")

    def test_is_wechat_requires_exact_hostname(self) -> None:
        """仅精确的微信公众号主机名应被识别为微信链接。"""
        url = ArticleURL("https://example.com/mp.weixin.qq.com/article")
        assert url.is_wechat is False

    def test_allow_http_protocol(self) -> None:
        """测试允许HTTP协议"""
        url = ArticleURL("http://example.com/article")
        assert url.scheme == "http"

    def test_allow_https_protocol(self) -> None:
        """测试允许HTTPS协议"""
        url = ArticleURL("https://example.com/article")
        assert url.scheme == "https"

    def test_wechat_factory_rejects_non_wechat_hosts(self) -> None:
        """测试微信公众号工厂方法拒绝非微信域名。"""
        with pytest.raises(InvalidURLError, match="微信公众号链接"):
            ArticleURL.wechat("https://example.com/article")


class TestResolvedIpValidation:
    """解析后 IP 的安全验证测试"""

    @pytest.mark.parametrize(
        ("ip_string", "expected"),
        [
            ("1.1.1.1", True),
            ("192.168.1.1", False),
            ("0.0.0.0", False),
            ("ff02::1", False),
            ("::", False),
            ("not-an-ip", False),
        ],
    )
    def test_validate_resolved_ip(self, ip_string: str, expected: bool) -> None:
        assert validate_resolved_ip(ip_string) is expected

    def test_resolve_and_validate_host_returns_safe_public_ip(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(socket, "gethostbyname", lambda _hostname: "8.8.8.8")

        assert resolve_and_validate_host("example.com") == (True, "8.8.8.8")

    def test_resolve_and_validate_host_rejects_private_ip(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(socket, "gethostbyname", lambda _hostname: "10.0.0.1")

        assert resolve_and_validate_host("internal.example") == (False, None)

    def test_resolve_and_validate_host_handles_dns_failures(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def raise_gaierror(_hostname: str) -> str:
            raise socket.gaierror("dns failed")

        monkeypatch.setattr(socket, "gethostbyname", raise_gaierror)

        assert resolve_and_validate_host("missing.example") == (False, None)
