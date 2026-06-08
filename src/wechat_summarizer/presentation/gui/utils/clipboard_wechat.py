"""WeChat article link extraction and normalization."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qs, urlencode, urlparse

from loguru import logger

from .clipboard_models import MAX_TEXT_LENGTH, MAX_URL_LENGTH, MAX_URLS


class WeChatLinkDetector:
    """微信公众号链接检测器"""

    WECHAT_PATTERNS = [
        r'https?://mp\.weixin\.qq\.com/s\?[^\s\n\r<>"\'、。，！]+',
        r"https?://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+",
        r'https?://mp\.weixin\.qq\.com/s/[^\s\n\r<>"\']+__biz=[^\s\n\r<>"\']+',
        r'https?://mp\.weixin\.qq\.com/mp/appmsg/show\?[^\s\n\r<>"\']+',
    ]
    ALLOWED_DOMAINS = [
        "mp.weixin.qq.com",
        "weixin.qq.com",
    ]
    DANGEROUS_PATTERNS = [
        r"<script",
        r"javascript:",
        r"data:",
        r"vbscript:",
        r"on\w+\s*=",
    ]

    @classmethod
    def extract_links(cls, text: str, smart_dedup: bool = True) -> tuple[list[str], int, int]:
        """从文本中提取微信公众号链接"""
        if not text:
            return [], 0, 0

        if len(text) > MAX_TEXT_LENGTH:
            logger.warning(f"文本过长({len(text)}字符)，截断至{MAX_TEXT_LENGTH}")
            text = text[:MAX_TEXT_LENGTH]

        logger.debug(f"检测文本长度: {len(text)} 字符")
        raw_links: list[str] = []
        for pattern in cls.WECHAT_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            logger.debug(f"模式匹配到 {len(matches)} 个")
            raw_links.extend(matches)

        cleaned_links: list[str] = []
        invalid_count = 0

        for link in raw_links:
            cleaned = cls._clean_url(link)
            if cleaned and cls.is_valid_wechat_link(cleaned):
                if cls._is_safe_url(cleaned):
                    cleaned_links.append(cleaned)
                else:
                    invalid_count += 1
                    logger.warning(f"检测到不安全URL: {cleaned[:50]}...")
            else:
                invalid_count += 1

        if smart_dedup:
            unique_links, dup_count = cls._smart_deduplicate(cleaned_links)
        else:
            unique_links, dup_count = cls._simple_deduplicate(cleaned_links)

        if len(unique_links) > MAX_URLS:
            logger.warning(f"URL数量超限({len(unique_links)})，截断至{MAX_URLS}")
            unique_links = unique_links[:MAX_URLS]

        logger.debug(f"最终提取到 {len(unique_links)} 个唯一链接")
        return unique_links, dup_count, invalid_count

    @classmethod
    def _clean_url(cls, url: str) -> str | None:
        """清理URL"""
        if not url:
            return None

        url = url.strip()
        url = url.rstrip(".,;:!?\"'\\)>、。，！？】」』")
        url = url.replace("&amp;", "&")
        url = url.replace("&lt;", "<")
        url = url.replace("&gt;", ">")
        url = url.replace("&quot;", '"')

        if len(url) > MAX_URL_LENGTH:
            return None

        return url

    @classmethod
    def _is_safe_url(cls, url: str) -> bool:
        """检查URL是否安全"""
        url_lower = url.lower()
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, url_lower):
                return False

        try:
            parsed = urlparse(url)
            if parsed.netloc not in cls.ALLOWED_DOMAINS:
                return False
        except Exception:
            return False

        return True

    @classmethod
    def _smart_deduplicate(cls, links: list[str]) -> tuple[list[str], int]:
        """智能去重 - 基于文章核心参数"""
        seen_ids: set[str] = set()
        unique_links: list[str] = []
        dup_count = 0

        for link in links:
            article_id = cls._extract_article_id(link)
            if article_id not in seen_ids:
                seen_ids.add(article_id)
                unique_links.append(link)
            else:
                dup_count += 1

        return unique_links, dup_count

    @classmethod
    def _simple_deduplicate(cls, links: list[str]) -> tuple[list[str], int]:
        """简单去重 - 基于完整URL"""
        seen: set[str] = set()
        unique_links: list[str] = []
        dup_count = 0

        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
            else:
                dup_count += 1

        return unique_links, dup_count

    @classmethod
    def _extract_article_id(cls, url: str) -> str:
        """提取文章唯一标识"""
        try:
            parsed = urlparse(url)

            if "/s/" in parsed.path:
                path_parts = parsed.path.split("/s/")
                if len(path_parts) > 1:
                    short_id = path_parts[1].split("?")[0].split("#")[0]
                    if short_id and len(short_id) > 5:
                        return f"short:{short_id}"

            params = parse_qs(parsed.query)
            biz = params.get("__biz", [""])[0]
            mid = params.get("mid", params.get("appmsgid", [""]))[0]
            idx = params.get("idx", params.get("itemidx", ["1"]))[0]
            sn = params.get("sn", [""])[0]

            if biz and mid:
                return f"biz:{biz}:mid:{mid}:idx:{idx}"
            if sn:
                return f"sn:{sn}"

        except Exception as exc:
            logger.debug(f"解析URL失败: {exc}")

        return f"hash:{hashlib.md5(url.encode(), usedforsecurity=False).hexdigest()[:16]}"

    @classmethod
    def is_valid_wechat_link(cls, url: str) -> bool:
        """验证是否为有效的微信公众号链接"""
        if not url:
            return False

        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False
            if parsed.netloc not in cls.ALLOWED_DOMAINS:
                return False

            valid_paths = ["/s", "/s/", "/mp/appmsg"]
            return any(parsed.path.startswith(path) for path in valid_paths)

        except Exception:
            return False

    @classmethod
    def normalize_url(cls, url: str) -> str:
        """标准化URL - 移除追踪参数，保留核心参数"""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            core_params = ["__biz", "mid", "idx", "sn", "chksm"]
            filtered = {
                key: value[0] for key, value in params.items() if key in core_params and value
            }

            if filtered:
                new_query = urlencode(filtered)
                return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"

            return url

        except Exception:
            return url


__all__ = ["WeChatLinkDetector"]
