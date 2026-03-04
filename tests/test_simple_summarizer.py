"""SimpleSummarizer 单元测试

测试简单规则摘要器的各种功能：
- summarize() with concise style
- summarize() with bullet_points style
- _extract_tags()
- _extract_key_points()
"""

from __future__ import annotations

import pytest

from wechat_summarizer.domain.entities.summary import SummaryMethod, SummaryStyle
from wechat_summarizer.domain.value_objects import ArticleContent
from wechat_summarizer.infrastructure.adapters.summarizers.simple import SimpleSummarizer


@pytest.mark.unit
class TestSimpleSummarizer:
    """SimpleSummarizer 测试类"""

    @pytest.fixture
    def summarizer(self) -> SimpleSummarizer:
        """创建 SimpleSummarizer 实例"""
        return SimpleSummarizer()

    @pytest.fixture
    def chinese_content(self) -> ArticleContent:
        """中文文章内容 fixture"""
        text = """人工智能正在改变我们的生活方式。

首先，AI 技术已经广泛应用于医疗诊断领域。

其次，自动驾驶汽车正在逐步走向商业化。

总之，人工智能将继续推动社会进步。

1. 医疗AI诊断准确率提高
2. 自动驾驶技术成熟
3. 智能家居普及

重要的是，我们需要关注AI的伦理问题。"""
        return ArticleContent.from_text(text)

    @pytest.fixture
    def short_content(self) -> ArticleContent:
        """短文章内容 fixture"""
        text = "这是一篇很短的测试文章。"
        return ArticleContent.from_text(text)

    def test_summarizer_name(self, summarizer: SimpleSummarizer) -> None:
        """测试摘要器名称"""
        assert summarizer.name == "simple"

    def test_summarizer_method(self, summarizer: SimpleSummarizer) -> None:
        """测试摘要器方法"""
        assert summarizer.method == SummaryMethod.SIMPLE

    def test_summarizer_is_available(self, summarizer: SimpleSummarizer) -> None:
        """测试摘要器始终可用"""
        assert summarizer.is_available() is True

    def test_summarize_concise_style(
        self, summarizer: SimpleSummarizer, chinese_content: ArticleContent
    ) -> None:
        """测试 concise 风格摘要"""
        summary = summarizer.summarize(
            chinese_content,
            style=SummaryStyle.CONCISE,
            max_length=500,
        )

        assert summary.content is not None
        assert len(summary.content) > 0
        assert summary.method == SummaryMethod.SIMPLE
        assert summary.style == SummaryStyle.CONCISE
        # 摘要应该从第一段开始
        assert "人工智能" in summary.content

    def test_summarize_bullet_points_style(
        self, summarizer: SimpleSummarizer, chinese_content: ArticleContent
    ) -> None:
        """测试 bullet_points 风格摘要"""
        summary = summarizer.summarize(
            chinese_content,
            style=SummaryStyle.BULLET_POINTS,
            max_length=500,
        )

        assert summary.content is not None
        assert len(summary.content) > 0
        assert summary.method == SummaryMethod.SIMPLE
        assert summary.style == SummaryStyle.BULLET_POINTS
        # bullet_points 风格应提取关键句（包含关键词如"首先"、"总之"等）

    def test_summarize_with_sample_content_fixture(
        self, summarizer: SimpleSummarizer, sample_content: ArticleContent
    ) -> None:
        """测试使用 conftest.py 中的 sample_content fixture"""
        summary = summarizer.summarize(sample_content, style=SummaryStyle.CONCISE)

        assert summary.content is not None
        assert summary.method == SummaryMethod.SIMPLE
        assert isinstance(summary.key_points, tuple)
        assert isinstance(summary.tags, tuple)

    def test_summarize_respects_max_length(
        self, summarizer: SimpleSummarizer, chinese_content: ArticleContent
    ) -> None:
        """测试摘要长度限制"""
        max_length = 50
        summary = summarizer.summarize(
            chinese_content,
            style=SummaryStyle.CONCISE,
            max_length=max_length,
        )

        # 摘要内容应该在合理范围内（可能略超因为不截断单词）
        assert len(summary.content) <= max_length + 50

    def test_summarize_extracts_key_points(
        self, summarizer: SimpleSummarizer, chinese_content: ArticleContent
    ) -> None:
        """测试关键点提取"""
        summary = summarizer.summarize(chinese_content, style=SummaryStyle.CONCISE)

        assert isinstance(summary.key_points, tuple)
        # 应该提取到列表项（1. 2. 3.）
        assert len(summary.key_points) > 0

    def test_summarize_extracts_tags(
        self, summarizer: SimpleSummarizer, chinese_content: ArticleContent
    ) -> None:
        """测试标签提取"""
        summary = summarizer.summarize(chinese_content, style=SummaryStyle.CONCISE)

        assert isinstance(summary.tags, tuple)
        assert len(summary.tags) > 0
        # 应该提取到高频中文词汇

    def test_extract_tags_directly(self, summarizer: SimpleSummarizer) -> None:
        """直接测试 _extract_tags 方法"""
        text = "人工智能人工智能人工智能机器学习机器学习深度学习"
        tags = summarizer._extract_tags(text, max_tags=3)

        assert isinstance(tags, list)
        assert len(tags) <= 3
        # 人工智能出现次数最多，应该排在前面
        assert "人工智能" in tags

    def test_extract_tags_filters_stopwords(self, summarizer: SimpleSummarizer) -> None:
        """测试 _extract_tags 过滤停用词"""
        text = "的的的是是是在在有有和和与与"
        tags = summarizer._extract_tags(text, max_tags=5)

        # 停用词应被过滤
        assert "的" not in tags
        assert "是" not in tags

    def test_extract_key_points_from_numbered_list(self, summarizer: SimpleSummarizer) -> None:
        """测试从编号列表提取关键点"""
        paragraphs = [
            "1. 第一个要点",
            "2. 第二个要点",
            "3. 第三个要点",
            "这是普通段落",
        ]
        key_points = summarizer._extract_key_points(paragraphs, max_points=5)

        assert len(key_points) == 3
        assert "第一个要点" in key_points
        assert "第二个要点" in key_points
        assert "第三个要点" in key_points

    def test_extract_key_points_from_chinese_numbers(self, summarizer: SimpleSummarizer) -> None:
        """测试从中文编号列表提取关键点"""
        paragraphs = [
            "一、第一个要点",
            "二、第二个要点",
            "三、第三个要点",
        ]
        key_points = summarizer._extract_key_points(paragraphs, max_points=5)

        assert len(key_points) == 3

    def test_extract_key_points_fallback_to_first_sentences(
        self, summarizer: SimpleSummarizer
    ) -> None:
        """测试没有编号时回退到首句提取"""
        paragraphs = [
            "这是第一段的首句。这是第一段的第二句。",
            "这是第二段的首句。这是第二段的第二句。",
        ]
        key_points = summarizer._extract_key_points(paragraphs, max_points=5)

        assert len(key_points) >= 1
        assert "这是第一段的首句" in key_points

    def test_summarize_short_content(
        self, summarizer: SimpleSummarizer, short_content: ArticleContent
    ) -> None:
        """测试短文章摘要"""
        summary = summarizer.summarize(short_content, style=SummaryStyle.CONCISE)

        assert summary.content is not None
        # 短文章应直接作为摘要
        assert "测试文章" in summary.content

    def test_summarize_empty_paragraphs_handling(self, summarizer: SimpleSummarizer) -> None:
        """测试空段落处理"""
        text = """

第一段内容


第二段内容

"""
        content = ArticleContent.from_text(text)
        summary = summarizer.summarize(content, style=SummaryStyle.CONCISE)

        assert summary.content is not None
        assert "第一段内容" in summary.content

    def test_bullet_points_fallback_when_no_keywords(self, summarizer: SimpleSummarizer) -> None:
        """测试 bullet_points 风格在没有关键词时的回退"""
        text = "这是没有任何关键词的普通文本段落。"
        content = ArticleContent.from_text(text)
        summary = summarizer.summarize(
            content,
            style=SummaryStyle.BULLET_POINTS,
            max_length=500,
        )

        # 应该回退到提取前几段
        assert summary.content is not None
        assert len(summary.content) > 0
