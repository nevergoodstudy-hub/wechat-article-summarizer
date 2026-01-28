"""Notion 导出器

最小实现：在指定 Notion Database 中创建页面，并写入摘要/链接等关键信息。

注意：Notion 的 Block 结构较复杂，这里先以“可用且稳定”为目标，避免把整篇正文转换成大量块。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx
from loguru import logger

from ....domain.entities import Article
from ....shared.exceptions import ExporterAuthError, ExporterError
from ....shared.utils import truncate_text
from .base import BaseExporter


@dataclass(frozen=True)
class NotionConfig:
    api_key: str
    database_id: str
    notion_version: str = "2022-06-28"
    title_property: str = "Name"  # 大多数数据库默认标题字段名


NOTION_VERSION_MULTI_SOURCE = "2025-09-03"  # Notion 数据源（data_source）版本


class NotionExporter(BaseExporter):
    """Notion 导出器"""

    def __init__(
        self,
        api_key: str,
        database_id: str,
        notion_version: str = "2022-06-28",
        title_property: str = "Name",
        timeout: int = 20,
    ):
        self._cfg = NotionConfig(
            api_key=api_key,
            database_id=database_id,
            notion_version=notion_version,
            title_property=title_property,
        )
        self._timeout = timeout
        self._resolved_title_property: str | None = None

    @property
    def name(self) -> str:
        return "notion"

    @property
    def target(self) -> str:
        return "notion"

    def is_available(self) -> bool:
        return bool(self._cfg.api_key and self._cfg.database_id)

    def export(self, article: Article, path: str | None = None, **options) -> str:
        if not self.is_available():
            raise ExporterError(
                "Notion 未配置（export.notion_api_key / export.notion_database_id）"
            )

        # 可选参数
        title_property_opt = options.get("title_property")
        title_property = (
            str(title_property_opt).strip()
            if title_property_opt
            else (
                self._resolved_title_property
                or self._discover_title_property(database_id=self._cfg.database_id)
            )
        )
        include_content = bool(options.get("include_content", False))
        max_content_chars = int(options.get("max_content_chars", 4000))

        title = article.title or "Untitled"

        children = []
        children.extend(self._blocks_for_link(article))

        if article.summary:
            children.extend(self._blocks_for_summary(article))

        if include_content:
            children.extend(self._blocks_for_content(article, max_chars=max_content_chars))

        payload_base = {
            "properties": {
                title_property: {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": truncate_text(title, max_length=1800)},
                        }
                    ]
                }
            },
            "children": children,
        }

        # 1) 优先按 database_id 父级创建（兼容旧版本）
        parent_db = {"type": "database_id", "database_id": self._cfg.database_id}
        resp = self._post_page(
            parent=parent_db, notion_version=self._cfg.notion_version, payload_base=payload_base
        )

        # 2) 处理 2025-09-03 多数据源数据库：需要 data_source_id
        if resp.status_code >= 400 and self._looks_like_multi_source_error(resp.text):
            ds_id = self._discover_data_source_id(database_id=self._cfg.database_id)
            parent_ds = {"type": "data_source_id", "data_source_id": ds_id}
            resp = self._post_page(
                parent=parent_ds,
                notion_version=NOTION_VERSION_MULTI_SOURCE,
                payload_base=payload_base,
            )

        # 3) 如果用户提供的其实是 data_source_id（误填到 database_id），尝试兜底
        if resp.status_code == 404:
            parent_ds = {"type": "data_source_id", "data_source_id": self._cfg.database_id}
            resp = self._post_page(
                parent=parent_ds,
                notion_version=NOTION_VERSION_MULTI_SOURCE,
                payload_base=payload_base,
            )

        if resp.status_code in (401, 403):
            raise ExporterAuthError(f"Notion 鉴权失败 (HTTP {resp.status_code})")

        if resp.status_code >= 400:
            raise ExporterError(f"Notion 导出失败 (HTTP {resp.status_code}): {resp.text}")

        data = resp.json()
        url = data.get("url") or data.get("id") or ""
        logger.info(f"Notion导出成功: {url}")
        return url

    def _post_page(self, parent: dict, notion_version: str, payload_base: dict) -> httpx.Response:
        payload = {"parent": parent, **payload_base}

        headers = {
            "Authorization": f"Bearer {self._cfg.api_key}",
            "Notion-Version": notion_version,
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                return client.post("https://api.notion.com/v1/pages", headers=headers, json=payload)
        except Exception as e:
            raise ExporterError(f"Notion API 请求失败: {e}") from e

    def _discover_title_property(self, database_id: str) -> str:
        """自动发现数据库的 title 属性名。

        Notion 数据库的“标题列”名称不一定是 Name。
        如果发现失败，则回退到默认值（cfg.title_property）。
        """
        for ver in (self._cfg.notion_version, NOTION_VERSION_MULTI_SOURCE):
            headers = {
                "Authorization": f"Bearer {self._cfg.api_key}",
                "Notion-Version": ver,
            }

            try:
                with httpx.Client(timeout=self._timeout) as client:
                    resp = client.get(
                        f"https://api.notion.com/v1/databases/{database_id}", headers=headers
                    )
            except Exception:
                continue

            if resp.status_code >= 400:
                continue

            data = resp.json()
            if not isinstance(data, dict):
                continue

            props = data.get("properties")
            if not isinstance(props, dict):
                continue

            for name, meta in props.items():
                if isinstance(meta, dict) and meta.get("type") == "title":
                    resolved = str(name)
                    self._resolved_title_property = resolved
                    return resolved

        # fallback
        return self._cfg.title_property

    def _discover_data_source_id(self, database_id: str) -> str:
        """在 2025-09-03 版本下获取 database 的 data_sources[0].id。"""
        headers = {
            "Authorization": f"Bearer {self._cfg.api_key}",
            "Notion-Version": NOTION_VERSION_MULTI_SOURCE,
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.get(
                    f"https://api.notion.com/v1/databases/{database_id}", headers=headers
                )
        except Exception as e:
            raise ExporterError(f"Notion discovery 请求失败: {e}") from e

        if resp.status_code in (401, 403):
            raise ExporterAuthError(f"Notion discovery 鉴权失败 (HTTP {resp.status_code})")
        if resp.status_code >= 400:
            raise ExporterError(f"Notion discovery 失败 (HTTP {resp.status_code}): {resp.text}")

        data = resp.json()
        if not isinstance(data, dict):
            raise ExporterError("Notion discovery 响应不是 JSON object")

        sources = data.get("data_sources") or []
        if not isinstance(sources, list) or not sources:
            raise ExporterError(
                "Notion 数据库未返回 data_sources；请确认 Notion-Version 是否为 2025-09-03"
            )

        first = sources[0]
        ds_id = first.get("id") if isinstance(first, dict) else None
        if not ds_id:
            raise ExporterError("Notion data_sources[0].id 为空")
        return str(ds_id)

    @staticmethod
    def _looks_like_multi_source_error(message: str) -> bool:
        msg = message.lower()
        return (
            "data_source_id" in msg
            or ("data_source" in msg and "database" in msg)
            or ("multi-source" in msg)
        )

    # ---------------- blocks helpers ----------------

    @staticmethod
    def _rt(text: str, link: str | None = None) -> list[dict]:
        item: dict = {"type": "text", "text": {"content": text}}
        if link:
            item["text"]["link"] = {"url": link}
        return [item]

    def _blocks_for_link(self, article: Article) -> list[dict]:
        return [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": self._rt("🔗 原文链接")},
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": self._rt(str(article.url), link=str(article.url))},
            },
        ]

    def _blocks_for_summary(self, article: Article) -> list[dict]:
        summary = article.summary
        if summary is None:
            return []

        blocks: list[dict] = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": self._rt("📝 摘要")},
            },
        ]

        blocks.extend(self._paragraph_blocks(summary.content))

        if summary.key_points:
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": self._rt("📌 关键要点")},
                }
            )
            for p in summary.key_points[:10]:
                blocks.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": self._rt(truncate_text(str(p), 1800))},
                    }
                )

        if summary.tags:
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": self._rt("🏷️ 标签")},
                }
            )
            tags_text = " ".join(f"#{t}" for t in summary.tags[:20])
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": self._rt(truncate_text(tags_text, 1800))},
                }
            )

        return blocks

    def _blocks_for_content(self, article: Article, max_chars: int) -> list[dict]:
        text = article.content_text
        if not text:
            return []

        blocks: list[dict] = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": self._rt("📄 正文（节选）")},
            }
        ]

        # Notion 对单个 rich_text 长度有限，按段落切块
        excerpt = text[:max_chars]
        blocks.extend(self._paragraph_blocks(excerpt))
        return blocks

    def _paragraph_blocks(self, text: str) -> list[dict]:
        # 将内容按空行/换行拆分，并对每段做长度限制
        # Notion 单段过长容易报错，因此这里做 conservative 的 chunk。
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
        blocks: list[dict] = []
        for p in paragraphs:
            for piece in self._split_long_text(p, max_len=1800):
                blocks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {"rich_text": self._rt(piece)},
                    }
                )
        return blocks

    @staticmethod
    def _split_long_text(text: str, max_len: int = 1800) -> list[str]:
        if len(text) <= max_len:
            return [text]

        parts: list[str] = []
        start = 0
        while start < len(text):
            end = min(len(text), start + max_len)
            parts.append(text[start:end])
            start = end
        return parts
