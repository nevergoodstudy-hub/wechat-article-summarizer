"""Shared article rendering for Word preview dialogs."""

from __future__ import annotations

import webbrowser
from typing import TYPE_CHECKING

import customtkinter as ctk

from ..utils.i18n import tr
from .word_preview_content import build_content_preview_with_images, extract_images_from_article

if TYPE_CHECKING:
    from ....domain.entities import Article

SEPARATOR = "────────────────────────────────────────────────────────────"
ACCENT_COLOR = ("#07C160", "#4CAF50")


def render_article_document(
    doc_scroll: ctk.CTkScrollableFrame,
    article: Article,
    *,
    footer_text: str | None = None,
    bind_link: bool = False,
) -> None:
    """Render one article into the preview document surface."""
    _render_title(doc_scroll, article)
    _render_meta(doc_scroll, article)
    _render_link(doc_scroll, article, bind_link=bind_link)
    _render_separator(doc_scroll)
    _render_summary(doc_scroll, article)
    _render_body(doc_scroll, article)
    _render_footer(doc_scroll, article, footer_text=footer_text)


def _render_title(doc_scroll: ctk.CTkScrollableFrame, article: Article) -> None:
    ctk.CTkLabel(
        doc_scroll,
        text=article.title,
        font=ctk.CTkFont(size=20, weight="bold"),
        wraplength=650,
        justify="center",
    ).pack(pady=(20, 10))


def _render_meta(doc_scroll: ctk.CTkScrollableFrame, article: Article) -> None:
    meta_items = []
    if article.account_name:
        meta_items.append(tr("公众号: {account}").format(account=article.account_name))
    if article.author:
        meta_items.append(tr("作者: {author}").format(author=article.author))
    if article.publish_time:
        meta_items.append(
            tr("发布时间: {publish_time}").format(publish_time=article.publish_time_str)
        )
    meta_items.append(tr("字数: {word_count}").format(word_count=article.word_count))
    ctk.CTkLabel(
        doc_scroll,
        text=" | ".join(meta_items),
        font=ctk.CTkFont(size=10),
        text_color="gray",
    ).pack()


def _render_link(doc_scroll: ctk.CTkScrollableFrame, article: Article, *, bind_link: bool) -> None:
    link_label = ctk.CTkLabel(
        doc_scroll,
        text=tr("原文链接: {url}").format(url=article.url),
        font=ctk.CTkFont(size=9),
        text_color=ACCENT_COLOR,
        cursor="hand2",
    )
    link_label.pack(pady=(5, 10))
    if bind_link:
        link_label.bind("<Button-1>", lambda _event: webbrowser.open(str(article.url)))


def _render_summary(doc_scroll: ctk.CTkScrollableFrame, article: Article) -> None:
    if not article.summary:
        return

    ctk.CTkLabel(
        doc_scroll,
        text=tr("📝 文章摘要"),
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=ACCENT_COLOR,
    ).pack(anchor="w", padx=20, pady=(15, 8))
    summary_frame = ctk.CTkFrame(
        doc_scroll,
        fg_color=("#f8f9fa", "#2a2a2a"),
        corner_radius=8,
    )
    summary_frame.pack(fill="x", padx=20, pady=5)
    ctk.CTkLabel(
        summary_frame,
        text=article.summary.content,
        font=ctk.CTkFont(size=11),
        wraplength=620,
        justify="left",
        anchor="w",
    ).pack(fill="x", padx=15, pady=10)
    _render_key_points(doc_scroll, article)
    _render_separator(doc_scroll, pady=10)


def _render_key_points(doc_scroll: ctk.CTkScrollableFrame, article: Article) -> None:
    if not article.summary or not article.summary.key_points:
        return

    ctk.CTkLabel(
        doc_scroll,
        text=tr("📌 关键要点"),
        font=ctk.CTkFont(size=12, weight="bold"),
    ).pack(anchor="w", padx=20, pady=(15, 5))
    for point in article.summary.key_points:
        ctk.CTkLabel(
            doc_scroll,
            text=f"  • {point}",
            font=ctk.CTkFont(size=11),
            wraplength=620,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=25, pady=2)


def _render_body(doc_scroll: ctk.CTkScrollableFrame, article: Article) -> None:
    ctk.CTkLabel(
        doc_scroll,
        text=tr("📄 正文内容"),
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=ACCENT_COLOR,
    ).pack(anchor="w", padx=20, pady=(10, 8))
    ctk.CTkLabel(
        doc_scroll,
        text=build_content_preview_with_images(article),
        font=ctk.CTkFont(size=11),
        wraplength=650,
        justify="left",
        anchor="w",
    ).pack(fill="x", padx=20, pady=5)
    _render_image_notice(doc_scroll, article)


def _render_image_notice(doc_scroll: ctk.CTkScrollableFrame, article: Article) -> None:
    images = extract_images_from_article(article)
    if not images:
        return

    img_info_frame = ctk.CTkFrame(
        doc_scroll,
        fg_color=("#e8f5e9", "#1b5e20"),
        corner_radius=8,
    )
    img_info_frame.pack(fill="x", padx=20, pady=15)
    ctk.CTkLabel(
        img_info_frame,
        text=tr("🖼️ 文档将包含 {count} 张图片").format(count=len(images)),
        font=ctk.CTkFont(size=11),
    ).pack(pady=8)


def _render_footer(
    doc_scroll: ctk.CTkScrollableFrame,
    article: Article,
    *,
    footer_text: str | None,
) -> None:
    _render_separator(doc_scroll, pady=(20, 5))
    text = footer_text or (
        tr("文章ID: {article_id} | 抓取时间: {fetched_at}").format(
            article_id=article.id,
            fetched_at=article.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
    )
    ctk.CTkLabel(doc_scroll, text=text, font=ctk.CTkFont(size=8), text_color="gray").pack()
    ctk.CTkLabel(
        doc_scroll,
        text=tr("由 WeChat Article Summarizer 生成"),
        font=ctk.CTkFont(size=8),
        text_color="gray",
    ).pack(pady=(0, 20))


def _render_separator(doc_scroll: ctk.CTkScrollableFrame, pady: object | None = None) -> None:
    label = ctk.CTkLabel(doc_scroll, text=SEPARATOR, text_color="gray")
    if pady is None:
        label.pack()
    else:
        label.pack(pady=pady)


__all__ = ["render_article_document"]
