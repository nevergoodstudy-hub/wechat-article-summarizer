"""Word 文档预览对话框

提供单篇和批量文章的 Word 导出预览功能。
"""

from __future__ import annotations

import re
import webbrowser
from tkinter import filedialog
from typing import TYPE_CHECKING

import customtkinter as ctk
from loguru import logger

if TYPE_CHECKING:
    from ....domain.entities import Article
    from ..app import WechatSummarizerGUI

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing


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
        result_parts = []
        img_counter = [0]

        def process_element(element, depth=0):
            from bs4 import NavigableString

            if isinstance(element, NavigableString):
                text = str(element).strip()
                if text and len(text) > 1:
                    result_parts.append(text)
                return None
            else:
                tag_name = getattr(element, "name", None)
                if not tag_name or tag_name in ["script", "style", "meta", "link", "noscript"]:
                    return None
                else:
                    if tag_name == "img":
                        img_counter[0] += 1
                        img_url = element.get("data-src") or element.get("src") or ""
                        if "emoji" not in img_url.lower() and "emotion" not in img_url.lower():
                            result_parts.append(f"\n\n[图片 {img_counter[0]}]\n\n")
                        return None
                    else:
                        if tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                            text = element.get_text(strip=True)
                            if text:
                                result_parts.append(f"\n\n【{text}】\n\n")
                            return None
                        else:
                            if tag_name == "p":
                                for img in element.find_all("img"):
                                    img_counter[0] += 1
                                    img_url = img.get("data-src") or img.get("src") or ""
                                    if (
                                        "emoji" not in img_url.lower()
                                        and "emotion" not in img_url.lower()
                                    ):
                                        result_parts.append(f"\n\n[图片 {img_counter[0]}]\n\n")
                                text = element.get_text(strip=True)
                                if text:
                                    result_parts.append(f"\n    {text}\n")
                                return None
                            else:
                                if tag_name in ["ul", "ol"]:
                                    for li in element.find_all("li", recursive=False):
                                        text = li.get_text(strip=True)
                                        if text:
                                            result_parts.append(f"\n  • {text}")
                                    result_parts.append("\n")
                                    return None
                                else:
                                    if tag_name == "blockquote":
                                        text = element.get_text(strip=True)
                                        if text:
                                            result_parts.append(f"\n    「{text}」\n")
                                        return None
                                    else:
                                        if tag_name == "table":
                                            result_parts.append(
                                                "\n\n┌────────── 表格 ──────────┐\n"
                                            )
                                            rows = element.find_all("tr")
                                            for row_idx, row in enumerate(rows):
                                                cells = row.find_all(["td", "th"])
                                                row_texts = []
                                                for cell in cells:
                                                    cell_text = cell.get_text(strip=True)
                                                    if len(cell_text) > 20:
                                                        cell_text = cell_text[:17] + "..."
                                                    row_texts.append(cell_text)
                                                if row_texts:
                                                    row_str = " │ ".join(row_texts)
                                                    result_parts.append(f"│ {row_str} │\n")
                                                    if row_idx == 0:
                                                        result_parts.append(
                                                            "├──────────────────────────────┤\n"
                                                        )
                                            result_parts.append(
                                                "└──────────────────────────────┘\n\n"
                                            )
                                        else:
                                            if hasattr(element, "children"):
                                                for child in element.children:
                                                    process_element(child, depth + 1)

        process_element(content_container)
        preview = "".join(result_parts)
        preview = re.sub("\\n{3,}", "\n\n", preview)
        if len(preview) > 3000:
            preview = preview[:3000] + "\n\n... (预览已截断，完整内容将包含在Word文档中) ..."
        return preview.strip()
    except Exception as e:
        logger.warning(f"构建内容预览失败: {e}")
        text = article.content_text
        if len(text) > 3000:
            text = text[:3000] + "\n\n... (预览已截断) ..."
        return text


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
    except Exception as e:
        logger.warning(f"提取图片失败: {e}")
    return images


