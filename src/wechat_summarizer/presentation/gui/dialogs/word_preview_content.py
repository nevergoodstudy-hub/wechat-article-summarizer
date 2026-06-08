"""Content helpers for Word preview dialogs."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from ....domain.entities import Article

SKIPPED_TAGS = {"script", "style", "meta", "link", "noscript"}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


def build_content_preview_with_images(article: Article) -> str:
    """构建带图片位置标记的内容预览"""
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(article.content_html, "html.parser")
        content_container = (
            soup.find(id="js_content")
            or soup.find(class_="rich_media_content")
            or soup.body
            or soup
        )
        result_parts: list[str] = []
        img_counter = [0]
        _append_element_preview(content_container, result_parts, img_counter)
        preview = "".join(result_parts)
        preview = re.sub("\\n{3,}", "\n\n", preview)
        if len(preview) > 3000:
            preview = preview[:3000] + "\n\n... (预览已截断，完整内容将包含在Word文档中) ..."
        return preview.strip()
    except Exception as exc:
        logger.warning(f"构建内容预览失败: {exc}")
        text = article.content_text
        if len(text) > 3000:
            text = text[:3000] + "\n\n... (预览已截断) ..."
        return text


def _append_element_preview(element: Any, result_parts: list[str], img_counter: list[int]) -> None:
    from bs4 import NavigableString

    if isinstance(element, NavigableString):
        text = str(element).strip()
        if text and len(text) > 1:
            result_parts.append(text)
        return

    tag_name = getattr(element, "name", None)
    if not tag_name or tag_name in SKIPPED_TAGS:
        return
    if tag_name == "img":
        _append_image_marker(element, result_parts, img_counter)
        return
    if tag_name in HEADING_TAGS:
        _append_heading(element, result_parts)
        return
    if tag_name == "p":
        _append_paragraph(element, result_parts, img_counter)
        return
    if tag_name in ["ul", "ol"]:
        _append_list(element, result_parts)
        return
    if tag_name == "blockquote":
        _append_quote(element, result_parts)
        return
    if tag_name == "table":
        _append_table(element, result_parts)
        return

    if hasattr(element, "children"):
        for child in element.children:
            _append_element_preview(child, result_parts, img_counter)


def _append_image_marker(element: Any, result_parts: list[str], img_counter: list[int]) -> None:
    img_counter[0] += 1
    img_url = element.get("data-src") or element.get("src") or ""
    if "emoji" not in img_url.lower() and "emotion" not in img_url.lower():
        result_parts.append(f"\n\n[图片 {img_counter[0]}]\n\n")


def _append_heading(element: Any, result_parts: list[str]) -> None:
    text = element.get_text(strip=True)
    if text:
        result_parts.append(f"\n\n【{text}】\n\n")


def _append_paragraph(element: Any, result_parts: list[str], img_counter: list[int]) -> None:
    for img in element.find_all("img"):
        _append_image_marker(img, result_parts, img_counter)
    text = element.get_text(strip=True)
    if text:
        result_parts.append(f"\n    {text}\n")


def _append_list(element: Any, result_parts: list[str]) -> None:
    for li in element.find_all("li", recursive=False):
        text = li.get_text(strip=True)
        if text:
            result_parts.append(f"\n  • {text}")
    result_parts.append("\n")


def _append_quote(element: Any, result_parts: list[str]) -> None:
    text = element.get_text(strip=True)
    if text:
        result_parts.append(f"\n    「{text}」\n")


def _append_table(element: Any, result_parts: list[str]) -> None:
    result_parts.append("\n\n┌────────── 表格 ──────────┐\n")
    rows = element.find_all("tr")
    for row_idx, row in enumerate(rows):
        row_texts = [
            _truncate_cell_text(cell.get_text(strip=True)) for cell in row.find_all(["td", "th"])
        ]
        if row_texts:
            row_str = " │ ".join(row_texts)
            result_parts.append(f"│ {row_str} │\n")
            if row_idx == 0:
                result_parts.append("├──────────────────────────────┤\n")
    result_parts.append("└──────────────────────────────┘\n\n")


def _truncate_cell_text(cell_text: str) -> str:
    if len(cell_text) > 20:
        return cell_text[:17] + "..."
    return cell_text


def extract_images_from_article(article: Article) -> list[str]:
    """提取文章中的图片 URL"""
    images = []
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(article.content_html, "html.parser")
        for img in soup.find_all("img"):
            img_url = img.get("data-src") or img.get("src")
            if isinstance(img_url, str) and img_url.startswith("http"):
                images.append(img_url)
    except Exception as exc:
        logger.warning(f"提取图片失败: {exc}")
    return images


__all__ = [
    "build_content_preview_with_images",
    "extract_images_from_article",
]
