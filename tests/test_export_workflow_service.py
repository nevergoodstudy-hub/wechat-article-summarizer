"""Tests for export workflow service."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from unittest.mock import Mock

import pytest

from wechat_summarizer.features.export_workflow import ExportWorkflowService


class _ArchiveFormat(Enum):
    ZIP = "zip"
    RAR = "rar"


@dataclass
class _ArchiveFormatInfo:
    format: _ArchiveFormat
    name: str
    extension: str
    available: bool
    reason: str


@pytest.mark.unit
class TestExportWorkflowService:
    """Archive exporter details should stay behind the feature service."""

    def test_list_archive_formats_projects_payloads(self) -> None:
        archive_exporter = Mock()
        archive_exporter.get_available_formats.return_value = [
            _ArchiveFormatInfo(_ArchiveFormat.ZIP, "ZIP", ".zip", True, "standard"),
            _ArchiveFormatInfo(_ArchiveFormat.RAR, "RAR", ".rar", False, "missing tool"),
        ]

        service = ExportWorkflowService(archive_exporter)

        payload = service.list_archive_formats()

        assert [item.value for item in payload] == ["zip", "rar"]
        assert payload[0].display_name == "✓ ZIP (.zip)"
        assert payload[1].available is False
        assert payload[1].reason == "missing tool"

    def test_export_archive_delegates_to_archive_exporter(self, sample_article) -> None:
        archive_exporter = Mock()
        archive_exporter.export_batch.return_value = "out.zip"
        service = ExportWorkflowService(archive_exporter)

        result = service.export_archive(
            [sample_article],
            path="out.zip",
            archive_format="zip",
            progress_callback=None,
        )

        assert result == "out.zip"
        archive_exporter.export_batch.assert_called_once_with(
            articles=[sample_article],
            path="out.zip",
            archive_format="zip",
            progress_callback=None,
        )
