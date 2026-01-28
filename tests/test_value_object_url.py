import pytest
from wechat_summarizer.domain.value_objects import ArticleURL
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

    def test_allow_http_protocol(self) -> None:
        """测试允许HTTP协议"""
        url = ArticleURL("http://example.com/article")
        assert url.scheme == "http"

    def test_allow_https_protocol(self) -> None:
        """测试允许HTTPS协议"""
        url = ArticleURL("https://example.com/article")
        assert url.scheme == "https"
