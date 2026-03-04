"""Scrapers 单元测试

测试抓取器的功能：
- GenericHttpxScraper: can_handle(), scrape() with mocked responses
- WechatHttpxScraper: can_handle(), scrape() with mocked responses
- 错误处理: timeout, 403, 404
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from wechat_summarizer.domain.value_objects import ArticleURL
from wechat_summarizer.infrastructure.adapters.scrapers.generic_httpx import (
    GenericHttpxScraper,
)
from wechat_summarizer.infrastructure.adapters.scrapers.wechat_httpx import (
    WechatHttpxScraper,
)
from wechat_summarizer.shared.exceptions import (
    ScraperBlockedError,
    ScraperError,
    ScraperTimeoutError,
)


@pytest.mark.unit
class TestGenericHttpxScraper:
    """GenericHttpxScraper 测试类"""

    @pytest.fixture
    def scraper(self) -> GenericHttpxScraper:
        """创建 GenericHttpxScraper 实例"""
        return GenericHttpxScraper(timeout=10, max_retries=2)

    @pytest.fixture
    def generic_url(self) -> ArticleURL:
        """通用网页 URL"""
        return ArticleURL.from_string("https://example.com/article/123")

    @pytest.fixture
    def wechat_url(self) -> ArticleURL:
        """微信 URL（GenericHttpxScraper 不应处理）"""
        return ArticleURL.from_string("https://mp.weixin.qq.com/s/test123")

    @pytest.fixture
    def generic_html_response(self) -> str:
        """模拟通用网页 HTML 响应"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta property="og:title" content="测试文章标题">
            <title>测试文章 - 示例网站</title>
        </head>
        <body>
            <nav>导航栏</nav>
            <article>
                <h1>测试文章标题</h1>
                <p>这是文章的正文内容，用于测试通用抓取器。</p>
                <p>这是第二段内容，包含更多测试文本，确保内容足够长。</p>
                <p>这是第三段内容，继续添加更多文本以满足最小字数要求。</p>
                <p>这是第四段内容，通用抓取器会启发式提取这些段落。</p>
                <p>这是第五段内容，确保文章足够长以便测试。</p>
            </article>
            <footer>页脚</footer>
        </body>
        </html>
        """

    def test_scraper_name(self, scraper: GenericHttpxScraper) -> None:
        """测试抓取器名称"""
        assert scraper.name == "generic_httpx"

    def test_can_handle_generic_url(
        self, scraper: GenericHttpxScraper, generic_url: ArticleURL
    ) -> None:
        """测试 can_handle 对通用 URL 返回 True"""
        assert scraper.can_handle(generic_url) is True

    def test_can_handle_rejects_wechat_url(
        self, scraper: GenericHttpxScraper, wechat_url: ArticleURL
    ) -> None:
        """测试 can_handle 对微信 URL 返回 False"""
        assert scraper.can_handle(wechat_url) is False

    def test_scrape_success(
        self,
        scraper: GenericHttpxScraper,
        generic_url: ArticleURL,
        generic_html_response: str,
    ) -> None:
        """测试成功抓取通用网页"""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.text = generic_html_response
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            article = scraper.scrape(generic_url)

            assert article is not None
            assert article.title == "测试文章标题"
            assert article.url == generic_url
            assert "正文内容" in article.content.text

    def test_scrape_timeout_error(
        self, scraper: GenericHttpxScraper, generic_url: ArticleURL
    ) -> None:
        """测试请求超时错误"""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.side_effect = httpx.TimeoutException("Connection timeout")
            mock_client_class.return_value = mock_client

            with pytest.raises(ScraperTimeoutError):
                scraper.scrape(generic_url)

    def test_scrape_http_error(self, scraper: GenericHttpxScraper, generic_url: ArticleURL) -> None:
        """测试 HTTP 错误 (404)"""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=mock_response,
        )

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(ScraperError) as exc_info:
                scraper.scrape(generic_url)

            assert "HTTP错误" in str(exc_info.value)

    def test_extract_title_from_og_meta(
        self, scraper: GenericHttpxScraper, generic_url: ArticleURL
    ) -> None:
        """测试从 og:title 提取标题"""
        html = """
        <html>
        <head><meta property="og:title" content="OG标题"></head>
        <body><article><p>内容内容内容内容内容内容内容内容内容内容</p></article></body>
        </html>
        """
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.text = html
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            article = scraper.scrape(generic_url)
            assert article.title == "OG标题"


@pytest.mark.unit
class TestWechatHttpxScraper:
    """WechatHttpxScraper 测试类"""

    @pytest.fixture
    def scraper(self) -> WechatHttpxScraper:
        """创建 WechatHttpxScraper 实例"""
        return WechatHttpxScraper(timeout=10, max_retries=2)

    @pytest.fixture
    def wechat_url(self) -> ArticleURL:
        """微信公众号 URL"""
        return ArticleURL.from_string("https://mp.weixin.qq.com/s/test123456")

    @pytest.fixture
    def generic_url(self) -> ArticleURL:
        """通用 URL（WechatHttpxScraper 不应处理）"""
        return ArticleURL.from_string("https://example.com/article")

    def test_scraper_name(self, scraper: WechatHttpxScraper) -> None:
        """测试抓取器名称"""
        assert scraper.name == "wechat_httpx"

    def test_can_handle_wechat_url(
        self, scraper: WechatHttpxScraper, wechat_url: ArticleURL
    ) -> None:
        """测试 can_handle 对微信 URL 返回 True"""
        assert scraper.can_handle(wechat_url) is True

    def test_can_handle_rejects_generic_url(
        self, scraper: WechatHttpxScraper, generic_url: ArticleURL
    ) -> None:
        """测试 can_handle 对通用 URL 返回 False"""
        assert scraper.can_handle(generic_url) is False

    def test_scrape_success(
        self,
        scraper: WechatHttpxScraper,
        wechat_url: ArticleURL,
        wechat_html_response: str,
    ) -> None:
        """测试成功抓取微信文章 (使用 conftest fixture)"""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.text = wechat_html_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(scraper, "_get_with_retry", return_value=mock_response):
            article = scraper.scrape(wechat_url)

            assert article is not None
            assert article.title == "测试文章标题"
            assert article.url == wechat_url
            assert "正文内容" in article.content.text

    def test_scrape_timeout_error(
        self, scraper: WechatHttpxScraper, wechat_url: ArticleURL
    ) -> None:
        """测试请求超时错误"""
        with patch.object(
            scraper,
            "_get_with_retry",
            side_effect=httpx.TimeoutException("Connection timeout"),
        ), pytest.raises(ScraperTimeoutError):
            scraper.scrape(wechat_url)

    def test_scrape_blocked_error_403(
        self, scraper: WechatHttpxScraper, wechat_url: ArticleURL
    ) -> None:
        """测试被封禁错误 (403)"""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Forbidden",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(
            scraper, "_get_with_retry", return_value=mock_response
        ), pytest.raises(ScraperBlockedError):
            scraper.scrape(wechat_url)


    def test_scrape_blocked_error_429(
        self, scraper: WechatHttpxScraper, wechat_url: ArticleURL
    ) -> None:
        """测试限流错误 (429)"""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Too Many Requests",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(
            scraper, "_get_with_retry", return_value=mock_response
        ), pytest.raises(ScraperBlockedError):
            scraper.scrape(wechat_url)

    def test_scrape_http_error_404(
        self, scraper: WechatHttpxScraper, wechat_url: ArticleURL
    ) -> None:
        """测试 HTTP 错误 (404)"""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(scraper, "_get_with_retry", return_value=mock_response):
            with pytest.raises(ScraperError) as exc_info:
                scraper.scrape(wechat_url)

            assert "HTTP错误" in str(exc_info.value)

    def test_scrape_empty_content_error(
        self, scraper: WechatHttpxScraper, wechat_url: ArticleURL
    ) -> None:
        """测试无法提取内容时的错误"""
        empty_html = """
        <html>
        <head><title>空文章</title></head>
        <body><div>没有正文内容</div></body>
        </html>
        """
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.text = empty_html
        mock_response.raise_for_status = MagicMock()

        with patch.object(scraper, "_get_with_retry", return_value=mock_response):
            with pytest.raises(ScraperError) as exc_info:
                scraper.scrape(wechat_url)

            assert "无法提取" in str(exc_info.value)

    def test_extract_title_from_rich_media_title(
        self, scraper: WechatHttpxScraper, wechat_url: ArticleURL
    ) -> None:
        """测试从 rich_media_title 提取标题"""
        html = """
        <html>
        <head><title>fallback标题</title></head>
        <body>
            <h1 class="rich_media_title">微信文章标题</h1>
            <div id="js_content"><p>正文内容</p></div>
        </body>
        </html>
        """
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.text = html
        mock_response.raise_for_status = MagicMock()

        with patch.object(scraper, "_get_with_retry", return_value=mock_response):
            article = scraper.scrape(wechat_url)
            assert article.title == "微信文章标题"

    def test_scraper_close(self, scraper: WechatHttpxScraper) -> None:
        """测试关闭抓取器"""
        # 不应抛出异常
        scraper.close()

    def test_user_agent_rotation(self) -> None:
        """测试 User-Agent 轮换"""
        scraper = WechatHttpxScraper(user_agent_rotation=True)
        ua1 = scraper._choose_user_agent()

        # 多次调用可能返回不同的 UA（由于随机性）
        # 这里只验证返回的是有效字符串
        assert isinstance(ua1, str)
        assert len(ua1) > 0

    def test_user_agent_no_rotation(self) -> None:
        """测试禁用 User-Agent 轮换"""
        scraper = WechatHttpxScraper(user_agent_rotation=False)
        ua1 = scraper._choose_user_agent()
        ua2 = scraper._choose_user_agent()

        # 禁用轮换时应返回相同的 UA
        assert ua1 == ua2


@pytest.mark.unit
class TestArticleURLIntegration:
    """ArticleURL 与 Scraper 的集成测试"""

    def test_url_is_wechat_property(self) -> None:
        """测试 ArticleURL.is_wechat 属性"""
        wechat_url = ArticleURL.from_string("https://mp.weixin.qq.com/s/abc123")
        generic_url = ArticleURL.from_string("https://example.com/article")

        assert wechat_url.is_wechat is True
        assert generic_url.is_wechat is False

    def test_url_scheme_property(self) -> None:
        """测试 ArticleURL.scheme 属性"""
        https_url = ArticleURL.from_string("https://example.com/article")
        http_url = ArticleURL.from_string("http://example.com/article")

        assert https_url.scheme == "https"
        assert http_url.scheme == "http"

    def test_url_domain_property(self) -> None:
        """测试 ArticleURL.domain 属性"""
        url = ArticleURL.from_string("https://mp.weixin.qq.com/s/abc123")
        assert url.domain == "mp.weixin.qq.com"
