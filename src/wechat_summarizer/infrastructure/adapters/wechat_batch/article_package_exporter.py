"""Markdown 文章内容包导出器。"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from ....domain.entities.article import Article


class MarkdownExporterProtocol(Protocol):
    """Markdown 导出器协议。"""

    def export(
        self,
        article: Article,
        path: str | None = None,
        **options: Any,
    ) -> str:
        """导出单篇文章到 Markdown 文件。"""
        ...


class MarkdownArticlePackageExporter:
    """把文章导出为 Markdown 文件并打包成 ZIP。"""

    def __init__(self, markdown_exporter: MarkdownExporterProtocol | None = None) -> None:
        if markdown_exporter is None:
            from ..exporters.markdown import MarkdownExporter

            markdown_exporter = MarkdownExporter()
        self._markdown_exporter = markdown_exporter

    def export(
        self,
        *,
        articles: list[Article],
        output_path: str | Path,
        manifest: dict,
    ) -> Path:
        archive_path = Path(output_path)
        archive_path.parent.mkdir(parents=True, exist_ok=True)

        with TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            for article in articles:
                self._markdown_exporter.export(article, path=str(temp_dir))

            manifest_path = temp_dir / "manifest.json"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
                for file_path in temp_dir.iterdir():
                    archive.write(file_path, arcname=file_path.name)

        return archive_path
