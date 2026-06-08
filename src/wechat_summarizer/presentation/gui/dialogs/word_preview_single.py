"""Single-article Word preview dialog."""

from __future__ import annotations

import webbrowser
from typing import TYPE_CHECKING

import customtkinter as ctk
from loguru import logger

from ..styles.colors import ModernColors
from .word_preview_render import render_article_document
from .word_preview_window import add_preview_toolbar, create_document_scroll, create_preview_window

if TYPE_CHECKING:
    from ..app import WechatSummarizerGUI


def show_word_preview(gui: WechatSummarizerGUI) -> None:
    """Word预览 - 模拟最终Word文档布局"""
    if not gui.current_article:
        return

    article = gui.current_article
    logger.info(f"打开Word预览: {article.title}")
    preview_window = create_preview_window(gui.root, f"Word文档预览 - {article.title[:30]}...")
    add_preview_toolbar(preview_window)
    doc_scroll = create_document_scroll(preview_window)
    render_article_document(doc_scroll, article)

    btn_frame = ctk.CTkFrame(preview_window, fg_color="transparent")
    btn_frame.pack(fill="x", padx=15, pady=10)

    def do_export() -> None:
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


__all__ = ["show_word_preview"]
