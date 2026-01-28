"""用例层测试

测试 FetchArticleUseCase、SummarizeArticleUseCase、ExportArticleUseCase 等用例。
"""

from unittest.mock import Mock, MagicMock
from uuid import uuid4
from datetime import datetime

import pytest

from wechat_summarizer.application.use_cases import (
    FetchArticleUseCase,
    SummarizeArticleUseCase,
    ExportArticleUseCase,
)
from wechat_summarizer.domain.entities import Article, Summary
from wechat_summarizer.domain.entities.summary import SummaryMethod, SummaryStyle
from wechat_summarizer.domain.value_objects import ArticleURL, ArticleContent
from wechat_summarizer.shared.exceptions import UseCaseError, ScraperError


class TestFetchArticleUseCase:
    """FetchArticleUseCase 测试"""

    @pytest.mark.unit
    def test_execute_with_valid_url(self, sample_article: Article) -> None:
        """测试正常抓取流程"""
        mock_scraper = Mock()
        mock_scraper.name = "mock_scraper"
        mock_scraper.can_handle.return_value = True
        mock_scraper.scrape.return_value = sample_article

        use_case = FetchArticleUseCase([mock_scraper])
        article = use_case.execute("https://mp.weixin.qq.com/s/test")

        assert article.title == sample_article.title
        mock_scraper.scrape.assert_called_once()

    @pytest.mark.unit
    def test_execute_with_cache_hit(self, sample_article: Article) -> None:
        """测试缓存命中"""
        mock_scraper = Mock()
        mock_scraper.name = "mock_scraper"

        mock_storage = Mock()
        mock_storage.get_by_url.return_value = sample_article

        use_case = FetchArticleUseCase([mock_scraper], storage=mock_storage)
        article = use_case.execute("https://mp.weixin.qq.com/s/test")

        assert article == sample_article
        mock_scraper.scrape.assert_not_called()  # 不应调用抓取器

    @pytest.mark.unit
    def test_execute_with_cache_miss(self, sample_article: Article) -> None:
        """测试缓存未命中"""
        mock_scraper = Mock()
        mock_scraper.name = "mock_scraper"
        mock_scraper.can_handle.return_value = True
        mock_scraper.scrape.return_value = sample_article

        mock_storage = Mock()
        mock_storage.get_by_url.return_value = None

        use_case = FetchArticleUseCase([mock_scraper], storage=mock_storage)
        article = use_case.execute("https://mp.weixin.qq.com/s/test")

        assert article == sample_article
        mock_scraper.scrape.assert_called_once()
        mock_storage.save.assert_called_once()

    @pytest.mark.unit
    def test_execute_with_invalid_url(self) -> None:
        """测试无效 URL"""
        mock_scraper = Mock()
        use_case = FetchArticleUseCase([mock_scraper])

        # 使用空URL触发无效URL错误
        with pytest.raises(UseCaseError, match="无效的URL"):
            use_case.execute("")

    @pytest.mark.unit
    def test_execute_with_private_ip_url(self) -> None:
        """测试私有IP URL（SSRF防护）"""
        mock_scraper = Mock()
        use_case = FetchArticleUseCase([mock_scraper])

        with pytest.raises(UseCaseError, match="无效的URL"):
            use_case.execute("http://192.168.1.1/internal")

    @pytest.mark.unit
    def test_execute_preferred_scraper(self, sample_article: Article) -> None:
        """测试指定抓取器"""
        mock_scraper1 = Mock()
        mock_scraper1.name = "scraper1"

        mock_scraper2 = Mock()
        mock_scraper2.name = "scraper2"
        mock_scraper2.scrape.return_value = sample_article

        use_case = FetchArticleUseCase([mock_scraper1, mock_scraper2])
        article = use_case.execute(
            "https://mp.weixin.qq.com/s/test",
            preferred_scraper="scraper2",
        )

        assert article == sample_article
        mock_scraper1.scrape.assert_not_called()
        mock_scraper2.scrape.assert_called_once()

    @pytest.mark.unit
    def test_execute_fallback_on_scraper_error(self, sample_article: Article) -> None:
        """测试抓取器失败时回退到下一个"""
        mock_scraper1 = Mock()
        mock_scraper1.name = "scraper1"
        mock_scraper1.can_handle.return_value = True
        mock_scraper1.scrape.side_effect = ScraperError("模拟失败")

        mock_scraper2 = Mock()
        mock_scraper2.name = "scraper2"
        mock_scraper2.can_handle.return_value = True
        mock_scraper2.scrape.return_value = sample_article

        use_case = FetchArticleUseCase([mock_scraper1, mock_scraper2])
        article = use_case.execute("https://mp.weixin.qq.com/s/test")

        assert article == sample_article
        mock_scraper1.scrape.assert_called_once()
        mock_scraper2.scrape.assert_called_once()

    @pytest.mark.unit
    def test_execute_no_available_scraper(self) -> None:
        """测试没有可用抓取器"""
        mock_scraper = Mock()
        mock_scraper.name = "mock_scraper"
        mock_scraper.can_handle.return_value = False

        use_case = FetchArticleUseCase([mock_scraper])

        with pytest.raises(UseCaseError, match="没有可用的抓取器"):
            use_case.execute("https://mp.weixin.qq.com/s/test")


