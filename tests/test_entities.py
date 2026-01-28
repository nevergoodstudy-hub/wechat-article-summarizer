"""领域实体测试

测试 Article 和 Summary 实体的核心行为。
"""

from datetime import datetime
from uuid import uuid4

import pytest

from wechat_summarizer.domain.entities import Article, Summary
from wechat_summarizer.domain.entities.summary import SummaryMethod, SummaryStyle
from wechat_summarizer.domain.value_objects import ArticleContent, ArticleURL


class TestArticleEntity:
    """Article 实体测试"""

    @pytest.mark.unit
    def test_create_article_with_minimal_fields(self, sample_wechat_url: ArticleURL) -> None:
        """测试创建只有必填字段的文章"""
        article = Article(
            url=sample_wechat_url,
            title="测试标题",
        )

        assert article.url == sample_wechat_url
        assert article.title == "测试标题"
        assert article.id is not None
        assert article.author is None
        assert article.content is None
        assert article.summary is None

    @pytest.mark.unit
    def test_create_article_with_all_fields(
        self, sample_wechat_url: ArticleURL, sample_content: ArticleContent
    ) -> None:
        """测试创建完整字段的文章"""
        article_id = uuid4()
        publish_time = datetime(2024, 1, 15, 10, 30, 0)

        article = Article(
            id=article_id,
            url=sample_wechat_url,
            title="完整测试标题",
            author="测试作者",
            account_name="测试公众号",
            publish_time=publish_time,
            content=sample_content,
        )

        assert article.id == article_id
        assert article.title == "完整测试标题"
        assert article.author == "测试作者"
        assert article.account_name == "测试公众号"
        assert article.publish_time == publish_time
        assert article.content == sample_content

    @pytest.mark.unit
    def test_article_content_text_property(self, sample_article: Article) -> None:
        """测试文章内容文本属性"""
        text = sample_article.content_text
        assert text is not None
        assert "测试文章" in text

    @pytest.mark.unit
    def test_article_content_html_property(self, sample_article: Article) -> None:
        """测试文章内容 HTML 属性"""
        html = sample_article.content_html
        assert html is not None
        assert "<p>" in html or "测试" in html

    @pytest.mark.unit
    def test_article_word_count(self, sample_article: Article) -> None:
        """测试文章字数统计"""
        word_count = sample_article.word_count
        assert word_count > 0

    @pytest.mark.unit
    def test_attach_summary_to_article(
        self, sample_article: Article, sample_summary: Summary
    ) -> None:
        """测试为文章添加摘要"""
        assert sample_article.summary is None

        sample_article.attach_summary(sample_summary)

        assert sample_article.summary is not None
        assert sample_article.summary.content == sample_summary.content

    @pytest.mark.unit
    def test_update_article_content(
        self, sample_article: Article, sample_content: ArticleContent
    ) -> None:
        """测试更新文章内容"""
        new_content = ArticleContent.from_text("新的文章内容")
        original_updated_at = sample_article.updated_at

        sample_article.update_content(new_content)

        assert sample_article.content == new_content
        assert sample_article.updated_at >= original_updated_at

    @pytest.mark.unit
    def test_article_without_content_returns_empty(
        self, sample_wechat_url: ArticleURL
    ) -> None:
        """测试无内容文章返回空字符串"""
        article = Article(url=sample_wechat_url, title="无内容")

        assert article.content_text == ""
        assert article.content_html == ""
        assert article.word_count == 0


class TestSummaryEntity:
    """Summary 实体测试"""

    @pytest.mark.unit
    def test_create_summary_with_minimal_fields(self) -> None:
        """测试创建只有必填字段的摘要"""
        summary = Summary(content="这是摘要内容")

        assert summary.content == "这是摘要内容"
        assert summary.key_points == ()
        assert summary.tags == ()
        assert summary.method == SummaryMethod.SIMPLE
        assert summary.style == SummaryStyle.CONCISE

    @pytest.mark.unit
    def test_create_summary_with_all_fields(self) -> None:
        """测试创建完整字段的摘要"""
        summary = Summary(
            content="完整摘要内容",
            key_points=("要点1", "要点2", "要点3"),
            tags=("标签1", "标签2"),
            method=SummaryMethod.OPENAI,
            style=SummaryStyle.DETAILED,
            model_name="gpt-4",
            input_tokens=100,
            output_tokens=50,
        )

        assert summary.content == "完整摘要内容"
        assert len(summary.key_points) == 3
        assert len(summary.tags) == 2
        assert summary.method == SummaryMethod.OPENAI
        assert summary.style == SummaryStyle.DETAILED
        assert summary.model_name == "gpt-4"
        assert summary.input_tokens == 100
        assert summary.output_tokens == 50
        assert summary.total_tokens == 150

    @pytest.mark.unit
    def test_summary_with_key_points(self, sample_summary: Summary) -> None:
        """测试摘要关键要点"""
        new_summary = sample_summary.with_key_points(("新要点1", "新要点2"))

        assert len(new_summary.key_points) == 2
        assert "新要点1" in new_summary.key_points
        assert sample_summary.content == new_summary.content

    @pytest.mark.unit
    def test_summary_with_tags(self, sample_summary: Summary) -> None:
        """测试摘要标签"""
        new_summary = sample_summary.with_tags(("新标签1", "新标签2", "新标签3"))

        assert len(new_summary.tags) == 3
        assert "新标签1" in new_summary.tags
        assert sample_summary.content == new_summary.content

    @pytest.mark.unit
    def test_summary_immutability(self, sample_summary: Summary) -> None:
        """测试摘要不可变性"""
        original_content = sample_summary.content
        _ = sample_summary.with_key_points(("修改后要点",))

        assert sample_summary.content == original_content

    @pytest.mark.unit
    def test_summary_method_enum_values(self) -> None:
        """测试摘要方法枚举值"""
        assert SummaryMethod.SIMPLE.value == "simple"
        assert SummaryMethod.OPENAI.value == "openai"
        assert SummaryMethod.ANTHROPIC.value == "anthropic"
        assert SummaryMethod.OLLAMA.value == "ollama"
        assert SummaryMethod.ZHIPU.value == "zhipu"

    @pytest.mark.unit
    def test_summary_style_enum_values(self) -> None:
        """测试摘要风格枚举值"""
        assert SummaryStyle.CONCISE.value == "concise"
        assert SummaryStyle.DETAILED.value == "detailed"
        assert SummaryStyle.BULLET_POINTS.value == "bullet"
