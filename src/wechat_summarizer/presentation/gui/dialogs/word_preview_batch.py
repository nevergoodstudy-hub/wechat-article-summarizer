"""Batch Word preview dialog."""

from __future__ import annotations

import webbrowser
from tkinter import filedialog
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from ..styles.colors import ModernColors
from ..utils.i18n import tr
from .word_preview_render import render_article_document
from .word_preview_window import add_preview_toolbar, create_document_scroll, create_preview_window

if TYPE_CHECKING:
    from ....domain.entities import Article
    from ..app import WechatSummarizerGUI


def show_batch_word_preview(gui: WechatSummarizerGUI) -> None:
    """显示批量 Word 导出预览窗口（带翻页功能）- 与单篇预览样式一致"""
    if not gui.batch_results:
        return

    preview_window = create_preview_window(
        gui.root,
        tr("Word 导出预览 - 共 {count} 篇文章").format(count=len(gui.batch_results)),
        center_on_parent=True,
    )
    add_preview_toolbar(preview_window)

    current_page = [0]
    total_pages = len(gui.batch_results)
    nav = _create_navigation_bar(preview_window, current_page, total_pages)
    doc_scroll = create_document_scroll(preview_window)

    def update_preview() -> None:
        for widget in doc_scroll.winfo_children():
            widget.destroy()
        article = gui.batch_results[current_page[0]]
        nav["page_label"].configure(
            text=tr("第 {current} 篇 / 共 {total} 篇").format(
                current=current_page[0] + 1,
                total=total_pages,
            )
        )
        nav["prev_btn"].configure(state="normal" if current_page[0] > 0 else "disabled")
        nav["next_btn"].configure(
            state="normal" if current_page[0] < total_pages - 1 else "disabled"
        )
        render_article_document(
            doc_scroll,
            article,
            footer_text=_build_batch_footer(article, current_page[0], total_pages),
            bind_link=True,
        )

    def go_next() -> None:
        if current_page[0] < total_pages - 1:
            current_page[0] += 1
            update_preview()

    def go_prev() -> None:
        if current_page[0] > 0:
            current_page[0] -= 1
            update_preview()

    nav["prev_btn"].configure(command=go_prev)
    nav["next_btn"].configure(command=go_next)
    update_preview()
    _create_batch_buttons(preview_window, gui, current_page, total_pages)
    _bind_navigation_keys(preview_window, go_prev, go_next)


def _create_navigation_bar(
    preview_window: ctk.CTkToplevel,
    current_page: list[int],
    total_pages: int,
) -> dict[str, Any]:
    nav_bar = ctk.CTkFrame(preview_window, height=40, fg_color="transparent")
    nav_bar.pack(fill="x", padx=15, pady=(0, 5))
    prev_btn = ctk.CTkButton(
        nav_bar,
        text=tr("◀ 上一篇"),
        width=90,
        height=32,
        corner_radius=8,
        fg_color=ModernColors.NEUTRAL_BTN,
    )
    prev_btn.pack(side="left", padx=2)
    page_frame = ctk.CTkFrame(nav_bar, fg_color="transparent")
    page_frame.pack(side="left", expand=True)
    page_label = ctk.CTkLabel(
        page_frame,
        text=tr("第 {current} 篇 / 共 {total} 篇").format(
            current=current_page[0] + 1,
            total=total_pages,
        ),
        font=ctk.CTkFont(size=13),
    )
    page_label.pack()
    next_btn = ctk.CTkButton(
        nav_bar,
        text=tr("下一篇 ▶"),
        width=90,
        height=32,
        corner_radius=8,
        fg_color=ModernColors.NEUTRAL_BTN,
    )
    next_btn.pack(side="right", padx=2)
    return {"prev_btn": prev_btn, "page_label": page_label, "next_btn": next_btn}


def _create_batch_buttons(
    preview_window: ctk.CTkToplevel,
    gui: WechatSummarizerGUI,
    current_page: list[int],
    total_pages: int,
) -> None:
    btn_frame = ctk.CTkFrame(preview_window, fg_color="transparent")
    btn_frame.pack(fill="x", padx=15, pady=10)

    def open_current_url() -> None:
        article = gui.batch_results[current_page[0]]
        webbrowser.open(str(article.url))

    def do_export() -> None:
        dir_path = filedialog.askdirectory(title=tr("选择输出目录"))
        if dir_path:
            preview_window.destroy()
            gui._do_batch_export("word", dir_path)

    ctk.CTkButton(
        btn_frame,
        text=tr("🔗 查看当前原文"),
        width=120,
        height=38,
        corner_radius=8,
        fg_color=ModernColors.NEUTRAL_BTN,
        command=open_current_url,
    ).pack(side="left")
    ctk.CTkButton(
        btn_frame,
        text=tr("取消"),
        width=80,
        height=38,
        corner_radius=8,
        fg_color=ModernColors.NEUTRAL_BTN,
        command=preview_window.destroy,
    ).pack(side="right", padx=(5, 0))
    ctk.CTkButton(
        btn_frame,
        text=tr("✓ 导出全部 {count} 篇为 Word").format(count=total_pages),
        width=200,
        height=38,
        corner_radius=8,
        fg_color=ModernColors.SUCCESS,
        font=ctk.CTkFont(size=14, weight="bold"),
        command=do_export,
    ).pack(side="right")


def _bind_navigation_keys(
    preview_window: ctk.CTkToplevel,
    go_prev: Any,
    go_next: Any,
) -> None:
    def on_key(event: Any) -> None:
        if event.keysym == "Left":
            go_prev()
        elif event.keysym == "Right":
            go_next()

    preview_window.bind("<Left>", on_key)
    preview_window.bind("<Right>", on_key)


def _build_batch_footer(article: Article, page_index: int, total_pages: int) -> str:
    return tr("文章 {current}/{total} | ID: {article_id} | 抓取时间: {fetched_at}").format(
        current=page_index + 1,
        total=total_pages,
        article_id=article.id,
        fetched_at=article.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    )


__all__ = ["show_batch_word_preview"]
