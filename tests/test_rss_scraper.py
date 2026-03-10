"""RSS 抓取器安全相关测试。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from wechat_summarizer.infrastructure.adapters.scrapers.rss import RssScraper


def test_parse_feed_uses_safe_client(tmp_path: Path) -> None:
    """解析 feed 时应通过安全客户端获取远程内容。"""
    scraper = RssScraper(subscriptions_file=tmp_path / "subscriptions.json")
    response = MagicMock()
    response.text = """<?xml version="1.0"?><rss><channel><title>示例订阅</title></channel></rss>"""
    response.raise_for_status = MagicMock()

    client = MagicMock()
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    client.get.return_value = response

    with patch(
        "wechat_summarizer.infrastructure.adapters.scrapers.rss.create_safe_client",
        return_value=client,
    ) as mock_factory:
        scraper.parse_feed("https://example.com/feed.xml")

    mock_factory.assert_called_once()
    client.get.assert_called_once_with("https://example.com/feed.xml")
