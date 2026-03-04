"""ExportArticleUseCase 导出文章用例测试

测试导出用例的核心逻辑：目标查找、可用性检查、异常处理。
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from wechat_summarizer.application.use_cases.export_article import ExportArticleUseCase
from wechat_summarizer.domain.entities import Article
from wechat_summarizer.shared.exceptions import UseCaseError


class TestExportArticleUseCase:
    """ExportArticleUseCase 测试"""

    @pytest.fixture
    def mock_html_exporter(self, tmp_path: Path) -> Mock:
        exporter = Mock()
        exporter.name = "html"
        exporter.target = "html"
        exporter.is_available.return_value = True
        exporter.export.return_value = str(tmp_path / "article.html")
        return exporter

    @pytest.fixture
    def mock_markdown_exporter(self, tmp_path: Path) -> Mock:
        exporter = Mock()
        exporter.name = "markdown"
        exporter.target = "markdown"
        exporter.is_available.return_value = True
        exporter.export.return_value = str(tmp_path / "article.md")
        return exporter

    @pytest.fixture
    def mock_unavailable_exporter(self) -> Mock:
        exporter = Mock()
        exporter.name = "onenote"
        exporter.target = "onenote"
        exporter.is_available.return_value = False
        return exporter

    @pytest.fixture
    def use_case(
        self,
        mock_html_exporter: Mock,
        mock_markdown_exporter: Mock,
        mock_unavailable_exporter: Mock,
    ) -> ExportArticleUseCase:
        return ExportArticleUseCase(
            exporters={
                "html": mock_html_exporter,
                "markdown": mock_markdown_exporter,
                "onenote": mock_unavailable_exporter,
            }
        )

    # ---- 正常导出 ----

    @pytest.mark.unit
    def test_export_html(
        self, use_case: ExportArticleUseCase, sample_article: Article, mock_html_exporter: Mock
    ) -> None:
        """导出 HTML 成功"""
        result = use_case.execute(sample_article, "html")

        assert "article.html" in result
        mock_html_exporter.export.assert_called_once()

    @pytest.mark.unit
    def test_export_markdown(
        self,
        use_case: ExportArticleUseCase,
        sample_article: Article,
        mock_markdown_exporter: Mock,
    ) -> None:
        """导出 Markdown 成功"""
        result = use_case.execute(sample_article, "markdown")

        assert "article.md" in result
        mock_markdown_exporter.export.assert_called_once()

    @pytest.mark.unit
    def test_export_with_path(
        self,
        use_case: ExportArticleUseCase,
        sample_article: Article,
        mock_html_exporter: Mock,
        tmp_path: Path,
    ) -> None:
        """导出时传递路径参数"""
        use_case.execute(sample_article, "html", path=str(tmp_path))

        call_kwargs = mock_html_exporter.export.call_args
        assert call_kwargs.kwargs.get("path") == str(tmp_path)

    # ---- 异常处理 ----

    @pytest.mark.unit
    def test_export_unknown_target_raises(
        self, use_case: ExportArticleUseCase, sample_article: Article
    ) -> None:
        """导出不存在的目标引发 UseCaseError"""
        with pytest.raises(UseCaseError, match="未找到导出目标"):
            use_case.execute(sample_article, "notion")

    @pytest.mark.unit
    def test_export_unavailable_target_raises(
        self, use_case: ExportArticleUseCase, sample_article: Article
    ) -> None:
        """导出不可用的目标引发 UseCaseError"""
        with pytest.raises(UseCaseError, match="不可用"):
            use_case.execute(sample_article, "onenote")

    @pytest.mark.unit
    def test_export_failure_raises_use_case_error(
        self,
        use_case: ExportArticleUseCase,
        sample_article: Article,
        mock_html_exporter: Mock,
    ) -> None:
        """导出器内部异常被包装为 UseCaseError"""
        mock_html_exporter.export.side_effect = RuntimeError("disk full")

        with pytest.raises(UseCaseError, match="导出失败"):
            use_case.execute(sample_article, "html")

    @pytest.mark.unit
    def test_export_failure_chains_original_exception(
        self,
        use_case: ExportArticleUseCase,
        sample_article: Article,
        mock_html_exporter: Mock,
    ) -> None:
        """导出异常链保留原始异常"""
        original = RuntimeError("原始错误")
        mock_html_exporter.export.side_effect = original

        with pytest.raises(UseCaseError) as exc_info:
            use_case.execute(sample_article, "html")

        assert exc_info.value.__cause__ is original

    # ---- list_available_targets ----

    @pytest.mark.unit
    def test_list_available_targets(self, use_case: ExportArticleUseCase) -> None:
        """列出可用的导出目标"""
        targets = use_case.list_available_targets()

        assert "html" in targets
        assert "markdown" in targets
        assert "onenote" not in targets  # 不可用

    @pytest.mark.unit
    def test_list_available_targets_empty(self) -> None:
        """无导出器时返回空列表"""
        use_case = ExportArticleUseCase(exporters={})
        assert use_case.list_available_targets() == []
