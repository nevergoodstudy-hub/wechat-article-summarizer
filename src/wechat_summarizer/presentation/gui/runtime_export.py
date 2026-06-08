"""GUI 批量导出运行时逻辑。

将 `app.py` 中与批量导出相关的后台线程与进度 UI 更新逻辑拆分到独立模块。
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from loguru import logger

from ...shared.progress import BatchProgressTracker, ProgressInfo
from .dialogs import (
    BatchArchiveExportDialog,
    choose_batch_output_directory,
    choose_export_file_path,
    show_batch_export_success,
    show_export_error,
    show_export_options_dialog,
    show_export_success,
)
from .styles.colors import ModernColors


def on_export(gui: Any) -> None:
    """单篇导出：弹出格式选择并执行。"""
    if not gui.current_article:
        return

    if not gui._check_export_dir_configured():
        return

    def export_as(target: str) -> None:
        if target == "word":
            gui._show_word_preview()
        else:
            do_export(gui, target)

    show_export_options_dialog(gui.root, gui._exporter_info, export_as)


def do_export(gui: Any, target: str) -> None:
    """执行单篇导出。"""
    if not gui.current_article:
        return

    logger.info(f"开始导出: {target}")
    ext_map = {
        "html": (".html", "HTML文件", "*.html"),
        "markdown": (".md", "Markdown文件", "*.md"),
        "word": (".docx", "Word文档", "*.docx"),
        "zip": (".zip", "ZIP文件", "*.zip"),
    }
    ext_info = ext_map.get(target, (".html", "HTML文件", "*.html"))

    initial_dir = None
    if gui.user_prefs.remember_export_dir and gui.user_prefs.export_dir:
        dir_path = Path(gui.user_prefs.export_dir)
        if dir_path.exists():
            initial_dir = str(dir_path)
    if not initial_dir:
        default_dir = gui.settings.export.default_output_dir
        if default_dir and Path(default_dir).exists():
            initial_dir = default_dir

    path = choose_export_file_path(
        extension=ext_info[0],
        filetype_name=ext_info[1],
        filetype_pattern=ext_info[2],
        article_title=gui.current_article.title,
        initial_dir=initial_dir,
    )
    if not path:
        logger.info("导出已取消")
        return

    if gui.user_prefs.remember_export_dir:
        export_dir = str(Path(path).parent)
        if export_dir != gui.user_prefs.export_dir:
            gui.user_prefs.export_dir = export_dir
            logger.info(f"已记住导出目录: {export_dir}")

    gui.export_btn.configure(state="disabled")
    gui._set_status("正在导出...", ModernColors.INFO)

    def do_export_thread() -> None:
        try:
            logger.info(f"导出路径: {path}")
            result = gui.container.export_use_case.execute(
                gui.current_article, target=target, path=path
            )
            logger.success(f"导出成功: {result}")
            gui.root.after(0, lambda: export_complete(gui, True, str(result)))
        except Exception as e:
            logger.error(f"导出失败: {e}")
            error_msg = str(e)
            gui.root.after(0, lambda msg=error_msg: export_complete(gui, False, msg))

    threading.Thread(target=do_export_thread, daemon=True).start()


def export_complete(gui: Any, success: bool, message: str) -> None:
    """单篇导出完成。"""
    gui.export_btn.configure(state="normal")
    if success:
        gui._set_status("导出完成", ModernColors.SUCCESS)
        show_export_success(message)
    else:
        gui._set_status("导出失败", ModernColors.ERROR)
        show_export_error(message)


def on_batch_export(gui: Any) -> None:
    """批量压缩导出 - 支持多格式和文章选择。"""
    if not gui.batch_results:
        return

    if not gui._check_export_dir_configured():
        return

    archive_formats = gui.container.export_workflow_service.list_archive_formats()
    dialog = BatchArchiveExportDialog(gui.root, gui.batch_results, archive_formats)
    result = dialog.get()
    if not result:
        return

    do_archive_export(
        gui,
        articles=result["articles"],
        archive_format=result["format"],
        path=result["path"],
    )


def do_archive_export(gui: Any, articles: list, archive_format: str, path: str) -> None:
    """执行多格式压缩导出（带进度跟踪）。"""
    disable_export_buttons(gui)
    gui._archive_export_articles = articles
    gui._archive_progress_tracker = BatchProgressTracker(
        total=len(articles), smoothing_factor=0.3, log_interval=1
    )
    gui._archive_progress_tracker.set_callback(gui._on_export_progress_update)
    gui.batch_progress.set(0)

    format_names = {"zip": "ZIP", "7z": "7z", "rar": "RAR"}
    format_name = format_names.get(archive_format, archive_format.upper())

    gui.batch_status_label.configure(text=f"正在打包 0/{len(articles)} 篇为 {format_name}...")
    gui.batch_elapsed_label.configure(text="00:00")
    gui.batch_eta_label.configure(text="--:--")
    gui.batch_rate_label.configure(text="计算中...")
    gui.batch_count_label.configure(text="0 / 0")

    gui._batch_export_active = True
    logger.info(f"📦 开始导出 {len(articles)} 篇文章为 {format_name} 压缩包")
    threading.Thread(
        target=archive_export_worker, args=(gui, articles, archive_format, path), daemon=True
    ).start()


def archive_export_worker(gui: Any, articles: list, archive_format: str, path: str) -> None:
    """工作线程：执行多格式压缩导出。"""
    try:
        tracker = gui._archive_progress_tracker

        def progress_callback(current: int, total: int, item_name: str) -> None:
            if current > tracker.current:
                tracker.update_success(current_item=item_name)

        result = gui.container.export_workflow_service.export_archive(
            articles=articles,
            path=path,
            archive_format=archive_format,
            progress_callback=progress_callback,
        )

        tracker.finish()
        gui.root.after(0, lambda: archive_export_complete(gui, result, archive_format))
    except Exception as e:
        logger.error(f"压缩导出失败: {e}")
        error_msg = str(e)
        gui.root.after(0, lambda msg=error_msg: archive_export_error(gui, msg))


def archive_export_complete(gui: Any, result: str, archive_format: str) -> None:
    """处理压缩导出完成。"""
    gui._batch_export_active = False

    enable_export_buttons(gui)
    gui.batch_progress.set(1.0)

    format_names = {"zip": "ZIP", "7z": "7z", "rar": "RAR"}
    format_name = format_names.get(archive_format, archive_format.upper())

    gui.batch_status_label.configure(text=f"{format_name} 导出完成")
    logger.success(f"批量导出成功: {result}")
    show_export_success(result)


def archive_export_error(gui: Any, error: str) -> None:
    """处理压缩导出错误。"""
    gui._batch_export_active = False

    enable_export_buttons(gui)
    gui.batch_status_label.configure(text="压缩导出失败")
    show_export_error(error)


def on_batch_export_format(gui: Any, target: str) -> None:
    """批量导出指定格式。"""
    if not gui.batch_results:
        return

    if not gui._check_export_dir_configured():
        return

    if target == "word":
        gui._show_batch_word_preview()
        return

    dir_path = choose_batch_output_directory()
    if not dir_path:
        return

    do_batch_export(gui, target, dir_path)


def do_batch_export(gui: Any, target: str, dir_path: str) -> None:
    """执行批量导出（后台线程）。"""
    disable_export_buttons(gui)
    gui._export_progress_tracker = BatchProgressTracker(
        total=len(gui.batch_results), smoothing_factor=0.3, log_interval=1
    )
    gui._export_progress_tracker.set_callback(gui._on_export_progress_update)
    gui.batch_progress.set(0)
    gui.batch_status_label.configure(text=f"正在导出 0/{len(gui.batch_results)} 篇...")
    gui.batch_elapsed_label.configure(text="00:00")
    gui.batch_eta_label.configure(text="--:--")
    gui.batch_rate_label.configure(text="计算中...")
    gui.batch_count_label.configure(text="0 / 0")

    gui._batch_export_active = True

    logger.info(f"📤 开始批量导出 {len(gui.batch_results)} 篇文章为 {target.upper()} 格式")
    threading.Thread(target=batch_export_worker, args=(gui, target, dir_path), daemon=True).start()


def on_export_progress_update(gui: Any, info: ProgressInfo) -> None:
    """导出进度更新回调。"""
    gui.root.after(0, lambda: update_export_progress_ui(gui, info))


def update_export_progress_ui(gui: Any, info: ProgressInfo) -> None:
    """更新导出进度 GUI 显示。"""
    progress_value = info.percentage / 100.0
    gui.batch_progress.set(progress_value)
    gui.batch_status_label.configure(text=f"正在导出 {info.progress_text} ({info.percentage_text})")
    gui.batch_elapsed_label.configure(text=info.elapsed_formatted)
    gui.batch_eta_label.configure(text=info.eta_formatted)
    gui.batch_rate_label.configure(text=info.rate_formatted)
    if hasattr(gui, "_export_progress_tracker"):
        tracker = gui._export_progress_tracker
        gui.batch_count_label.configure(text=f"{tracker.success_count} / {tracker.failure_count}")


def batch_export_worker(gui: Any, target: str, dir_path: str) -> None:
    """批量导出工作线程。"""
    try:
        output_dir = Path(dir_path)
        tracker = gui._export_progress_tracker
        ext_map = {"markdown": ".md", "html": ".html", "word": ".docx"}
        ext = ext_map.get(target, ".html")
        for article in gui.batch_results:
            try:
                safe_title = "".join(
                    c for c in article.title[:50] if c.isalnum() or c in " _-"
                ).strip()
                file_path = output_dir / f"{safe_title}{ext}"
                gui.container.export_use_case.execute(article, target=target, path=str(file_path))
                tracker.update_success(current_item=article.title[:30])
            except Exception as e:
                logger.warning(f"导出失败 {article.title}: {e}")
                tracker.update_failure(current_item=article.title[:30], error=str(e))
        tracker.finish()
        gui.root.after(
            0,
            lambda: batch_export_complete(
                gui, tracker.success_count, tracker.failure_count, dir_path
            ),
        )
    except Exception as e:
        logger.error(f"导出失败: {e}")
        error_msg = str(e)
        gui.root.after(0, lambda msg=error_msg: batch_export_error(gui, msg))


def batch_export_complete(gui: Any, success_count: int, failure_count: int, dir_path: str) -> None:
    """批量导出完成。"""
    gui._batch_export_active = False

    enable_export_buttons(gui)
    gui.batch_progress.set(1.0)
    gui.batch_status_label.configure(text=f"导出完成: {success_count} 成功, {failure_count} 失败")
    total = success_count + failure_count
    logger.success(f"批量导出完成: {success_count}/{total}")
    show_batch_export_success(success_count, total, dir_path)


def batch_export_error(gui: Any, error: str) -> None:
    """批量导出出错。"""
    gui._batch_export_active = False

    enable_export_buttons(gui)
    gui.batch_status_label.configure(text="导出失败")
    show_export_error(error)


def disable_export_buttons(gui: Any) -> None:
    """禁用所有导出按钮。"""
    gui.batch_export_btn.configure(state="disabled")
    gui.batch_export_md_btn.configure(state="disabled")
    gui.batch_export_word_btn.configure(state="disabled")
    gui.batch_export_html_btn.configure(state="disabled")


def enable_export_buttons(gui: Any) -> None:
    """启用所有导出按钮。"""
    if gui.batch_results:
        gui.batch_export_btn.configure(state="normal")
        gui.batch_export_md_btn.configure(state="normal")
        gui.batch_export_word_btn.configure(state="normal")
        gui.batch_export_html_btn.configure(state="normal")
