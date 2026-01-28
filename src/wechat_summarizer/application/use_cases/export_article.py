"""导出文章用例"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from ...domain.entities import Article
from ...shared.exceptions import UseCaseError

if TYPE_CHECKING:
    from ..ports.outbound import ExporterPort


class ExportArticleUseCase:
    """
    导出文章用例

    负责协调导出器来导出文章。
    """

    def __init__(self, exporters: dict[str, ExporterPort]):
        """
        Args:
            exporters: 导出器字典 {target_name: exporter}
        """
        self._exporters = exporters

    def execute(
        self,
        article: Article,
        target: str,
        path: str | None = None,
        **options,
    ) -> str:
        """
        执行导出文章用例

        Args:
            article: 文章实体
            target: 导出目标 (html, markdown, onenote, notion, obsidian)
            path: 导出路径（文件导出时使用）
            **options: 额外选项

        Returns:
            导出结果（文件路径或成功消息）

        Raises:
            UseCaseError: 导出失败
        """
        # 获取导出器
        exporter = self._get_exporter(target)
        if exporter is None:
            raise UseCaseError(f"未找到导出目标: {target}")

        if not exporter.is_available():
            raise UseCaseError(f"导出器 {target} 不可用")

        # 执行导出
        logger.info(f"导出文章到 {target}: {article.title}")

        try:
            result = exporter.export(article, path=path, **options)
            logger.info(f"导出成功: {result}")
            return result

        except Exception as e:
            logger.error(f"导出失败: {e}")
            raise UseCaseError(f"导出失败: {e}") from e

    def _get_exporter(self, target: str) -> ExporterPort | None:
        """获取导出器"""
        return self._exporters.get(target)

    def list_available_targets(self) -> list[str]:
        """列出可用的导出目标"""
        return [name for name, exporter in self._exporters.items() if exporter.is_available()]
