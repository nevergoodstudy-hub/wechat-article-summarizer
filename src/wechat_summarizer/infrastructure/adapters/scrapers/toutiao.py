"""头条号抓取器

支持今日头条文章的抓取。
头条号使用动态渲染，部分内容可能需要 Playwright。
"""

from __future__ import annotations

import asyncio
import random
import re
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from ....domain.entities import Article, ArticleSource, SourceType
from ....domain.value_objects import ArticleContent, ArticleURL
from ....shared.constants import USER_AGENTS
from ....shared.exceptions import ScraperBlockedError, ScraperError, ScraperTimeoutError
from .base import BaseScraper


class ToutiaoScraper(BaseScraper):
    """
    今日头条抓取器

    支持头条号文章的抓取。
    """

    # 头条文章 URL 模式
    ARTICLE_PATTERN = re.compile(r"toutiao\.com/(?:article|a\d+|i\d+)/(\d+)")
    # 头条号主页 URL 模式
    HOMEPAGE_PATTERN = re.compile(r"toutiao\.com/c/user/(\d+)")

    def __init__(
        self,
        timeout: int = 30,
        user_agent_rotation: bool = True,
        request_delay: tuple[float, float] = (0.5, 2.0),
    ):
        """
        Args:
            timeout: 请求超时时间
            user_agent_rotation: 是否轮换 User-Agent
            request_delay: 请求间隔范围（秒）
        """
        self._timeout = timeout
        self._user_agent_rotation = user_agent_rotation
        self._request_delay = request_delay

    @property
    def name(self) -> str:
        return "toutiao"

    def can_handle(self, url: ArticleURL) -> bool:
        """判断是否能处理该 URL"""
        url_str = str(url)
        return "toutiao.com" in url_str and bool(self.ARTICLE_PATTERN.search(url_str))

    def _get_headers(self) -> dict[str, str]:
        """获取请求头"""
        return {
            "User-Agent": self._choose_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.toutiao.com/",
        }

    def _choose_user_agent(self) -> str:
        if self._user_agent_rotation:
            return random.choice(USER_AGENTS)
        return USER_AGENTS[0]

    def scrape(self, url: ArticleURL) -> Article:
        """抓取头条文章"""
        logger.debug(f"头条抓取器开始抓取: {url}")

        headers = self._get_headers()

        try:
            with httpx.Client(
                timeout=self._timeout,
                follow_redirects=True,
            ) as client:
                response = client.get(str(url), headers=headers)
        except httpx.TimeoutException as e:
            raise ScraperTimeoutError(f"请求超时: {e}") from e
        except httpx.TransportError as e:
            raise ScraperError(f"网络错误: {e}") from e

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status in (401, 403, 429):
                raise ScraperBlockedError(f"请求被拒绝 (HTTP {status})") from e
            raise ScraperError(f"HTTP错误 (HTTP {status})") from e

        return self._parse_html(response.text, url)

    async def scrape_async(self, url: ArticleURL) -> Article:
        """异步抓取头条文章"""
        logger.debug(f"头条抓取器异步抓取: {url}")

        # 随机延迟
        delay = random.uniform(*self._request_delay)
        await asyncio.sleep(delay)

        headers = self._get_headers()

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
            ) as client:
                response = await client.get(str(url), headers=headers)
        except httpx.TimeoutException as e:
            raise ScraperTimeoutError(f"请求超时: {e}") from e
        except httpx.TransportError as e:
            raise ScraperError(f"网络错误: {e}") from e

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status in (401, 403, 429):
                raise ScraperBlockedError(f"请求被拒绝 (HTTP {status})") from e
            raise ScraperError(f"HTTP错误 (HTTP {status})") from e

        return self._parse_html(response.text, url)

    def _parse_html(self, html: str, url: ArticleURL) -> Article:
        """解析头条页面"""
        soup = BeautifulSoup(html, "html.parser")

        # 提取标题
        title = self._extract_title(soup)

        # 提取作者
        author = self._extract_author(soup)

        # 提取发布时间
        publish_time = self._extract_publish_time(soup, html)

        # 提取正文
        content_html = self._extract_content(soup, html)
        if not content_html:
            raise ScraperError("无法提取文章内容，可能需要使用 Playwright 渲染")

        content = ArticleContent.from_html(content_html)

        # 创建来源
        source = ArticleSource(
            type=SourceType.WEB,
            platform="今日头条",
            scraper_name=self.name,
        )

        return Article(
            url=url,
            title=title,
            author=author,
            account_name="今日头条",
            publish_time=publish_time,
            content=content,
            source=source,
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        # 尝试多种方式
        selectors = [
            ("h1", {"class": "article-title"}),
            ("h1", None),
            ("meta", {"property": "og:title"}),
            ("title", None),
        ]

        for tag, attrs in selectors:
            elem = soup.find(tag, attrs=attrs) if attrs else soup.find(tag)
            if elem:
                if tag == "meta":
                    content = elem.get("content")
                    if content:
                        # 清理头条特有的后缀
                        title = str(content).strip()
                        if " - 今日头条" in title:
                            title = title.replace(" - 今日头条", "")
                        return title
                else:
                    return elem.get_text(strip=True)

        return "无标题"

    def _extract_author(self, soup: BeautifulSoup) -> str | None:
        """提取作者"""
        # 尝试从 meta 标签获取
        author_meta = soup.find("meta", {"name": "author"})
        if author_meta:
            content = author_meta.get("content")
            if content:
                return str(content).strip()

        # 尝试从页面元素获取
        author_selectors = [
            "a.name",
            "span.name",
            ".user-info .name",
            ".article-sub .name",
        ]

        for selector in author_selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)

        return None

    def _extract_publish_time(self, soup: BeautifulSoup, html: str) -> datetime | None:
        """提取发布时间"""
        # 尝试从 meta 标签获取
        time_meta = soup.find("meta", {"property": "article:published_time"})
        if time_meta:
            time_str = time_meta.get("content")
            if time_str:
                try:
                    return datetime.fromisoformat(str(time_str).replace("Z", "+00:00"))
                except ValueError:
                    pass

        # 尝试从 JSON 数据中提取
        time_patterns = [
            r'"publish_time":\s*(\d+)',
            r'"time":\s*"(\d{4}-\d{2}-\d{2})"',
            r'发布时间[：:]\s*(\d{4}-\d{2}-\d{2})',
        ]

        for pattern in time_patterns:
            match = re.search(pattern, html)
            if match:
                time_val = match.group(1)
                try:
                    if time_val.isdigit() and len(time_val) >= 10:
                        # Unix 时间戳（秒）
                        timestamp = int(time_val[:10])
                        return datetime.fromtimestamp(timestamp)
                    else:
                        return datetime.strptime(time_val, "%Y-%m-%d")
                except (ValueError, OSError):
                    pass

        return None

    def _extract_content(self, soup: BeautifulSoup, html: str) -> str:
        """提取正文内容"""
        # 尝试多种选择器
        selectors = [
            "article",
            ".article-content",
            ".content-article",
            "#article-content",
            ".article-body",
            ".tt-article-content",
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                # 清理不需要的元素
                for unwanted in elem.find_all(["script", "style", "iframe", "noscript"]):
                    unwanted.decompose()
                return str(elem)

        # 降级：尝试从 JSON 数据中提取
        content_pattern = r'"content":\s*"([^"]+)"'
        match = re.search(content_pattern, html)
        if match:
            content = match.group(1)
            # 解码 Unicode 转义
            try:
                content = content.encode("utf-8").decode("unicode_escape")
                return f"<div>{content}</div>"
            except Exception:
                pass

        return ""
