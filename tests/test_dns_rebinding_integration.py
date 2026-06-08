"""DNS rebinding 防护接入抓取器的集成测试。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from wechat_summarizer.domain.value_objects import ArticleURL
from wechat_summarizer.infrastructure.adapters.scrapers.generic_httpx import GenericHttpxScraper
from wechat_summarizer.infrastructure.adapters.scrapers.wechat_httpx import WechatHttpxScraper
from wechat_summarizer.shared.exceptions import ScraperBlockedError
from wechat_summarizer.shared.utils.ssrf_protection import SSRFBlockedError, safe_fetch_sync


@pytest.mark.parametrize(
    ("scraper_cls", "url"),
    [
        (WechatHttpxScraper, "https://mp.weixin.qq.com/s/test123"),
        (GenericHttpxScraper, "https://example.com/article"),
    ],
)
def test_scraper_blocks_on_unsafe_dns_resolution(scraper_cls, url: str):
    scraper = scraper_cls(timeout=1)
    article_url = ArticleURL.from_string(url)

    with (
        patch(
            "wechat_summarizer.infrastructure.adapters.scrapers.wechat_httpx.safe_fetch_sync",
            side_effect=SSRFBlockedError("blocked"),
        ),
        patch(
            "wechat_summarizer.infrastructure.adapters.scrapers.generic_httpx.safe_fetch_sync",
            side_effect=SSRFBlockedError("blocked"),
        ),
        pytest.raises(ScraperBlockedError),
    ):
        scraper.scrape(article_url)


def test_wechat_scraper_allows_safe_dns_and_requests():
    scraper = WechatHttpxScraper(timeout=1)
    article_url = ArticleURL.from_string("https://mp.weixin.qq.com/s/test123")

    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None
    fake_response.text = "<html><h1 id='activity-name'>T</h1><div id='js_content'>C</div></html>"

    with (
        patch(
            "wechat_summarizer.infrastructure.adapters.scrapers.wechat_httpx.safe_fetch_sync",
            return_value=fake_response,
        ),
        patch.object(scraper, "_get_with_retry", return_value=fake_response),
    ):
        article = scraper.scrape(article_url)

    assert article.title


def test_scraper_blocks_dns_rebinding_between_validation_and_transport():
    """DNS rebind from public IP to metadata IP must be blocked before connection."""
    scraper = GenericHttpxScraper(timeout=1, max_retries=1)
    article_url = ArticleURL.from_string("https://rebind.example.com/article")
    public_dns = [(2, 1, 6, "", ("93.184.216.34", 443))]
    metadata_dns = [(2, 1, 6, "", ("169.254.169.254", 443))]

    with (
        patch("socket.getaddrinfo", side_effect=[public_dns, metadata_dns]),
        patch.object(httpx.HTTPTransport, "handle_request") as base_transport,
        pytest.raises(ScraperBlockedError, match="SSRF防护拦截"),
    ):
        scraper.scrape(article_url)

    base_transport.assert_not_called()


def test_safe_fetch_sync_blocks_redirect_to_metadata_ip_per_hop():
    """Redirect targets are normalized and validated before the next request."""

    def _redirect_once(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"location": "//169.254.169.254/latest/meta-data"},
            request=request,
        )

    public_dns = [(2, 1, 6, "", ("93.184.216.34", 443))]

    with (
        patch("socket.getaddrinfo", return_value=public_dns),
        patch.object(
            httpx.HTTPTransport, "handle_request", side_effect=_redirect_once
        ) as base_transport,
        pytest.raises(SSRFBlockedError, match=r"169\.254\.169\.254"),
    ):
        safe_fetch_sync("https://redirect.example.com/start", max_redirects=5)

    assert base_transport.call_count == 1


@pytest.mark.parametrize("host", ["2130706433", "0177.0.0.1"])
def test_scraper_blocks_alternative_ip_notation_before_connection(host: str):
    """Alternative IPv4 notations must not reach the HTTP transport."""
    scraper = GenericHttpxScraper(timeout=1, max_retries=1)
    article_url = ArticleURL.from_string(f"https://{host}/article")

    with (
        patch.object(httpx.HTTPTransport, "handle_request") as base_transport,
        pytest.raises(ScraperBlockedError, match="alternative IP notation"),
    ):
        scraper.scrape(article_url)

    base_transport.assert_not_called()
