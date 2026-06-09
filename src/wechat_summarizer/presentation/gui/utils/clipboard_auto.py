"""High-level automatic WeChat link detection."""

from __future__ import annotations

from loguru import logger

from .clipboard_browser import BrowserDetector
from .clipboard_manager import ClipboardManager
from .clipboard_models import DetectionResult
from .clipboard_wechat import WeChatLinkDetector
from .i18n import tr


class AutoLinkDetector:
    """自动链接检测器 - 整合剪贴板和浏览器检测"""

    @staticmethod
    def detect(smart_dedup: bool = True) -> DetectionResult:
        """执行自动检测"""
        clipboard_content = ClipboardManager.get_clipboard_content()
        if clipboard_content:
            links, dup_count, invalid_count = WeChatLinkDetector.extract_links(
                clipboard_content,
                smart_dedup=smart_dedup,
            )
            if links:
                logger.info(f"从剪贴板检测到 {len(links)} 个微信链接")
                msg_parts = [tr("从剪贴板检测到 {count} 个微信公众号链接").format(count=len(links))]
                if dup_count > 0:
                    msg_parts.append(tr("(去除 {count} 个重复)").format(count=dup_count))
                if invalid_count > 0:
                    msg_parts.append(tr("(过滤 {count} 个无效)").format(count=invalid_count))

                return DetectionResult(
                    links=links,
                    source="clipboard",
                    message=" ".join(msg_parts),
                    duplicates_removed=dup_count,
                    invalid_removed=invalid_count,
                )

        if BrowserDetector.check_wechat_browser_activity():
            logger.info("检测到微信公众号浏览器活动")
            return DetectionResult(
                links=[],
                source="browser",
                message=tr("检测到您正在浏览微信公众号页面\n请复制链接后重试"),
            )

        return DetectionResult(links=[], source="none", message="")

    @staticmethod
    def detect_from_text(text: str, smart_dedup: bool = True) -> DetectionResult:
        """从指定文本检测链接"""
        if not text:
            return DetectionResult(links=[], source="text", message=tr("输入文本为空"))

        links, dup_count, invalid_count = WeChatLinkDetector.extract_links(
            text,
            smart_dedup=smart_dedup,
        )

        if links:
            msg_parts = [tr("检测到 {count} 个微信公众号链接").format(count=len(links))]
            if dup_count > 0:
                msg_parts.append(tr("(去除 {count} 个重复)").format(count=dup_count))
            if invalid_count > 0:
                msg_parts.append(tr("(过滤 {count} 个无效)").format(count=invalid_count))

            return DetectionResult(
                links=links,
                source="text",
                message=" ".join(msg_parts),
                duplicates_removed=dup_count,
                invalid_removed=invalid_count,
            )

        return DetectionResult(links=[], source="text", message=tr("未检测到有效的微信公众号链接"))

    @staticmethod
    def batch_detect(texts: list[str]) -> DetectionResult:
        """批量检测多个文本"""
        all_links: list[str] = []
        total_dups = 0
        total_invalid = 0

        for text in texts:
            if text:
                links, dups, invalid = WeChatLinkDetector.extract_links(text)
                all_links.extend(links)
                total_dups += dups
                total_invalid += invalid

        unique_links, final_dups = WeChatLinkDetector._smart_deduplicate(all_links)
        total_dups += final_dups

        if unique_links:
            msg_parts = [tr("批量检测到 {count} 个微信公众号链接").format(count=len(unique_links))]
            if total_dups > 0:
                msg_parts.append(tr("(去除 {count} 个重复)").format(count=total_dups))

            return DetectionResult(
                links=unique_links,
                source="batch",
                message=" ".join(msg_parts),
                duplicates_removed=total_dups,
                invalid_removed=total_invalid,
            )

        return DetectionResult(links=[], source="batch", message=tr("批量检测未发现有效链接"))


__all__ = ["AutoLinkDetector"]
