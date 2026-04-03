"""DNS rebinding 防护接入抓取器的集成测试。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from wechat_summarizer.domain.value_objects import ArticleURL
from wechat_summarizer.infrastructure.adapters.scrapers.generic_httpx import GenericHttpxScraper
from wechat_summarizer.infrastructure.adapters.scrapers.wechat_httpx import WechatHttpxScraper
from wechat_summarizer.shared.exceptions import ScraperBlockedError
from wechat_summarizer.shared.utils.ssrf_protection import SSRFBlockedError


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

    with patch(
        "wechat_summarizer.infrastructure.adapters.scrapers.wechat_httpx.safe_fetch_sync",
        side_effect=SSRFBlockedError("blocked"),
    ), patch(
        "wechat_summarizer.infrastructure.adapters.scrapers.generic_httpx.safe_fetch_sync",
        side_effect=SSRFBlockedError("blocked"),
    ):
        with pytest.raises(ScraperBlockedError):
            scraper.scrape(article_url)


def test_wechat_scraper_allows_safe_dns_and_requests():
    scraper = WechatHttpxScraper(timeout=1)
    article_url = ArticleURL.from_string("https://mp.weixin.qq.com/s/test123")

    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None
    fake_response.text = "<html><h1 id='activity-name'>T</h1><div id='js_content'>C</div></html>"

    with patch(
        "wechat_summarizer.infrastructure.adapters.scrapers.wechat_httpx.safe_fetch_sync",
        return_value=fake_response,
    ), patch.object(scraper, "_get_with_retry", return_value=fake_response):
        article = scraper.scrape(article_url)

    assert article.title