def show_word_preview(gui: WechatSummarizerGUI) -> None:
    """Word预览 - 模拟最终Word文档布局"""
    if not gui.current_article:
        return None
    else:
        article = gui.current_article
        logger.info(f"打开Word预览: {article.title}")
        preview_window = ctk.CTkToplevel(gui.root)
        preview_window.title(f"Word文档预览 - {article.title[:30]}...")
        preview_window.geometry("800x750")
        preview_window.transient(gui.root)
        toolbar = ctk.CTkFrame(preview_window, height=40, fg_color="transparent")
        toolbar.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(
            toolbar, text="📄 Word文档预览", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        ctk.CTkLabel(
            toolbar,
            text="以下预览与最终生成的Word文档布局一致",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(side="right")
        doc_container = ctk.CTkFrame(
            preview_window,
            corner_radius=Spacing.RADIUS_SM,
            fg_color=(ModernColors.LIGHT_SURFACE_ALT, ModernColors.DARK_CARD_HOVER),
        )
        doc_container.pack(fill="both", expand=True, padx=15, pady=5)
        doc_scroll = ctk.CTkScrollableFrame(
            doc_container, fg_color=("white", "#1e1e1e"), corner_radius=0
        )
        doc_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(
            doc_scroll,
            text=article.title,
            font=ctk.CTkFont(size=20, weight="bold"),
            wraplength=650,
            justify="center",
        ).pack(pady=(20, 10))
        meta_items = []
        if article.account_name:
            meta_items.append(f"公众号: {article.account_name}")
        if article.author:
            meta_items.append(f"作者: {article.author}")
        if article.publish_time:
            meta_items.append(f"发布时间: {article.publish_time_str}")
        meta_items.append(f"字数: {article.word_count}")
        ctk.CTkLabel(
            doc_scroll, text=" | ".join(meta_items), font=ctk.CTkFont(size=10), text_color="gray"
        ).pack()
        ctk.CTkLabel(
            doc_scroll,
            text=f"原文链接: {article.url!s}",
            font=ctk.CTkFont(size=9),
            text_color=("#07C160", "#4CAF50"),
            cursor="hand2",
        ).pack(pady=(5, 10))
        ctk.CTkLabel(
            doc_scroll,
            text="────────────────────────────────────────────────────────────",
            text_color="gray",
        ).pack()
        if article.summary:
            ctk.CTkLabel(
                doc_scroll,
                text="📝 文章摘要",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=("#07C160", "#4CAF50"),
            ).pack(anchor="w", padx=20, pady=(15, 8))
            summary_frame = ctk.CTkFrame(
                doc_scroll, fg_color=("#f8f9fa", "#2a2a2a"), corner_radius=8
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
            if article.summary.key_points:
                ctk.CTkLabel(
                    doc_scroll, text="📌 关键要点", font=ctk.CTkFont(size=12, weight="bold")
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
            ctk.CTkLabel(
                doc_scroll,
                text="────────────────────────────────────────────────────────────",
                text_color="gray",
            ).pack(pady=10)
        ctk.CTkLabel(
            doc_scroll,
            text="📄 正文内容",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#07C160", "#4CAF50"),
        ).pack(anchor="w", padx=20, pady=(10, 8))
        content_preview = build_content_preview_with_images(article)
        content_label = ctk.CTkLabel(
            doc_scroll,
            text=content_preview,
            font=ctk.CTkFont(size=11),
            wraplength=650,
            justify="left",
            anchor="w",
        )
        content_label.pack(fill="x", padx=20, pady=5)
        images = extract_images_from_article(article)
        if images:
            img_info_frame = ctk.CTkFrame(
                doc_scroll, fg_color=("#e8f5e9", "#1b5e20"), corner_radius=8
            )
            img_info_frame.pack(fill="x", padx=20, pady=15)
            ctk.CTkLabel(
                img_info_frame, text=f"🖼️ 文档将包含 {len(images)} 张图片", font=ctk.CTkFont(size=11)
            ).pack(pady=8)
        ctk.CTkLabel(
            doc_scroll,
            text="────────────────────────────────────────────────────────────",
            text_color="gray",
        ).pack(pady=(20, 5))
        footer_text = (
            f"文章ID: {article.id} | 抓取时间: {article.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        ctk.CTkLabel(
            doc_scroll, text=footer_text, font=ctk.CTkFont(size=8), text_color="gray"
        ).pack()
        ctk.CTkLabel(
            doc_scroll,
            text="由 WeChat Article Summarizer 生成",
            font=ctk.CTkFont(size=8),
            text_color="gray",
        ).pack(pady=(0, 20))
        btn_frame = ctk.CTkFrame(preview_window, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=10)

        def do_export():
            preview_window.destroy()
            gui._do_export("word")

        ctk.CTkButton(
            btn_frame,
            text="🔗 查看原文",
            width=100,
            height=38,
            corner_radius=8,
            fg_color=ModernColors.NEUTRAL_BTN,
            command=lambda: webbrowser.open(str(article.url)),
        ).pack(side="left")
        ctk.CTkButton(
            btn_frame,
            text="取消",
            width=80,
            height=38,
            corner_radius=8,
            fg_color=ModernColors.NEUTRAL_BTN,
            command=preview_window.destroy,
        ).pack(side="right", padx=(5, 0))
        ctk.CTkButton(
            btn_frame,
            text="✓ 确认导出Word",
            width=150,
            height=38,
            corner_radius=8,
            fg_color=ModernColors.SUCCESS,
            command=do_export,
        ).pack(side="right")


def show_batch_word_preview(gui: WechatSummarizerGUI) -> None:
    """显示批量 Word 导出预览窗口（带翻页功能）- 与单篇预览样式一致"""
    if not gui.batch_results:
        return None
    else:
        preview_window = ctk.CTkToplevel(gui.root)
        preview_window.title(f"Word 导出预览 - 共 {len(gui.batch_results)} 篇文章")
        preview_window.geometry("800x750")
        preview_window.transient(gui.root)
        preview_window.update_idletasks()
        x = gui.root.winfo_rootx() + (gui.root.winfo_width() - 800) // 2
        y = gui.root.winfo_rooty() + (gui.root.winfo_height() - 750) // 2
        preview_window.geometry(f"+{x}+{y}")
        current_page = [0]
        total_pages = len(gui.batch_results)
        toolbar = ctk.CTkFrame(preview_window, height=40, fg_color="transparent")
        toolbar.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(
            toolbar, text="📄 Word文档预览", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        ctk.CTkLabel(
            toolbar,
            text="以下预览与最终生成的Word文档布局一致",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(side="right")
        nav_bar = ctk.CTkFrame(preview_window, height=40, fg_color="transparent")
        nav_bar.pack(fill="x", padx=15, pady=(0, 5))

        def go_next():
            if current_page[0] < total_pages - 1:
                current_page[0] += 1
                update_preview()

        def go_prev():
            if current_page[0] > 0:
                current_page[0] -= 1
                update_preview()

        prev_btn = ctk.CTkButton(
            nav_bar,
            text="◀ 上一篇",
            width=90,
            height=32,
            corner_radius=8,
            fg_color=ModernColors.NEUTRAL_BTN,
            command=go_prev,
        )
        prev_btn.pack(side="left", padx=2)
        page_frame = ctk.CTkFrame(nav_bar, fg_color="transparent")
        page_frame.pack(side="left", expand=True)
        page_label = ctk.CTkLabel(
            page_frame, text=f"第 1 篇 / 共 {total_pages} 篇", font=ctk.CTkFont(size=13)
        )
        page_label.pack()
        next_btn = ctk.CTkButton(
            nav_bar,
            text="下一篇 ▶",
            width=90,
            height=32,
            corner_radius=8,
            fg_color=ModernColors.NEUTRAL_BTN,
            command=go_next,
        )
        next_btn.pack(side="right", padx=2)
        doc_container = ctk.CTkFrame(
            preview_window,
            corner_radius=Spacing.RADIUS_SM,
            fg_color=(ModernColors.LIGHT_SURFACE_ALT, ModernColors.DARK_CARD_HOVER),
        )
        doc_container.pack(fill="both", expand=True, padx=15, pady=5)
        doc_scroll = ctk.CTkScrollableFrame(
            doc_container, fg_color=("white", "#1e1e1e"), corner_radius=0
        )
        doc_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        def update_preview():
            for widget in doc_scroll.winfo_children():
                widget.destroy()
            article = gui.batch_results[current_page[0]]
            page_label.configure(text=f"第 {current_page[0] + 1} 篇 / 共 {total_pages} 篇")
            prev_btn.configure(state="normal" if current_page[0] > 0 else "disabled")
            next_btn.configure(state="normal" if current_page[0] < total_pages - 1 else "disabled")
            ctk.CTkLabel(
                doc_scroll,
                text=article.title,
                font=ctk.CTkFont(size=20, weight="bold"),
                wraplength=650,
                justify="center",
            ).pack(pady=(20, 10))
            meta_items = []
            if article.account_name:
                meta_items.append(f"公众号: {article.account_name}")
            if article.author:
                meta_items.append(f"作者: {article.author}")
            if article.publish_time:
                meta_items.append(f"发布时间: {article.publish_time_str}")
            meta_items.append(f"字数: {article.word_count}")
            ctk.CTkLabel(
                doc_scroll,
                text=" | ".join(meta_items),
                font=ctk.CTkFont(size=10),
                text_color="gray",
            ).pack()
            link_label = ctk.CTkLabel(
                doc_scroll,
                text=f"原文链接: {article.url!s}",
                font=ctk.CTkFont(size=9),
                text_color=("#07C160", "#4CAF50"),
                cursor="hand2",
            )
            link_label.pack(pady=(5, 10))
            link_label.bind("<Button-1>", lambda e: webbrowser.open(str(article.url)))
            ctk.CTkLabel(
                doc_scroll,
                text="────────────────────────────────────────────────────────────",
                text_color="gray",
            ).pack()
            if article.summary:
                ctk.CTkLabel(
                    doc_scroll,
                    text="📝 文章摘要",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=("#07C160", "#4CAF50"),
                ).pack(anchor="w", padx=20, pady=(15, 8))
                summary_frame = ctk.CTkFrame(
                    doc_scroll, fg_color=("#f8f9fa", "#2a2a2a"), corner_radius=8
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
                if article.summary.key_points:
                    ctk.CTkLabel(
                        doc_scroll, text="📌 关键要点", font=ctk.CTkFont(size=12, weight="bold")
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
                ctk.CTkLabel(
                    doc_scroll,
                    text="────────────────────────────────────────────────────────────",
                    text_color="gray",
                ).pack(pady=10)
            ctk.CTkLabel(
                doc_scroll,
                text="📄 正文内容",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=("#07C160", "#4CAF50"),
            ).pack(anchor="w", padx=20, pady=(10, 8))
            content_preview = build_content_preview_with_images(article)
            content_label = ctk.CTkLabel(
                doc_scroll,
                text=content_preview,
                font=ctk.CTkFont(size=11),
                wraplength=650,
                justify="left",
                anchor="w",
            )
            content_label.pack(fill="x", padx=20, pady=5)
            images = extract_images_from_article(article)
            if images:
                img_info_frame = ctk.CTkFrame(
                    doc_scroll, fg_color=("#e8f5e9", "#1b5e20"), corner_radius=8
                )
                img_info_frame.pack(fill="x", padx=20, pady=15)
                ctk.CTkLabel(
                    img_info_frame,
                    text=f"🖼️ 文档将包含 {len(images)} 张图片",
                    font=ctk.CTkFont(size=11),
                ).pack(pady=8)
            ctk.CTkLabel(
                doc_scroll,
                text="────────────────────────────────────────────────────────────",
                text_color="gray",
            ).pack(pady=(20, 5))
            footer_text = f"文章 {current_page[0] + 1}/{total_pages} | ID: {article.id} | 抓取时间: {article.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            ctk.CTkLabel(
                doc_scroll, text=footer_text, font=ctk.CTkFont(size=8), text_color="gray"
            ).pack()
            ctk.CTkLabel(
                doc_scroll,
                text="由 WeChat Article Summarizer 生成",
                font=ctk.CTkFont(size=8),
                text_color="gray",
            ).pack(pady=(0, 20))

        update_preview()
        btn_frame = ctk.CTkFrame(preview_window, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=10)

        def open_current_url():
            article = gui.batch_results[current_page[0]]
            webbrowser.open(str(article.url))

        def do_export():
            dir_path = filedialog.askdirectory(title="选择输出目录")
            if dir_path:
                preview_window.destroy()
                gui._do_batch_export("word", dir_path)

        ctk.CTkButton(
            btn_frame,
            text="🔗 查看当前原文",
            width=120,
            height=38,
            corner_radius=8,
            fg_color=ModernColors.NEUTRAL_BTN,
            command=open_current_url,
        ).pack(side="left")
        ctk.CTkButton(
            btn_frame,
            text="取消",
            width=80,
            height=38,
            corner_radius=8,
            fg_color=ModernColors.NEUTRAL_BTN,
            command=preview_window.destroy,
        ).pack(side="right", padx=(5, 0))
        ctk.CTkButton(
            btn_frame,
            text=f"✓ 导出全部 {total_pages} 篇为 Word",
            width=200,
            height=38,
            corner_radius=8,
            fg_color=ModernColors.SUCCESS,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=do_export,
        ).pack(side="right")

        def on_key(event):
            if event.keysym == "Left":
                go_prev()
            else:
                if event.keysym == "Right":
                    go_next()

        preview_window.bind("<Left>", on_key)
        preview_window.bind("<Right>", on_key)
