"""RSS/Atom 订阅抓取器

支持 RSS 和 Atom feed 的解析，并抓取全文内容。
需要安装可选依赖：pip install wechat-summarizer[rss]
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from loguru import logger

from ....domain.entities import Article, ArticleSource, SourceType
from ....domain.value_objects import ArticleContent, ArticleURL
from ....shared.constants import CONFIG_DIR_NAME
from ....shared.exceptions import ScraperError

if TYPE_CHECKING:
    from .generic_httpx import GenericHttpxScraper

# 检查 feedparser 是否可用
_feedparser_available = False
try:
    import feedparser

    _feedparser_available = True
except ImportError:
    pass


@dataclass
class FeedEntry:
    """Feed 条目"""

    title: str
    link: str
    summary: str = ""
    published: datetime | None = None
    author: str | None = None
    id: str = ""


@dataclass
class Subscription:
    """订阅信息"""

    url: str
    title: str = ""
    added_at: datetime = field(default_factory=datetime.now)
    last_sync: datetime | None = None
    processed_ids: set[str] = field(default_factory=set)


class RssScraper:
    """
    RSS/Atom 订阅抓取器

    解析 RSS feed 并抓取文章全文。
    """

    def __init__(
        self,
        generic_scraper: GenericHttpxScraper | None = None,
        subscriptions_file: str | Path | None = None,
    ):
        """
        Args:
            generic_scraper: 通用抓取器（用于获取全文）
            subscriptions_file: 订阅存储文件路径
        """
        if not _feedparser_available:
            raise ImportError(
                "feedparser 未安装，请运行: pip install wechat-summarizer[rss]"
            )

        self._generic_scraper = generic_scraper
        self._subscriptions_file = Path(subscriptions_file) if subscriptions_file else (
            Path.home() / CONFIG_DIR_NAME / "subscriptions.json"
        )
        self._subscriptions: dict[str, Subscription] = self._load_subscriptions()

    @property
    def name(self) -> str:
        return "rss"

    def is_available(self) -> bool:
        """检查是否可用"""
        return _feedparser_available

    def parse_feed(self, feed_url: str) -> list[FeedEntry]:
        """
        解析 RSS/Atom feed

        Args:
            feed_url: Feed URL

        Returns:
            Feed 条目列表
        """
        logger.debug(f"解析 feed: {feed_url}")

        try:
            # 获取 feed 内容
            with httpx.Client(timeout=30, follow_redirects=True) as client:
                response = client.get(feed_url)
                response.raise_for_status()
                content = response.text
        except Exception as e:
            raise ScraperError(f"获取 feed 失败: {e}") from e

        # 解析 feed
        feed = feedparser.parse(content)

        if feed.bozo:
            logger.warning(f"Feed 解析有警告: {feed.bozo_exception}")

        entries = []
        for entry in feed.entries:
            # 提取发布时间
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6])
                except Exception:
                    pass

            entries.append(
                FeedEntry(
                    title=getattr(entry, "title", "无标题"),
                    link=getattr(entry, "link", ""),
                    summary=getattr(entry, "summary", ""),
                    published=published,
                    author=getattr(entry, "author", None),
                    id=getattr(entry, "id", entry.link if hasattr(entry, "link") else ""),
                )
            )

        logger.info(f"解析到 {len(entries)} 条 feed 条目")
        return entries

    def scrape_entry(self, entry: FeedEntry) -> Article:
        """
        抓取单个 feed 条目的全文

        Args:
            entry: Feed 条目

        Returns:
            文章实体
        """
        if not entry.link:
            raise ScraperError("条目缺少链接")

        # 如果有通用抓取器，使用它获取全文
        if self._generic_scraper:
            try:
                url = ArticleURL.from_string(entry.link)
                article = self._generic_scraper.scrape(url)
                # 使用 feed 中的元数据补充
                if not article.author and entry.author:
                    article = Article(
                        id=article.id,
                        url=article.url,
                        title=article.title,
                        author=entry.author,
                        publish_time=entry.published or article.publish_time,
                        content=article.content,
                        source=article.source,
                    )
                return article
            except Exception as e:
                logger.warning(f"全文抓取失败，使用 feed 摘要: {e}")

        # 降级：使用 feed 中的摘要
        url = ArticleURL.from_string(entry.link)
        content = ArticleContent.from_html(entry.summary) if entry.summary else ArticleContent(
            html="", text="", images=()
        )

        source = ArticleSource(
            type=SourceType.RSS,
            platform="RSS",
            scraper_name=self.name,
        )

        return Article(
            url=url,
            title=entry.title,
            author=entry.author,
            publish_time=entry.published,
            content=content,
            source=source,
        )

    # -------------------- 订阅管理 --------------------

    def add_subscription(self, feed_url: str) -> Subscription:
        """添加订阅"""
        if feed_url in self._subscriptions:
            return self._subscriptions[feed_url]

        # 获取 feed 标题
        title = ""
        try:
            with httpx.Client(timeout=30, follow_redirects=True) as client:
                response = client.get(feed_url)
                response.raise_for_status()
                feed = feedparser.parse(response.text)
                title = getattr(feed.feed, "title", "")
        except Exception as e:
            logger.warning(f"获取 feed 标题失败: {e}")

        subscription = Subscription(url=feed_url, title=title)
        self._subscriptions[feed_url] = subscription
        self._save_subscriptions()

        logger.info(f"已添加订阅: {title or feed_url}")
        return subscription

    def remove_subscription(self, feed_url: str) -> bool:
        """移除订阅"""
        if feed_url in self._subscriptions:
            del self._subscriptions[feed_url]
            self._save_subscriptions()
            logger.info(f"已移除订阅: {feed_url}")
            return True
        return False

    def list_subscriptions(self) -> list[Subscription]:
        """列出所有订阅"""
        return list(self._subscriptions.values())

    def sync_subscription(
        self,
        feed_url: str,
        limit: int = 10,
    ) -> list[FeedEntry]:
        """
        同步订阅，返回新条目

        Args:
            feed_url: Feed URL
            limit: 最大返回条目数

        Returns:
            新的 feed 条目列表
        """
        if feed_url not in self._subscriptions:
            raise ScraperError(f"未找到订阅: {feed_url}")

        subscription = self._subscriptions[feed_url]
        entries = self.parse_feed(feed_url)

        # 过滤已处理的条目
        new_entries = [
            e for e in entries
            if e.id not in subscription.processed_ids
        ][:limit]

        # 更新已处理 ID
        for entry in new_entries:
            subscription.processed_ids.add(entry.id)

        subscription.last_sync = datetime.now()
        self._save_subscriptions()

        logger.info(f"同步 {feed_url}: 发现 {len(new_entries)} 条新条目")
        return new_entries

    def sync_all(self, limit_per_feed: int = 5) -> dict[str, list[FeedEntry]]:
        """
        同步所有订阅

        Args:
            limit_per_feed: 每个 feed 的最大条目数

        Returns:
            {feed_url: [新条目列表]}
        """
        results = {}
        for feed_url in self._subscriptions:
            try:
                entries = self.sync_subscription(feed_url, limit=limit_per_feed)
                results[feed_url] = entries
            except Exception as e:
                logger.error(f"同步 {feed_url} 失败: {e}")
                results[feed_url] = []
        return results

    # -------------------- 存储 --------------------

    def _load_subscriptions(self) -> dict[str, Subscription]:
        """加载订阅列表"""
        if not self._subscriptions_file.exists():
            return {}

        try:
            data = json.loads(self._subscriptions_file.read_text(encoding="utf-8"))
            subscriptions = {}
            for url, info in data.items():
                subscriptions[url] = Subscription(
                    url=url,
                    title=info.get("title", ""),
                    added_at=datetime.fromisoformat(info["added_at"]) if info.get("added_at") else datetime.now(),
                    last_sync=datetime.fromisoformat(info["last_sync"]) if info.get("last_sync") else None,
                    processed_ids=set(info.get("processed_ids", [])),
                )
            return subscriptions
        except Exception as e:
            logger.warning(f"加载订阅列表失败: {e}")
            return {}

    def _save_subscriptions(self) -> None:
        """保存订阅列表"""
        self._subscriptions_file.parent.mkdir(parents=True, exist_ok=True)

        data = {}
        for url, sub in self._subscriptions.items():
            data[url] = {
                "title": sub.title,
                "added_at": sub.added_at.isoformat(),
                "last_sync": sub.last_sync.isoformat() if sub.last_sync else None,
                "processed_ids": list(sub.processed_ids)[-1000],  # 只保留最近 1000 个
            }

        self._subscriptions_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
