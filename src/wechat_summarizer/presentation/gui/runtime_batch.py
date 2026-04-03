"""GUI 批量处理运行时逻辑。

将 `app.py` 中与批量抓取/摘要处理相关的线程与进度 UI 逻辑拆分到独立模块。
"""

from __future__ import annotations

import threading
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk
from loguru import logger

from ...domain.entities import Article
from ...shared.progress import BatchProgressTracker, ProgressInfo
from .styles import ModernColors


def on_import_urls(gui: Any) -> None:
    """导入 URL 文本文件到批量输入框。"""
    path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if not path:
        return

    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        gui.batch_url_text.delete("1.0", "end")
        gui.batch_url_text.insert("1.0", content)
        logger.info(f"已导入URL文件: {path}")
    except Exception as e:
        messagebox.showerror("错误", f"读取失败: {e}")


def on_paste_urls(gui: Any) -> None:
    """从剪贴板粘贴 URL 到批量输入框。"""
    try:
        content = gui.root.clipboard_get()
        gui.batch_url_text.insert("end", content)
    except Exception:
        messagebox.showwarning("提示", "剪贴板为空")


def on_batch_process(gui: Any) -> None:
    """校验并启动批量处理。"""
    content = gui.batch_url_text.get("1.0", "end").strip()
    if not content:
        messagebox.showwarning("提示", "请输入URL")
        return

    urls = [line.strip() for line in content.split("\n") if line.strip()]
    if not urls:
        messagebox.showwarning("提示", "未找到有效URL")
        return

    start_batch_processing(gui, urls)


def start_batch_processing(gui: Any, urls: list[str]) -> None:
    """开始批量处理。"""
    gui.batch_urls = urls
    gui.batch_results = []
    gui._batch_cancel_requested = False
    gui._batch_progress_tracker = BatchProgressTracker(
        total=len(urls), smoothing_factor=0.3, log_interval=1
    )
    gui._batch_progress_tracker.set_callback(gui._on_batch_progress_update)

    # 切换开始/停止按钮状态
    if hasattr(gui, "batch_page"):
        gui.batch_page.set_processing_state(True)
    else:
        gui.batch_start_btn.configure(state="disabled")

    gui.batch_page.batch_progress.set(0)
    gui.batch_status_label.configure(text=f"正在处理 0/{len(urls)} 篇...")
    gui.batch_page.batch_elapsed_label.configure(text="00:00")
    gui.batch_page.batch_eta_label.configure(text="--:--")
    gui.batch_rate_label.configure(text="计算中...")
    gui.batch_count_label.configure(text="0 / 0")

    # 设置任务状态（用于退出确认）
    gui._batch_processing_active = True

    logger.info(f"🚀 开始批量处理 {len(urls)} 篇文章")
    for widget in gui.batch_page.batch_result_frame.winfo_children():
        widget.destroy()

    threading.Thread(target=gui._batch_process_worker, daemon=True).start()


def on_batch_progress_update(gui: Any, info: ProgressInfo) -> None:
    """进度更新回调（在工作线程中调用）。"""
    gui.root.after(0, lambda: update_batch_progress_ui(gui, info))


def update_batch_progress_ui(gui: Any, info: ProgressInfo) -> None:
    """更新批量处理的 GUI 进度显示（在主线程中调用）。"""
    progress_value = info.percentage / 100.0
    gui.batch_progress.set(progress_value)
    gui.batch_status_label.configure(text=f"正在处理 {info.progress_text} ({info.percentage_text})")
    gui.batch_elapsed_label.configure(text=info.elapsed_formatted)
    gui.batch_eta_label.configure(text=info.eta_formatted)
    gui.batch_rate_label.configure(text=info.rate_formatted)

    if hasattr(gui, "_batch_progress_tracker"):
        tracker = gui._batch_progress_tracker
        gui.batch_count_label.configure(text=f"{tracker.success_count} / {tracker.failure_count}")


