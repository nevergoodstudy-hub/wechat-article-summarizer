"""Feature service for export workflows."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol

from .dto import ArchiveFormatPayload

if TYPE_CHECKING:
    from ...domain.entities import Article


class ArchiveExporterPort(Protocol):
    """Exporter surface needed by batch archive workflows."""

    def get_available_formats(self) -> list[Any]: ...

    def export_batch(
        self,
        articles: list[Article],
        path: str | None = None,
        archive_format: str = "zip",
        progress_callback: Callable[[int, int, str], None] | None = None,
        **options: Any,
    ) -> str: ...


class ExportWorkflowService:
    """Application-facing service for export-related workflows."""

    def __init__(self, archive_exporter: ArchiveExporterPort) -> None:
        self._archive_exporter = archive_exporter

    def list_archive_formats(self) -> list[ArchiveFormatPayload]:
        """List available archive formats without exposing infrastructure DTOs."""
        return [
            ArchiveFormatPayload(
                value=str(format_info.format.value),
                name=str(format_info.name),
                extension=str(format_info.extension),
                available=bool(format_info.available),
                reason=str(format_info.reason),
            )
            for format_info in self._archive_exporter.get_available_formats()
        ]

    def export_archive(
        self,
        articles: list[Article],
        path: str,
        archive_format: str,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> str:
        """Export articles into an archive."""
        return self._archive_exporter.export_batch(
            articles=articles,
            path=path,
            archive_format=archive_format,
            progress_callback=progress_callback,
        )
