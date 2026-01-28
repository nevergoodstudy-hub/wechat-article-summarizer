"""通用网页抓取器 - 支持任意网页"""

from __future__ import annotations

import random

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from ....domain.entities import Article, ArticleSource, SourceType
from ....domain.value_objects import ArticleContent, ArticleURL
from ....shared.constants import USER_AGENTS
from ....shared.exceptions import ScraperError, ScraperTimeoutError
from .base import BaseScraper


class GenericHttpxScraper(BaseScraper):
    """
    通用网页抓取器

    支持抓取任意 HTTP/HTTPS 网页，使用启发式算法提取正文内容。
    适用于非微信公众号的通用文章抓取。
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        proxy: str | None = None,
        user_agent_rotation: bool = True,
    ):
        self._timeout = timeout
        self._max_retries = max_retries
        self._proxy = proxy
        self._user_agent_rotation = user_agent_rotation

    @property
    def name(self) -> str:
        return "generic_httpx"

    def can_handle(self, url: ArticleURL) -> bool:
        """支持所有非微信公众号的 HTTP/HTTPS URL（作为后备抓取器）"""
        return url.scheme in ("http", "https") and not url.is_wechat

    def scrape(self, url: ArticleURL) -> Article:
        """抓取通用网页"""
        logger.debug(f"通用抓取器开始抓取: {url}")

        headers = {
            "User-Agent": self._choose_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        try:
            with httpx.Client(
                timeout=self._timeout,
                follow_redirects=True,
                proxy=self._proxy,
            ) as client:
                response = client.get(str(url), headers=headers)
                response.raise_for_status()
        except httpx.TimeoutException as e:
            raise ScraperTimeoutError(f"请求超时: {e}") from e
        except httpx.HTTPStatusError as e:
            raise ScraperError(f"HTTP错误 ({e.response.status_code})") from e
        except Exception as e:
            raise ScraperError(f"网络错误: {e}") from e

        return self._parse_html(response.text, url)

    def _choose_user_agent(self) -> str:
        if self._user_agent_rotation:
            return random.choice(USER_AGENTS)
        return USER_AGENTS[0]

    def _parse_html(self, html: str, url: ArticleURL) -> Article:
        """解析HTML内容，使用启发式算法提取正文"""
        soup = BeautifulSoup(html, "html.parser")

        # 移除脚本和样式
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        # 提取标题
        title = self._extract_title(soup)

        # 提取正文（启发式算法）
        content_html = self._extract_content_heuristic(soup)

        if not content_html:
            # 降级：取 body 内容
            body = soup.find("body")
            content_html = str(body) if body else str(soup)

        content = ArticleContent.from_html(content_html)

        # 创建来源
        source = ArticleSource(
            type=SourceType.WEB,
            platform=url.domain,
            scraper_name=self.name,
        )

        return Article(
            url=url,
            title=title,
            content=content,
            source=source,
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        # 优先级：og:title > h1 > title
        og_title = soup.find("meta", property="og:title")
        if og_title:
            content = og_title.get("content")
            if content:
                return str(content).strip()

        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        title = soup.find("title")
        if title:
            return title.get_text(strip=True)

        return "无标题"

    def _extract_content_heuristic(self, soup: BeautifulSoup) -> str:
        """启发式提取正文内容"""
        # 常见的正文容器选择器
        content_selectors = [
            "article",
            '[role="main"]',
            ".article-content",
            ".post-content",
            ".entry-content",
            ".content",
            ".main-content",
            "#content",
            "#article",
            ".article",
        ]

        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem and len(elem.get_text(strip=True)) > 200:
                return str(elem)

        # 降级：寻找包含最多文字的 div
        max_text_len = 0
        best_elem = None

        for div in soup.find_all("div"):
            text = div.get_text(strip=True)
            # 排除太短或包含太多链接的 div
            links = div.find_all("a")
            if len(text) > max_text_len and len(text) > 200:
                link_text_ratio = sum(len(a.get_text()) for a in links) / max(len(text), 1)
                if link_text_ratio < 0.5:  # 链接文本不超过总文本的50%
                    max_text_len = len(text)
                    best_elem = div

        return str(best_elem) if best_elem else ""

    async def scrape_async(self, url: ArticleURL) -> Article:
        """异步抓取通用网页"""
        logger.debug(f"通用抓取器异步抓取: {url}")

        headers = {
            "User-Agent": self._choose_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                proxy=self._proxy,
            ) as client:
                response = await client.get(str(url), headers=headers)
                response.raise_for_status()
        except httpx.TimeoutException as e:
            raise ScraperTimeoutError(f"请求超时: {e}") from e
        except httpx.HTTPStatusError as e:
            raise ScraperError(f"HTTP错误 ({e.response.status_code})") from e
        except Exception as e:
            raise ScraperError(f"网络错误: {e}") from e

        return self._parse_html(response.text, url)