def batch_process_worker(gui: Any) -> None:
    """批量处理工作线程。"""
    method = gui.batch_method_var.get()
    len(gui.batch_urls)
    tracker = gui._batch_progress_tracker

    for _i, url in enumerate(gui.batch_urls):
        # 检查取消标志
        if getattr(gui, "_batch_cancel_requested", False):
            logger.info("ℹ️ 用户取消了批量处理")
            break

        short_url = url[:50] + "..." if len(url) > 50 else url
        try:
            article = gui.container.fetch_use_case.execute(url)
            try:
                summary = gui.container.summarize_use_case.execute(article, method=method)
                article.attach_summary(summary)
            except Exception as e:
                logger.warning(f"摘要失败: {e}")

            gui.batch_results.append(article)
            tracker.update_success(current_item=article.title[:30])
            gui.root.after(0, lambda a=article: gui._add_batch_result_item(a, True))
        except Exception as e:
            logger.error(f"处理失败 {short_url}: {e}")
            tracker.update_failure(current_item=short_url, error=str(e))
            gui.root.after(0, lambda u=url, err=str(e): gui._add_batch_result_item_error(u, err))

    tracker.finish()
    gui.root.after(0, gui._batch_process_complete)


def update_batch_progress(gui: Any, value: float, status: str) -> None:
    """更新批量进度（兼容旧接口）。"""
    gui.batch_progress.set(value)
    gui.batch_status_label.configure(text=status)


def add_batch_result_item(gui: Any, article: Article, success: bool) -> None:
    """添加批量结果项。"""
    frame = ctk.CTkFrame(
        gui.batch_result_frame,
        corner_radius=8,
        fg_color=(ModernColors.LIGHT_INSET, ModernColors.DARK_INSET),
    )
    frame.pack(fill="x", pady=3)
    icon = "✓" if success else "✗"
    color = ModernColors.SUCCESS if success else ModernColors.ERROR
    title = article.title[:35] + "..." if len(article.title) > 35 else article.title
    ctk.CTkLabel(frame, text=f"{icon} {title}", anchor="w", text_color=color).pack(
        side="left", padx=10, pady=8, fill="x", expand=True
    )


def add_batch_result_item_error(gui: Any, url: str, error: str) -> None:
    """添加批量错误项。"""
    frame = ctk.CTkFrame(
        gui.batch_result_frame,
        corner_radius=8,
        fg_color=(ModernColors.LIGHT_INSET, ModernColors.DARK_INSET),
    )
    frame.pack(fill="x", pady=3)
    short_url = url[:25] + "..." if len(url) > 25 else url
    ctk.CTkLabel(frame, text=f"✗ {short_url}", anchor="w", text_color=ModernColors.ERROR).pack(
        side="left", padx=10, pady=8
    )
    ctk.CTkLabel(frame, text=error[:30], text_color="gray", font=ctk.CTkFont(size=11)).pack(
        side="right", padx=10, pady=8
    )


def batch_process_complete(gui: Any) -> None:
    """批量处理完成。"""
    gui._batch_processing_active = False
    gui._batch_cancel_requested = False

    # 恢复按钮状态
    if hasattr(gui, "batch_page"):
        gui.batch_page.set_processing_state(False)
    else:
        gui.batch_start_btn.configure(state="normal")

    gui.batch_progress.set(1.0)
    success_count = len(gui.batch_results)
    total = len(gui.batch_urls)
    gui.batch_status_label.configure(text=f"完成: {success_count}/{total} 篇成功")
    logger.success(f"批量处理完成: {success_count}/{total}")

    if gui.batch_results:
        gui.batch_export_btn.configure(state="normal")
        gui.batch_page.batch_export_md_btn.configure(state="normal")
        gui.batch_page.batch_export_word_btn.configure(state="normal")
        gui.batch_export_html_btn.configure(state="normal")
