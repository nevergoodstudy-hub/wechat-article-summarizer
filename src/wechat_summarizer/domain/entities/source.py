"""来源实体"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SourceType(str, Enum):
    """来源类型"""

    WECHAT = "wechat"  # 微信公众号
    RSS = "rss"  # RSS订阅
    WEB = "web"  # 普通网页
    LOCAL = "local"  # 本地文件


@dataclass(frozen=True)
class ArticleSource:
    """
    文章来源值对象

    记录文章的来源信息，包括来源类型、平台名称等。
    """

    type: SourceType = SourceType.WEB
    platform: str = ""  # 平台名称 (如: 微信公众号、知乎等)
    account_id: str | None = None  # 账号ID
    account_name: str | None = None  # 账号名称

    # RSS相关
    feed_url: str | None = None
    feed_title: str | None = None

    # 抓取信息
    scraped_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scraper_name: str = "unknown"

    @classmethod
    def wechat(cls, account_name: str, account_id: str | None = None) -> "ArticleSource":
        """创建微信公众号来源"""
        return cls(
            type=SourceType.WECHAT,
            platform="微信公众号",
            account_id=account_id,
            account_name=account_name,
            scraper_name="wechat_scraper",
        )

    @classmethod
    def rss(cls, feed_url: str, feed_title: str | None = None) -> "ArticleSource":
        """创建RSS来源"""
        return cls(
            type=SourceType.RSS,
            platform="RSS",
            feed_url=feed_url,
            feed_title=feed_title,
            scraper_name="rss_scraper",
        )

    @classmethod
    def web(cls, platform: str = "网页") -> "ArticleSource":
        """创建普通网页来源"""
        return cls(
            type=SourceType.WEB,
            platform=platform,
            scraper_name="web_scraper",
        )
