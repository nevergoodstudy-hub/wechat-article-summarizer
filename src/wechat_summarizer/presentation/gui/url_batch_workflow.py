"""URL 批处理工作流协调器。"""

from __future__ import annotations

import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING

from loguru import logger

from ...shared.progress import BatchProgressTracker, ProgressInfo
from .dialogs.batch_archive_export import BatchArchiveExportDialog
from .styles.colors import ModernColors

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False

if TYPE_CHECKING:
    from ...domain.entities import Article
    from .app import WechatSummarizerGUI


class UrlBatchWorkflowCoordinator:
    """协调 URL 批处理与导出流程。"""

    def __init__(self, gui: WechatSummarizerGUI) -> None:
        self.gui = gui

    def on_import_urls(self):
        """导入 URL 列表。"""
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return None
        try:
            content = Path(path).read_text(encoding="utf-8")
            self.gui.batch_url_text.delete("1.0", "end")
            self.gui.batch_url_text.insert("1.0", content)
            logger.info(f"已导入URL文件: {path}")
        except Exception as exc:
            messagebox.showerror("错误", f"读取失败: {exc}")
        return None

    def on_paste_urls(self):
        """从剪贴板粘贴 URL。"""
        try:
            content = self.gui.root.clipboard_get()
            self.gui.batch_url_text.insert("end", content)
        except Exception:
            messagebox.showwarning("提示", "剪贴板为空")
        return None

    def on_batch_process(self):
        """开始批量处理。"""
        content = self.gui.batch_url_text.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("提示", "请输入URL")
            return None

        urls = [line.strip() for line in content.split("\n") if line.strip()]
        if not urls:
            messagebox.showwarning("提示", "未找到有效URL")
            return None

        self.start_batch_processing(urls)
        return None

    def start_batch_processing(self, urls: list[str]) -> None:
        """初始化批量处理状态并启动后台线程。"""
        self.gui.batch_urls = urls
        self.gui.batch_results = []
        self.gui._batch_cancel_requested = False
        self.gui._batch_progress_tracker = BatchProgressTracker(
            total=len(urls),
            smoothing_factor=0.3,
            log_interval=1,
        )
        self.gui._batch_progress_tracker.set_callback(self.on_batch_progress_update)

        if hasattr(self.gui, "batch_page"):
            self.gui.batch_page.set_processing_state(True)
        else:
            self.gui.batch_start_btn.configure(state="disabled")

        self.gui.batch_progress.set(0)
        self.gui.batch_status_label.configure(text=f"正在处理 0/{len(urls)} 篇...")
        self.gui.batch_elapsed_label.configure(text="00:00")
        self.gui.batch_eta_label.configure(text="--:--")
        self.gui.batch_rate_label.configure(text="计算中...")
        self.gui.batch_count_label.configure(text="0 / 0")

        self.gui._batch_processing_active = True

        logger.info(f"🚀 开始批量处理 {len(urls)} 篇文章")
        for widget in self.gui.batch_result_frame.winfo_children():
            widget.destroy()
        threading.Thread(target=self.batch_process_worker, daemon=True).start()

    def on_batch_progress_update(self, info: ProgressInfo) -> None:
        """在主线程刷新批量处理进度。"""
        self.gui.root.after(0, lambda: self.update_batch_progress_ui(info))

    def update_batch_progress_ui(self, info: ProgressInfo) -> None:
        """更新批量处理的 GUI 进度显示。"""
        self.gui.batch_progress.set(info.percentage / 100.0)
        self.gui.batch_status_label.configure(
            text=f"正在处理 {info.progress_text} ({info.percentage_text})"
        )
        self.gui.batch_elapsed_label.configure(text=info.elapsed_formatted)
        self.gui.batch_eta_label.configure(text=info.eta_formatted)
        self.gui.batch_rate_label.configure(text=info.rate_formatted)
        tracker = getattr(self.gui, "_batch_progress_tracker", None)
        if tracker is not None:
            self.gui.batch_count_label.configure(
                text=f"{tracker.success_count} / {tracker.failure_count}"
            )

    def update_batch_progress(self, value: float, status: str) -> None:
        """兼容旧接口的批量进度更新。"""
        self.gui.batch_progress.set(value)
        self.gui.batch_status_label.configure(text=status)

    def batch_process_worker(self) -> None:
        """后台线程：批量抓取与摘要。"""
        method = self.gui.batch_method_var.get()
        tracker = self.gui._batch_progress_tracker
        if tracker is None:
            return
        for url in self.gui.batch_urls:
            if getattr(self.gui, "_batch_cancel_requested", False):
                logger.info("ℹ️ 用户取消了批量处理")
                break

            short_url = url[:50] + "..." if len(url) > 50 else url
            try:
                article = self.gui.container.fetch_use_case.execute(url)
                try:
                    summary = self.gui.container.summarize_use_case.execute(article, method=method)
                    article.attach_summary(summary)
                except Exception as exc:
                    logger.warning(f"摘要失败: {exc}")
                self.gui.batch_results.append(article)
                tracker.update_success(current_item=article.title[:30])
                self.gui.root.after(0, lambda current_article=article: self.add_batch_result_item(current_article, True))
            except Exception as exc:
                logger.error(f"处理失败 {short_url}: {exc}")
                tracker.update_failure(current_item=short_url, error=str(exc))
                self.gui.root.after(
                    0,
                    lambda current_url=url, err=str(exc): self.add_batch_result_item_error(current_url, err),
                )

        tracker.finish()
        self.gui.root.after(0, self.batch_process_complete)

    def add_batch_result_item(self, article: Article, success: bool) -> None:
        """向结果列表添加成功项。"""
        frame = ctk.CTkFrame(
            self.gui.batch_result_frame,
            corner_radius=8,
            fg_color=(ModernColors.LIGHT_INSET, ModernColors.DARK_INSET),
        )
        frame.pack(fill="x", pady=3)
        icon = "✓" if success else "✗"
        color = ModernColors.SUCCESS if success else ModernColors.ERROR
        title = article.title[:35] + "..." if len(article.title) > 35 else article.title
        ctk.CTkLabel(frame, text=f"{icon} {title}", anchor="w", text_color=color).pack(
            side="left",
            padx=10,
            pady=8,
            fill="x",
            expand=True,
        )

    def add_batch_result_item_error(self, url: str, error: str) -> None:
        """向结果列表添加失败项。"""
        frame = ctk.CTkFrame(
            self.gui.batch_result_frame,
            corner_radius=8,
            fg_color=(ModernColors.LIGHT_INSET, ModernColors.DARK_INSET),
        )
        frame.pack(fill="x", pady=3)
        short_url = url[:25] + "..." if len(url) > 25 else url
        ctk.CTkLabel(
            frame,
            text=f"✗ {short_url}",
            anchor="w",
            text_color=ModernColors.ERROR,
        ).pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(
            frame,
            text=error[:30],
            text_color="gray",
            font=ctk.CTkFont(size=11),
        ).pack(side="right", padx=10, pady=8)

    def batch_process_complete(self) -> None:
        """收尾批量处理状态。"""
        self.gui._batch_processing_active = False
        self.gui._batch_cancel_requested = False

        if hasattr(self.gui, "batch_page"):
            self.gui.batch_page.set_processing_state(False)
        else:
            self.gui.batch_start_btn.configure(state="normal")

        self.gui.batch_progress.set(1.0)
        success_count = len(self.gui.batch_results)
        total = len(self.gui.batch_urls)
        self.gui.batch_status_label.configure(text=f"完成: {success_count}/{total} 篇成功")
        logger.success(f"批量处理完成: {success_count}/{total}")

        if self.gui.batch_results:
            self.enable_export_buttons()

    def on_batch_export(self):
        """批量压缩导出。"""
        if not self.gui.batch_results:
            return None

        if not self.gui._check_export_dir_configured():
            return None

        dialog = BatchArchiveExportDialog(self.gui.root, self.gui.batch_results)
        result = dialog.get()
        if not result:
            return None

        self.do_archive_export(
            articles=result["articles"],
            archive_format=result["format"],
            path=result["path"],
        )
        return None

    def do_archive_export(self, articles: list, archive_format: str, path: str) -> None:
        """执行多格式压缩导出。"""
        self.disable_export_buttons()
        self.gui._archive_export_articles = articles
        self.gui._archive_progress_tracker = BatchProgressTracker(
            total=len(articles),
            smoothing_factor=0.3,
            log_interval=1,
        )
        self.gui._zip_progress_tracker = self.gui._archive_progress_tracker
        self.gui._archive_progress_tracker.set_callback(self.on_export_progress_update)
        self.gui.batch_progress.set(0)

        format_names = {"zip": "ZIP", "7z": "7z", "rar": "RAR"}
        format_name = format_names.get(archive_format, archive_format.upper())

        self.gui.batch_status_label.configure(text=f"正在打包 0/{len(articles)} 篇为 {format_name}...")
        self.gui.batch_elapsed_label.configure(text="00:00")
        self.gui.batch_eta_label.configure(text="--:--")
        self.gui.batch_rate_label.configure(text="计算中...")
        self.gui.batch_count_label.configure(text="0 / 0")

        self.gui._batch_export_active = True

        logger.info(f"📦 开始导出 {len(articles)} 篇文章为 {format_name} 压缩包")
        threading.Thread(
            target=self.archive_export_worker,
            args=(articles, archive_format, path),
            daemon=True,
        ).start()

    def archive_export_worker(self, articles: list, archive_format: str, path: str) -> None:
        """后台线程：执行多格式压缩导出。"""
        try:
            from ...infrastructure.adapters.exporters import MultiFormatArchiveExporter

            tracker = self.gui._archive_progress_tracker
            if tracker is None:
                return

            def progress_callback(current: int, total: int, item_name: str) -> None:
                if current > tracker.current:
                    tracker.update_success(current_item=item_name)

            exporter = MultiFormatArchiveExporter()
            result = exporter.export_batch(
                articles=articles,
                path=path,
                archive_format=archive_format,
                progress_callback=progress_callback,
            )

            tracker.finish()
            self.gui.root.after(0, lambda: self.archive_export_complete(result, archive_format))
        except Exception as exc:
            logger.error(f"压缩导出失败: {exc}")
            self.gui.root.after(0, lambda message=str(exc): self.archive_export_error(message))

    def archive_export_complete(self, result: str, archive_format: str) -> None:
        """处理压缩导出成功。"""
        self.gui._batch_export_active = False
        self.enable_export_buttons()
        self.gui.batch_progress.set(1.0)

        format_names = {"zip": "ZIP", "7z": "7z", "rar": "RAR"}
        format_name = format_names.get(archive_format, archive_format.upper())

        self.gui.batch_status_label.configure(text=f"{format_name} 导出完成")
        logger.success(f"批量导出成功: {result}")
        messagebox.showinfo("成功", f"导出成功: {result}")

    def archive_export_error(self, error: str) -> None:
        """处理压缩导出失败。"""
        self.gui._batch_export_active = False
        self.enable_export_buttons()
        self.gui.batch_status_label.configure(text="压缩导出失败")
        messagebox.showerror("错误", f"导出失败: {error}")

    def on_batch_export_format(self, target: str):
        """批量导出指定格式。"""
        if not self.gui.batch_results:
            return None

        if not self.gui._check_export_dir_configured():
            return None

        if target == "word":
            self.gui._show_batch_word_preview()
            return None

        dir_path = filedialog.askdirectory(title="选择输出目录")
        if not dir_path:
            return None
        self.do_batch_export(target, dir_path)
        return None

    def do_batch_export(self, target: str, dir_path: str) -> None:
        """执行目录型批量导出。"""
        self.disable_export_buttons()
        self.gui._export_progress_tracker = BatchProgressTracker(
            total=len(self.gui.batch_results),
            smoothing_factor=0.3,
            log_interval=1,
        )
        self.gui._export_progress_tracker.set_callback(self.on_export_progress_update)
        self.gui.batch_progress.set(0)
        self.gui.batch_status_label.configure(text=f"正在导出 0/{len(self.gui.batch_results)} 篇...")
        self.gui.batch_elapsed_label.configure(text="00:00")
        self.gui.batch_eta_label.configure(text="--:--")
        self.gui.batch_rate_label.configure(text="计算中...")
        self.gui.batch_count_label.configure(text="0 / 0")

        self.gui._batch_export_active = True

        logger.info(f"📤 开始批量导出 {len(self.gui.batch_results)} 篇文章为 {target.upper()} 格式")
        threading.Thread(
            target=self.batch_export_worker,
            args=(target, dir_path),
            daemon=True,
        ).start()

    def on_export_progress_update(self, info: ProgressInfo) -> None:
        """在主线程刷新导出进度。"""
        self.gui.root.after(0, lambda: self.update_export_progress_ui(info))

    def update_export_progress_ui(self, info: ProgressInfo) -> None:
        """更新导出进度的 GUI 显示。"""
        self.gui.batch_progress.set(info.percentage / 100.0)
        self.gui.batch_status_label.configure(
            text=f"正在导出 {info.progress_text} ({info.percentage_text})"
        )
        self.gui.batch_elapsed_label.configure(text=info.elapsed_formatted)
        self.gui.batch_eta_label.configure(text=info.eta_formatted)
        self.gui.batch_rate_label.configure(text=info.rate_formatted)
        tracker = getattr(self.gui, "_export_progress_tracker", None)
        if tracker is not None:
            self.gui.batch_count_label.configure(
                text=f"{tracker.success_count} / {tracker.failure_count}"
            )

    def batch_export_worker(self, target: str, dir_path: str) -> None:
        """后台线程：执行目录型批量导出。"""
        try:
            output_dir = Path(dir_path)
            tracker = self.gui._export_progress_tracker
            if tracker is None:
                return
            ext_map = {"markdown": ".md", "html": ".html", "word": ".docx"}
            ext = ext_map.get(target, ".html")

            for article in self.gui.batch_results:
                try:
                    safe_title = "".join(
                        char for char in article.title[:50] if char.isalnum() or char in " _-"
                    ).strip()
                    file_path = output_dir / f"{safe_title}{ext}"
                    self.gui.container.export_use_case.execute(
                        article,
                        target=target,
                        path=str(file_path),
                    )
                    tracker.update_success(current_item=article.title[:30])
                except Exception as exc:
                    logger.warning(f"导出失败 {article.title}: {exc}")
                    tracker.update_failure(current_item=article.title[:30], error=str(exc))

            tracker.finish()
            self.gui.root.after(
                0,
                lambda: self.batch_export_complete(
                    tracker.success_count,
                    tracker.failure_count,
                    dir_path,
                ),
            )
        except Exception as exc:
            logger.error(f"导出失败: {exc}")
            self.gui.root.after(0, lambda message=str(exc): self.batch_export_error(message))

    def batch_export_complete(self, success_count: int, failure_count: int, dir_path: str) -> None:
        """处理目录型批量导出成功。"""
        self.gui._batch_export_active = False
        self.enable_export_buttons()
        self.gui.batch_progress.set(1.0)
        self.gui.batch_status_label.configure(
            text=f"导出完成: {success_count} 成功, {failure_count} 失败"
        )
        total = success_count + failure_count
        logger.success(f"批量导出完成: {success_count}/{total}")
        messagebox.showinfo("成功", f"导出完成: {success_count}/{total} 篇\n输出目录: {dir_path}")

    def batch_export_error(self, error: str) -> None:
        """处理目录型批量导出失败。"""
        self.gui._batch_export_active = False
        self.enable_export_buttons()
        self.gui.batch_status_label.configure(text="导出失败")
        messagebox.showerror("错误", f"导出失败: {error}")

    def disable_export_buttons(self) -> None:
        """禁用所有批量导出按钮。"""
        self.gui.batch_export_btn.configure(state="disabled")
        self.gui.batch_export_md_btn.configure(state="disabled")
        self.gui.batch_export_word_btn.configure(state="disabled")
        self.gui.batch_export_html_btn.configure(state="disabled")

    def enable_export_buttons(self) -> None:
        """按结果状态启用批量导出按钮。"""
        if self.gui.batch_results:
            self.gui.batch_export_btn.configure(state="normal")
            self.gui.batch_export_md_btn.configure(state="normal")
            self.gui.batch_export_word_btn.configure(state="normal")
            self.gui.batch_export_html_btn.configure(state="normal")
