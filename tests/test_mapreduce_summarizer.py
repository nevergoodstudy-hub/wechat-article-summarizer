"""MapReduce 摘要器测试

测试 MapReduceSummarizer 的分块和合并功能。
"""

import pytest

from wechat_summarizer.domain.entities import Summary, SummaryMethod, SummaryStyle
from wechat_summarizer.domain.value_objects import ArticleContent
from wechat_summarizer.infrastructure.adapters.summarizers import (
    MapReduceSummarizer,
    SimpleSummarizer,
)


class TestMapReduceSummarizer:
    """MapReduce 摘要器测试"""

    @pytest.fixture
    def base_summarizer(self) -> SimpleSummarizer:
        """创建基础摘要器"""
        return SimpleSummarizer()

    @pytest.fixture
    def mapreduce_summarizer(self, base_summarizer: SimpleSummarizer) -> MapReduceSummarizer:
        """创建 MapReduce 摘要器"""
        return MapReduceSummarizer(
            base_summarizer=base_summarizer,
            chunk_size=500,  # 小块大小便于测试
            overlap=50,
            max_chunks=10,
        )

    @pytest.mark.unit
    def test_summarizer_properties(self, mapreduce_summarizer: MapReduceSummarizer) -> None:
        """测试摘要器属性"""
        assert mapreduce_summarizer.name == "mapreduce-simple"
        assert mapreduce_summarizer.method == SummaryMethod.SIMPLE
        assert mapreduce_summarizer.is_available() is True

    @pytest.mark.unit
    def test_short_text_direct_summarize(
        self, mapreduce_summarizer: MapReduceSummarizer
    ) -> None:
        """测试短文本直接摘要（不分块）"""
        short_text = "这是一段短文本，不需要分块处理。" * 5
        content = ArticleContent(text=short_text)

        summary = mapreduce_summarizer.summarize(content)

        assert isinstance(summary, Summary)
        assert summary.content
        assert summary.method == SummaryMethod.SIMPLE

    @pytest.mark.unit
    def test_long_text_chunk_split(self, mapreduce_summarizer: MapReduceSummarizer) -> None:
        """测试长文本分块"""
        # 创建超过 chunk_size 的长文本
        long_text = "这是一段测试文本。" * 200  # 约 2000 字符
        content = ArticleContent(text=long_text)

        summary = mapreduce_summarizer.summarize(content)

        assert isinstance(summary, Summary)
        assert summary.content
        # MapReduce 处理后应该有模型名称标记
        assert "mapreduce" in (summary.model_name or "")

    @pytest.mark.unit
    def test_chunk_split_logic(self, mapreduce_summarizer: MapReduceSummarizer) -> None:
        """测试分块逻辑"""
        # 创建带段落的长文本
        paragraphs = ["这是第一段内容。" * 30 for _ in range(5)]
        long_text = "\n\n".join(paragraphs)

        chunks = mapreduce_summarizer._split_into_chunks(long_text)

        assert len(chunks) > 1
        # 每个块不应超过 chunk_size（加上一定容差）
        for chunk in chunks:
            assert len(chunk) <= mapreduce_summarizer._chunk_size + 200

    @pytest.mark.unit
    def test_max_chunks_limit(self, base_summarizer: SimpleSummarizer) -> None:
        """测试最大块数限制"""
        summarizer = MapReduceSummarizer(
            base_summarizer=base_summarizer,
            chunk_size=100,
            overlap=10,
            max_chunks=3,  # 限制最多 3 块
        )

        # 创建非常长的文本
        very_long_text = "这是测试内容。" * 500

        chunks = summarizer._split_into_chunks(very_long_text)

        assert len(chunks) <= 3

    @pytest.mark.unit
    def test_unavailable_base_summarizer(self) -> None:
        """测试基础摘要器不可用时的行为"""

        class UnavailableSummarizer(SimpleSummarizer):
            def is_available(self) -> bool:
                return False

        summarizer = MapReduceSummarizer(
            base_summarizer=UnavailableSummarizer(),
        )

        assert summarizer.is_available() is False

    @pytest.mark.unit
    def test_merge_key_points(self, mapreduce_summarizer: MapReduceSummarizer) -> None:
        """测试关键点合并去重"""
        points = [
            "人工智能正在改变世界",
            "AI正在改变世界",  # 不同表述
            "人工智能正在改变世界",  # 重复
            "机器学习是AI的子领域",
        ]

        merged = mapreduce_summarizer._merge_key_points(points)

        # 应该去除完全相同的重复项
        assert len(merged) < len(points)
        assert "人工智能正在改变世界" in merged

    @pytest.mark.unit
    def test_merge_tags(self, mapreduce_summarizer: MapReduceSummarizer) -> None:
        """测试标签合并去重"""
        tags = ["AI", "ai", "人工智能", "AI", "机器学习"]

        merged = mapreduce_summarizer._merge_tags(tags)

        # 应该去除重复标签（大小写不敏感）
        assert len(merged) == 3  # AI, 人工智能, 机器学习


class TestMapReduceIntegration:
    """MapReduce 集成测试"""

    @pytest.mark.integration
    def test_container_has_mapreduce_summarizers(self) -> None:
        """测试容器中包含 MapReduce 摘要器"""
        from wechat_summarizer.infrastructure.config import get_container, reset_container

        reset_container()
        container = get_container()
        summarizers = container.summarizers

        # 如果有可用的 LLM 摘要器，应该有对应的 MapReduce 版本
        llm_names = ["openai", "anthropic", "zhipu", "deepseek", "ollama"]
        for name in llm_names:
            if name in summarizers and summarizers[name].is_available():
                mr_name = f"mapreduce-{name}"
                assert mr_name in summarizers, f"缺少 MapReduce 摘要器: {mr_name}"
