"""微信公众号Playwright抓取器 - 渲染模式"""

from __future__ import annotations

import random

from loguru import logger

from ....domain.entities import Article, ArticleSource
from ....domain.value_objects import ArticleContent, ArticleURL
from ....shared.constants import USER_AGENTS, WECHAT_CONTENT_SELECTORS
from ....shared.exceptions import ScraperError, ScraperTimeoutError
from .base import BaseScraper

# 延迟导入Playwright
_playwright_available = True
try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    from playwright.sync_api import sync_playwright
except ImportError:
    _playwright_available = False


class WechatPlaywrightScraper(BaseScraper):
    """
    微信公众号Playwright抓取器

    使用Playwright进行完整页面渲染，适用于需要JavaScript执行的页面。
    """

    def __init__(
        self,
        timeout: int = 30,
        headless: bool = True,
    ):
        if not _playwright_available:
            raise ImportError(
                "Playwright未安装，请运行: pip install playwright && playwright install chromium"
            )

        self._timeout = timeout * 1000  # 转换为毫秒
        self._headless = headless

    @property
    def name(self) -> str:
        return "wechat_playwright"

    def can_handle(self, url: ArticleURL) -> bool:
        """只处理微信公众号链接"""
        return url.is_wechat

    def scrape(self, url: ArticleURL) -> Article:
        """使用Playwright抓取微信公众号文章"""
        logger.debug(f"使用Playwright抓取: {url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self._headless)

            try:
                context = browser.new_context(
                    user_agent=random.choice(USER_AGENTS),
                    viewport={"width": 1280, "height": 800},
                    locale="zh-CN",
                )

                page = context.new_page()

                # 添加反检测脚本
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                """)

                try:
                    page.goto(str(url), timeout=self._timeout)
                    # 等待内容加载
                    page.wait_for_selector("#js_content", timeout=self._timeout)
                except PlaywrightTimeout:
                    raise ScraperTimeoutError("页面加载超时")

                # 执行JavaScript移除隐藏样式
                page.evaluate("""
                    document.querySelectorAll('[style*="visibility"]').forEach(el => {
                        el.style.visibility = 'visible';
                        el.style.opacity = '1';
                    });
                """)

                # 处理懒加载图片
                page.evaluate("""
                    document.querySelectorAll('img[data-src]').forEach(img => {
                        if (img.dataset.src && !img.src) {
                            img.src = img.dataset.src;
                        }
                    });
                """)

                # 等待图片加载
                page.wait_for_timeout(1000)

                # 获取页面内容
                html = page.content()

                return self._parse_with_page(page, url, html)

            finally:
                browser.close()

    def _parse_with_page(self, page, url: ArticleURL, html: str) -> Article:
        """使用Playwright页面解析内容"""
        # 提取标题
        title = page.title() or "无标题"
        title_elem = page.query_selector("h1.rich_media_title, #activity-name")
        if title_elem:
            title = title_elem.inner_text().strip()

        # 提取公众号名称
        account_name = None
        name_elem = page.query_selector("#js_name")
        if name_elem:
            account_name = name_elem.inner_text().strip()

        # 提取内容
        content_html = ""
        for selector in WECHAT_CONTENT_SELECTORS:
            elem = page.query_selector(selector)
            if elem:
                content_html = elem.inner_html()
                break

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
            account_name=account_name,
            content=content,
            source=source,
        )
