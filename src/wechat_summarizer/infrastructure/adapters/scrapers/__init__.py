"""抓取器适配器"""

from .base import BaseScraper
from .generic_httpx import GenericHttpxScraper
from .toutiao import ToutiaoScraper
from .wechat_httpx import WechatHttpxScraper
from .wechat_playwright import WechatPlaywrightScraper
from .zhihu import ZhihuScraper

# RSS 抓取器需要可选依赖
try:
    from .rss import FeedEntry, RssScraper, Subscription

    _rss_available = True
except ImportError:
    _rss_available = False
    RssScraper = None  # type: ignore
    FeedEntry = None  # type: ignore
    Subscription = None  # type: ignore

__all__ = [
    "BaseScraper",
    "WechatHttpxScraper",
    "WechatPlaywrightScraper",
    "GenericHttpxScraper",
    "ZhihuScraper",
    "ToutiaoScraper",
    "RssScraper",
    "FeedEntry",
    "Subscription",
]
