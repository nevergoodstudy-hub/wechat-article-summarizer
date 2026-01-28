"""Obsidian 导出器

实现方式：复用 MarkdownExporter 生成 Markdown，然后将文件写入 Obsidian Vault 目录。

注意：Obsidian 本质上就是一个 Markdown 文件夹，因此该导出器是“文件导出”的语义增强。
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from ....domain.entities import Article
from ....shared.exceptions import ExporterError
from .base import BaseExporter
from .markdown import MarkdownExporter


class ObsidianExporter(BaseExporter):
    """Obsidian 导出器"""

    def __init__(self, vault_path: str = ""):
        self._vault_path = vault_path

    @property
    def name(self) -> str:
        return "obsidian"

    @property
    def target(self) -> str:
        return "obsidian"

    def is_available(self) -> bool:
        # 不在这里创建目录，避免 `check` 命令产生副作用
        return bool(self._vault_path)

    def export(self, article: Article, path: str | None = None, **options) -> str:
        if not self._vault_path and not path:
            raise ExporterError("未配置 Obsidian Vault 路径（export.obsidian_vault_path）")

        base = Path(path) if path else Path(self._vault_path)

        # 如果用户传入的是文件路径，则直接写入该文件
        if base.suffix.lower() == ".md":
            out_file = base
            out_dir = out_file.parent
            out_dir.mkdir(parents=True, exist_ok=True)
            exporter = MarkdownExporter(output_dir=str(out_dir))
            result = exporter.export(article, path=str(out_file), **options)
            logger.info(f"Obsidian导出成功: {result}")
            return result

        # 目录模式：写入 vault 目录
        out_dir = base
        out_dir.mkdir(parents=True, exist_ok=True)

        exporter = MarkdownExporter(output_dir=str(out_dir))
        result = exporter.export(article, path=str(out_dir), **options)
        logger.info(f"Obsidian导出成功: {result}")
        return result
