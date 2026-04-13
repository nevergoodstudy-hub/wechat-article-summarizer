"""Thin runtime wrappers that delegate batch/export behavior to helper modules."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...shared.progress import ProgressInfo
from .dialogs.word_preview import (
    build_content_preview_with_images,
    extract_images_from_article,
    show_batch_word_preview,
    show_word_preview,
)
from .runtime_batch import (
    add_batch_result_item,
    add_batch_result_item_error,
    batch_process_complete,
    batch_process_worker,
    on_batch_process,
    on_batch_progress_update,
    on_import_urls,
    on_paste_urls,
    start_batch_processing,
    update_batch_progress,
    update_batch_progress_ui,
)
from .runtime_export import (
    archive_export_complete,
    archive_export_error,
    archive_export_worker,
    batch_export_complete,
    batch_export_error,
    batch_export_worker,
    disable_export_buttons,
    do_archive_export,
    do_batch_export,
    do_export,
    enable_export_buttons,
    export_complete,
    on_batch_export,
    on_batch_export_format,
    on_export,
    on_export_progress_update,
    update_export_progress_ui,
)

if TYPE_CHECKING:
    from ...domain.entities import Article


class GUIRuntimeMixin:
    """Provides backward-compatible instance methods for helper-based runtime logic."""

    def _on_export(self: Any) -> None:
        on_export(self)

    def _show_word_preview(self: Any) -> None:
        show_word_preview(self)

    def _show_batch_word_preview(self: Any) -> None:
        show_batch_word_preview(self)

    def _build_content_preview_with_images(self: Any, article: Article) -> str:
        return build_content_preview_with_images(article)

    def _extract_images_from_article(self: Any, article: Article) -> list[str]:
        return extract_images_from_article(article)

    def _do_export(self: Any, target: str) -> None:
        do_export(self, target)

    def _export_complete(self: Any, success: bool, message: str) -> None:
        export_complete(self, success, message)

    def _on_import_urls(self: Any) -> None:
        on_import_urls(self)

    def _on_paste_urls(self: Any) -> None:
        on_paste_urls(self)

    def _on_batch_process(self: Any) -> None:
        on_batch_process(self)

    def _start_batch_processing(self: Any, urls: list[str]) -> None:
        start_batch_processing(self, urls)

    def _on_batch_progress_update(self: Any, info: ProgressInfo) -> None:
        on_batch_progress_update(self, info)

    def _update_batch_progress_ui(self: Any, info: ProgressInfo) -> None:
        update_batch_progress_ui(self, info)

    def _batch_process_worker(self: Any) -> None:
        batch_process_worker(self)

    def _update_batch_progress(self: Any, value: float, status: str) -> None:
        update_batch_progress(self, value, status)

    def _add_batch_result_item(self: Any, article: Article, success: bool) -> None:
        add_batch_result_item(self, article, success)

    def _add_batch_result_item_error(self: Any, url: str, error: str) -> None:
        add_batch_result_item_error(self, url, error)

    def _batch_process_complete(self: Any) -> None:
        batch_process_complete(self)

    def _on_batch_export(self: Any) -> None:
        on_batch_export(self)

    def _do_archive_export(self: Any, articles: list[Any], archive_format: str, path: str) -> None:
        do_archive_export(self, articles, archive_format, path)

    def _archive_export_worker(
        self: Any,
        articles: list[Any],
        archive_format: str,
        path: str,
    ) -> None:
        archive_export_worker(self, articles, archive_format, path)

    def _archive_export_complete(self: Any, result: str, archive_format: str) -> None:
        archive_export_complete(self, result, archive_format)

    def _archive_export_error(self: Any, error: str) -> None:
        archive_export_error(self, error)

    def _on_batch_export_format(self: Any, target: str) -> None:
        on_batch_export_format(self, target)

    def _do_batch_export(self: Any, target: str, dir_path: str) -> None:
        do_batch_export(self, target, dir_path)

    def _on_export_progress_update(self: Any, info: ProgressInfo) -> None:
        on_export_progress_update(self, info)

    def _update_export_progress_ui(self: Any, info: ProgressInfo) -> None:
        update_export_progress_ui(self, info)

    def _batch_export_worker(self: Any, target: str, dir_path: str) -> None:
        batch_export_worker(self, target, dir_path)

    def _batch_export_complete(
        self: Any,
        success_count: int,
        failure_count: int,
        dir_path: str,
    ) -> None:
        batch_export_complete(self, success_count, failure_count, dir_path)

    def _batch_export_error(self: Any, error: str) -> None:
        batch_export_error(self, error)

    def _disable_export_buttons(self: Any) -> None:
        disable_export_buttons(self)

    def _enable_export_buttons(self: Any) -> None:
        enable_export_buttons(self)