class TestSummarizeArticleUseCase:
    """SummarizeArticleUseCase 测试"""

    @pytest.mark.unit
    def test_execute_with_valid_article(
        self, sample_article: Article, sample_summary: Summary
    ) -> None:
        """测试正常摘要流程"""
        mock_summarizer = Mock()
        mock_summarizer.name = "mock"
        mock_summarizer.is_available.return_value = True
        mock_summarizer.summarize.return_value = sample_summary

        use_case = SummarizeArticleUseCase({"mock": mock_summarizer})
        summary = use_case.execute(sample_article, method="mock")

        assert summary.content == sample_summary.content
        mock_summarizer.summarize.assert_called_once()

    @pytest.mark.unit
    def test_execute_default_method(
        self, sample_article: Article, sample_summary: Summary
    ) -> None:
        """测试默认摘要方法"""
        mock_simple = Mock()
        mock_simple.name = "simple"
        mock_simple.is_available.return_value = True
        mock_simple.summarize.return_value = sample_summary

        use_case = SummarizeArticleUseCase({"simple": mock_simple})
        summary = use_case.execute(sample_article)  # 不指定method，使用默认

        assert summary.content == sample_summary.content

    @pytest.mark.unit
    def test_execute_unavailable_method(self, sample_article: Article) -> None:
        """测试摘要方法不可用"""
        mock_summarizer = Mock()
        mock_summarizer.name = "openai"
        mock_summarizer.is_available.return_value = False

        use_case = SummarizeArticleUseCase({"openai": mock_summarizer})

        with pytest.raises(UseCaseError, match="不可用"):
            use_case.execute(sample_article, method="openai")

    @pytest.mark.unit
    def test_execute_unknown_method(self, sample_article: Article) -> None:
        """测试未知摘要方法"""
        use_case = SummarizeArticleUseCase({})

        with pytest.raises(UseCaseError, match="未找到"):
            use_case.execute(sample_article, method="unknown")


class TestExportArticleUseCase:
    """ExportArticleUseCase 测试"""

    @pytest.mark.unit
    def test_execute_with_valid_article(
        self, article_with_summary: Article, tmp_path
    ) -> None:
        """测试正常导出流程"""
        output_file = tmp_path / "output.html"

        mock_exporter = Mock()
        mock_exporter.name = "html"
        mock_exporter.is_available.return_value = True
        mock_exporter.export.return_value = str(output_file)

        use_case = ExportArticleUseCase({"html": mock_exporter})
        result = use_case.execute(article_with_summary, target="html")

        assert result == str(output_file)
        mock_exporter.export.assert_called_once()

    @pytest.mark.unit
    def test_execute_unknown_target(self, article_with_summary: Article) -> None:
        """测试未知导出目标"""
        use_case = ExportArticleUseCase({})

        with pytest.raises(UseCaseError, match="未找到"):
            use_case.execute(article_with_summary, target="unknown")

    @pytest.mark.unit
    def test_execute_unavailable_exporter(self, article_with_summary: Article) -> None:
        """测试导出器不可用"""
        mock_exporter = Mock()
        mock_exporter.name = "notion"
        mock_exporter.is_available.return_value = False

        use_case = ExportArticleUseCase({"notion": mock_exporter})

        with pytest.raises(UseCaseError, match="不可用"):
            use_case.execute(article_with_summary, target="notion")
