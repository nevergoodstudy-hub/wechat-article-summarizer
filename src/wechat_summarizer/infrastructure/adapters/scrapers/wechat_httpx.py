"""微信公众号HTTPX抓取器 - 快速模式"""

import random
import re
from datetime import datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from ....domain.entities import Article, ArticleSource
from ....domain.value_objects import ArticleContent, ArticleURL
from ....shared.constants import USER_AGENTS, WECHAT_CONTENT_SELECTORS
from ....shared.exceptions import ScraperBlockedError, ScraperError, ScraperTimeoutError
from ....shared.utils import retry
from .base import BaseScraper


class WechatHttpxScraper(BaseScraper):
    """
    微信公众号HTTPX抓取器

    使用HTTPX进行快速HTTP请求，适用于大部分微信文章。

    设计要点：
    - 仅对“网络层异常”（连接/超时等）进行重试
    - HTTP 状态码错误（如 404/403）不盲目重试，便于快速失败与定位
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

        # 基于实例参数创建“可配置”的重试包装（解决装饰器无法使用 self._max_retries 的问题）
        self._get_with_retry = retry(
            max_attempts=max_retries,
            exceptions=(httpx.TimeoutException, httpx.TransportError),
            delay=1.0,
            backoff=2.0,
            jitter=True,
        )(self._get)

    @property
    def name(self) -> str:
        return "wechat_httpx"

    def can_handle(self, url: ArticleURL) -> bool:
        """只处理微信公众号链接"""
        return url.is_wechat

    def scrape(self, url: ArticleURL) -> Article:
        """抓取微信公众号文章"""
        logger.debug(f"开始抓取: {url}")

        headers = {
            "User-Agent": self._choose_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        try:
            response = self._get_with_retry(str(url), headers=headers)
        except httpx.TimeoutException as e:
            raise ScraperTimeoutError(f"请求超时: {e}") from e
        except httpx.TransportError as e:
            raise ScraperError(f"网络错误: {e}") from e

        # 仅在请求成功后再做状态码检查（避免把 4xx/5xx 当成“网络异常”参与重试）
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            # 常见反爬/限流：401/403/429
            if status in (401, 403, 429):
                raise ScraperBlockedError(f"请求被拒绝/限流 (HTTP {status})") from e
            raise ScraperError(f"HTTP错误 (HTTP {status})") from e

        # 解析HTML
        return self._parse_html(response.text, url)

    def _choose_user_agent(self) -> str:
        if self._user_agent_rotation:
            return random.choice(USER_AGENTS)
        return USER_AGENTS[0]

    def _get(self, url: str, headers: dict[str, str]) -> httpx.Response:
        with httpx.Client(
            timeout=self._timeout,
            follow_redirects=True,
            proxy=self._proxy,
        ) as client:
            return client.get(url, headers=headers)

    def _parse_html(self, html: str, url: ArticleURL) -> Article:
        """解析HTML内容"""
        soup = BeautifulSoup(html, "html.parser")

        # 提取标题
        title = self._extract_title(soup)

        # 提取作者/公众号名称
        author, account_name = self._extract_author(soup)

        # 提取发布时间
        publish_time = self._extract_publish_time(soup, html)

        # 提取正文内容
        content_html = self._extract_content(soup)
        if not content_html:
            raise ScraperError("无法提取文章内容")

        # 创建内容对象
        content = ArticleContent.from_html(content_html)

        # 创建来源
        source = ArticleSource.wechat(
            account_name=account_name or "未知",
        )

        return Article(
            url=url,
            title=title,
            author=author,
            account_name=account_name,
            publish_time=publish_time,
            content=content,
            source=source,
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        # 尝试多种方式
        # bs4 stubs 对 attrs 的 value 类型要求较宽（str/bytes/Pattern/...），
        # 这里用 Any 简化静态类型兼容。
        selectors: list[tuple[str, dict[str, Any] | None]] = [
            ("h1", {"class": "rich_media_title"}),
            ("h1", {"id": "activity-name"}),
            ("meta", {"property": "og:title"}),
            ("title", None),
        ]

        for tag, attrs in selectors:
            elem = soup.find(tag, attrs=attrs) if attrs is not None else soup.find(tag)
            if elem:
                if tag == "meta":
                    content_val = elem.get("content")
                    if isinstance(content_val, list):
                        content_val = content_val[0] if content_val else ""
                    return str(content_val or "").strip()
                return elem.get_text(strip=True)

        return "无标题"

    def _extract_author(self, soup: BeautifulSoup) -> tuple[str | None, str | None]:
        """提取作者和公众号名称"""
        author = None
        account_name = None

        # 公众号名称
        name_elem = soup.find("a", {"id": "js_name"}) or soup.find(
            "span", {"class": "rich_media_meta_nickname"}
        )
        if name_elem:
            account_name = name_elem.get_text(strip=True)

        # 作者
        author_elem = soup.find("span", {"class": "rich_media_meta_text"})
        if author_elem:
            author = author_elem.get_text(strip=True)

        return author, account_name

    def _extract_publish_time(self, soup: BeautifulSoup, html: str) -> datetime | None:
        """提取发布时间"""
        # 方式1: 从script中提取
        patterns = [
            r'var createTime = "(\d{4}-\d{2}-\d{2})"',
            r'"create_time":\s*"(\d{4}-\d{2}-\d{2})"',
            r'publish_time\s*=\s*"(\d{4}-\d{2}-\d{2})"',
        ]

        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                try:
                    return datetime.strptime(match.group(1), "%Y-%m-%d")
                except ValueError:
                    pass

        # 方式2: 从元素中提取
        time_elem = soup.find("em", {"id": "publish_time"})
        if time_elem:
            time_text = time_elem.get_text(strip=True)
            try:
                return datetime.strptime(time_text, "%Y-%m-%d")
            except ValueError:
                pass

        return None

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文内容"""
        # 尝试多个选择器
        for selector in WECHAT_CONTENT_SELECTORS:
            if selector.startswith("#"):
                elem = soup.find(id=selector[1:])
            elif selector.startswith("."):
                elem = soup.find(class_=selector[1:])
            else:
                elem = soup.select_one(selector)

            if elem:
                return str(elem)

        return ""

    async def scrape_async(self, url: ArticleURL) -> Article:
        """异步抓取微信公众号文章"""
        logger.debug(f"开始异步抓取: {url}")

        headers = {
            "User-Agent": self._choose_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                proxy=self._proxy,
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
                raise ScraperBlockedError(f"请求被拒绝/限流 (HTTP {status})") from e
            raise ScraperError(f"HTTP错误 (HTTP {status})") from e

        return self._parse_html(response.text, url)
