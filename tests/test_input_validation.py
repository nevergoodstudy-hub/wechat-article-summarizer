"""输入验证测试用例

依据标准：
- OWASP Input Validation Cheat Sheet
- CWE-20: Improper Input Validation
"""

from __future__ import annotations

import pytest

from wechat_summarizer.domain.value_objects.content import ArticleContent
from wechat_summarizer.domain.value_objects.url import ArticleURL
from wechat_summarizer.shared.exceptions import InvalidURLError


class TestUrlValidationMalformed:
    """畸形URL验证测试"""

    def test_rejects_empty_url(self):
        """拒绝空URL"""
        with pytest.raises(InvalidURLError):
            ArticleURL("")

    def test_rejects_invalid_scheme(self):
        """拒绝无效协议"""
        invalid_schemes = [
            "ftp://example.com/file",
            "file:///etc/passwd",
            "gopher://example.com",
        ]
        for url in invalid_schemes:
            with pytest.raises(InvalidURLError):
                ArticleURL(url)

    def test_rejects_malformed_url(self):
        """拒绝格式错误的URL"""
        malformed_urls = [
            "http://",
            "https://",
        ]
        for url in malformed_urls:
            with pytest.raises(InvalidURLError):
                ArticleURL(url)

    def test_accepts_valid_http_url(self):
        """接受有效HTTP URL"""
        url = ArticleURL("http://example.com/article")
        assert url.value == "http://example.com/article"

    def test_accepts_valid_https_url(self):
        """接受有效HTTPS URL"""
        url = ArticleURL("https://mp.weixin.qq.com/s/abc123")
        assert url.value == "https://mp.weixin.qq.com/s/abc123"

    def test_accepts_url_with_query_params(self):
        """接受带查询参数的URL"""
        url = ArticleURL("https://example.com/article?id=123&ref=home")
        assert "id=123" in url.value

    def test_accepts_url_with_port(self):
        """接受带端口的URL"""
        url = ArticleURL("https://example.com:8080/article")
        assert ":8080" in url.value


class TestSsrfPrevention:
    """SSRF防护测试"""

    def test_rejects_localhost_variations(self):
        """拒绝localhost的各种变体"""
        localhost_variations = [
            "http://localhost/admin",
            "http://127.0.0.1/admin",
            "http://0.0.0.0/admin",
        ]
        for url in localhost_variations:
            with pytest.raises(InvalidURLError):
                ArticleURL(url)

    def test_rejects_private_ip_class_a(self):
        """拒绝A类私有IP (10.x.x.x)"""
        private_ips = [
            "http://10.0.0.1/admin",
            "http://10.255.255.255/admin",
        ]
        for url in private_ips:
            with pytest.raises(InvalidURLError):
                ArticleURL(url)

    def test_rejects_private_ip_class_c(self):
        """拒绝C类私有IP (192.168.x.x)"""
        private_ips = [
            "http://192.168.0.1/admin",
            "http://192.168.1.1/admin",
        ]
        for url in private_ips:
            with pytest.raises(InvalidURLError):
                ArticleURL(url)

    def test_accepts_public_ip(self):
        """接受公网IP"""
        public_ips = [
            "http://8.8.8.8/article",
            "http://1.1.1.1/article",
        ]
        for url in public_ips:
            article_url = ArticleURL(url)
            assert article_url.value == url


class TestXssSanitization:
    """XSS过滤测试"""

    def test_plain_text_strips_script_tags(self):
        """纯文本移除script标签"""
        html = "<p>Hello</p><script>alert('xss')</script><p>World</p>"
        content = ArticleContent(html)

        assert "<script>" not in content.text
        assert "Hello" in content.text
        assert "World" in content.text

    def test_preserves_normal_text_content(self):
        """保留正常文本内容"""
        html = "<h1>标题</h1><p>这是正常的文章内容。</p>"
        content = ArticleContent(html)

        assert "标题" in content.text
        assert "正常的文章内容" in content.text


class TestFilenameSanitization:
    """文件名清理测试"""

    def test_removes_windows_reserved_chars(self):
        """移除Windows保留字符"""
        from wechat_summarizer.infrastructure.adapters.exporters.markdown import MarkdownExporter

        exporter = MarkdownExporter(output_dir="./output")

        # 创建一个带有特殊字符的文章
        article = type(
            "Article",
            (),
            {
                "title": 'file<>:"|?*name',
            },
        )()

        result = exporter._generate_filename(article)

        # 检查危险字符被移除
        for char in '<>:"|?*':
            assert char not in result

    def test_handles_very_long_filename(self):
        """处理超长文件名"""
        from wechat_summarizer.infrastructure.adapters.exporters.markdown import MarkdownExporter

        exporter = MarkdownExporter(output_dir="./output")

        # 创建一个超长标题的文章
        article = type(
            "Article",
            (),
            {
                "title": "a" * 300,
            },
        )()

        result = exporter._generate_filename(article)

        # 结果应该被截断
        assert len(result) <= 60  # 50 + 扩展名

    def test_preserves_chinese_characters(self):
        """保留中文字符"""
        from wechat_summarizer.infrastructure.adapters.exporters.markdown import MarkdownExporter

        exporter = MarkdownExporter(output_dir="./output")

        article = type(
            "Article",
            (),
            {
                "title": "这是一篇中文文章标题",
            },
        )()

        result = exporter._generate_filename(article)

        # 中文字符应该被保留
        assert "中文" in result


class TestContentValidation:
    """内容验证测试"""

    def test_handles_empty_content(self):
        """处理空内容"""
        content = ArticleContent("")
        assert content.html == ""
        assert content.text == ""

    def test_handles_unicode_content(self):
        """处理Unicode内容"""
        unicode_content = "<p>中文内容 🎉 émoji</p>"
        content = ArticleContent(unicode_content)

        assert "中文内容" in content.text
