"""知乎专栏抓取器

支持知乎专栏文章和知乎回答的抓取。
包含反爬策略：Cookie 支持、User-Agent 轮换、请求间隔随机化。
"""

from __future__ import annotations

import asyncio
import random
import re
from datetime import datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from ....domain.entities import Article, ArticleSource, SourceType
from ....domain.value_objects import ArticleContent, ArticleURL
from ....shared.constants import USER_AGENTS
from ....shared.exceptions import ScraperBlockedError, ScraperError, ScraperTimeoutError
from .base import BaseScraper


class ZhihuScraper(BaseScraper):
    """
    知乎抓取器

    支持知乎专栏文章和知乎回答的抓取。
    """

    # 知乎专栏文章 URL 模式
    ZHUANLAN_PATTERN = re.compile(r"zhuanlan\.zhihu\.com/p/(\d+)")
    # 知乎回答 URL 模式
    ANSWER_PATTERN = re.compile(r"zhihu\.com/question/(\d+)/answer/(\d+)")

    def __init__(
        self,
        timeout: int = 30,
        cookie: str | None = None,
        user_agent_rotation: bool = True,
        request_delay: tuple[float, float] = (1.0, 3.0),
    ):
        """
        Args:
            timeout: 请求超时时间
            cookie: 知乎 Cookie（可选，用于访问私有内容）
            user_agent_rotation: 是否轮换 User-Agent
            request_delay: 请求间隔范围（秒）
        """
        self._timeout = timeout
        self._cookie = cookie
        self._user_agent_rotation = user_agent_rotation
        self._request_delay = request_delay

    @property
    def name(self) -> str:
        return "zhihu"

    def can_handle(self, url: ArticleURL) -> bool:
        """判断是否能处理该 URL"""
        url_str = str(url)
        return bool(
            self.ZHUANLAN_PATTERN.search(url_str) or self.ANSWER_PATTERN.search(url_str)
        )

    def _get_headers(self) -> dict[str, str]:
        """获取请求头"""
        headers = {
            "User-Agent": self._choose_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.zhihu.com/",
        }

        if self._cookie:
            headers["Cookie"] = self._cookie

        return headers

    def _choose_user_agent(self) -> str:
        if self._user_agent_rotation:
            return random.choice(USER_AGENTS)
        return USER_AGENTS[0]

    def scrape(self, url: ArticleURL) -> Article:
        """抓取知乎内容"""
        logger.debug(f"知乎抓取器开始抓取: {url}")

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

        # 检查响应状态
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status in (401, 403):
                raise ScraperBlockedError(
                    f"访问被拒绝 (HTTP {status})，可能需要登录或 Cookie"
                ) from e
            if status == 429:
                raise ScraperBlockedError("请求过于频繁，被限流") from e
            raise ScraperError(f"HTTP错误 (HTTP {status})") from e

        # 检查是否需要登录
        if "请先登录" in response.text or "登录知乎" in response.text:
            raise ScraperBlockedError("需要登录才能查看此内容，请配置 Cookie")

        return self._parse_html(response.text, url)

    async def scrape_async(self, url: ArticleURL) -> Article:
        """异步抓取知乎内容"""
        logger.debug(f"知乎抓取器异步抓取: {url}")

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
            if status in (401, 403):
                raise ScraperBlockedError(
                    f"访问被拒绝 (HTTP {status})，可能需要登录或 Cookie"
                ) from e
            if status == 429:
                raise ScraperBlockedError("请求过于频繁，被限流") from e
            raise ScraperError(f"HTTP错误 (HTTP {status})") from e

        if "请先登录" in response.text or "登录知乎" in response.text:
            raise ScraperBlockedError("需要登录才能查看此内容，请配置 Cookie")

        return self._parse_html(response.text, url)

    def _parse_html(self, html: str, url: ArticleURL) -> Article:
        """解析知乎页面"""
        soup = BeautifulSoup(html, "html.parser")
        url_str = str(url)

        if self.ZHUANLAN_PATTERN.search(url_str):
            return self._parse_zhuanlan(soup, url)
        elif self.ANSWER_PATTERN.search(url_str):
            return self._parse_answer(soup, url)
        else:
            raise ScraperError(f"无法识别的知乎 URL 格式: {url}")

    def _parse_zhuanlan(self, soup: BeautifulSoup, url: ArticleURL) -> Article:
        """解析知乎专栏文章"""
        # 提取标题
        title = self._extract_title(soup)

        # 提取作者
        author = self._extract_author(soup)

        # 提取发布时间
        publish_time = self._extract_publish_time(soup)

        # 提取正文
        content_html = self._extract_zhuanlan_content(soup)
        if not content_html:
            raise ScraperError("无法提取文章内容")

        # 处理懒加载图片
        content_html = self._process_lazy_images(content_html)

        content = ArticleContent.from_html(content_html)

        # 创建来源
        source = ArticleSource(
            type=SourceType.WEB,
            platform="知乎专栏",
            scraper_name=self.name,
        )

        return Article(
            url=url,
            title=title,
            author=author,
            account_name="知乎专栏",
            publish_time=publish_time,
            content=content,
            source=source,
        )

    def _parse_answer(self, soup: BeautifulSoup, url: ArticleURL) -> Article:
        """解析知乎回答"""
        # 提取问题标题
        question_title = ""
        question_elem = soup.find("h1", class_="QuestionHeader-title")
        if question_elem:
            question_title = question_elem.get_text(strip=True)

        # 提取回答者
        author = self._extract_answer_author(soup)

        # 提取回答内容
        content_html = self._extract_answer_content(soup)
        if not content_html:
            raise ScraperError("无法提取回答内容")

        # 处理懒加载图片
        content_html = self._process_lazy_images(content_html)

        content = ArticleContent.from_html(content_html)

        # 创建来源
        source = ArticleSource(
            type=SourceType.WEB,
            platform="知乎",
            scraper_name=self.name,
        )

        title = f"{question_title} - {author}的回答" if question_title else f"{author}的回答"

        return Article(
            url=url,
            title=title,
            author=author,
            account_name="知乎",
            content=content,
            source=source,
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取专栏文章标题"""
        # 尝试多种方式
        selectors = [
            ("h1", {"class": "Post-Title"}),
            ("h1", {"class": "css-1g7fi5x"}),
            ("meta", {"property": "og:title"}),
            ("title", None),
        ]

        for tag, attrs in selectors:
            elem = soup.find(tag, attrs=attrs) if attrs else soup.find(tag)
            if elem:
                if tag == "meta":
                    content = elem.get("content")
                    if content:
                        return str(content).strip()
                else:
                    return elem.get_text(strip=True)

        return "无标题"

    def _extract_author(self, soup: BeautifulSoup) -> str | None:
        """提取专栏文章作者"""
        # 尝试从 meta 标签获取
        author_meta = soup.find("meta", {"name": "author"})
        if author_meta:
            content = author_meta.get("content")
            if content:
                return str(content).strip()

        # 尝试从作者链接获取
        author_link = soup.find("a", class_="UserLink-link")
        if author_link:
            return author_link.get_text(strip=True)

        return None

    def _extract_answer_author(self, soup: BeautifulSoup) -> str:
        """提取回答作者"""
        author_elem = soup.find("span", class_="AuthorInfo-name")
        if author_elem:
            link = author_elem.find("a")
            if link:
                return link.get_text(strip=True)
            return author_elem.get_text(strip=True)

        return "匿名用户"

    def _extract_publish_time(self, soup: BeautifulSoup) -> datetime | None:
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

        # 尝试从页面元素获取
        time_elem = soup.find("time")
        if time_elem:
            datetime_attr = time_elem.get("datetime")
            if datetime_attr:
                try:
                    return datetime.fromisoformat(str(datetime_attr).replace("Z", "+00:00"))
                except ValueError:
                    pass

        return None

    def _extract_zhuanlan_content(self, soup: BeautifulSoup) -> str:
        """提取专栏文章正文"""
        # 尝试多种选择器
        selectors = [
            "div.Post-RichTextContainer",
            "div.RichText",
            "div.Post-content",
            "article",
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return str(elem)

        return ""

    def _extract_answer_content(self, soup: BeautifulSoup) -> str:
        """提取回答正文"""
        # 尝试多种选择器
        selectors = [
            "div.RichContent-inner",
            "div.AnswerItem-content",
            "span.RichText",
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return str(elem)

        return ""

    def _process_lazy_images(self, html: str) -> str:
        """处理懒加载图片（将 data-original 或 data-src 转为 src）"""
        soup = BeautifulSoup(html, "html.parser")

        for img in soup.find_all("img"):
            # 处理 data-original
            data_original = img.get("data-original")
            if data_original:
                img["src"] = data_original

            # 处理 data-src
            data_src = img.get("data-src")
            if data_src and not img.get("src"):
                img["src"] = data_src

            # 处理 data-actualsrc（知乎特有）
            data_actual = img.get("data-actualsrc")
            if data_actual:
                img["src"] = data_actual

        return str(soup)
