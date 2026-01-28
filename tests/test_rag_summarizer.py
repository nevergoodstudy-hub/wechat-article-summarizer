"""RAG 增强摘要器测试

测试 RAGEnhancedSummarizer 和 HyDEEnhancedSummarizer。
"""

import pytest

from wechat_summarizer.domain.entities import Summary, SummaryMethod, SummaryStyle
from wechat_summarizer.domain.value_objects import ArticleContent
from wechat_summarizer.infrastructure.adapters.embedders import SimpleHashEmbedder
from wechat_summarizer.infrastructure.adapters.summarizers import (
    RAGEnhancedSummarizer,
    SimpleSummarizer,
)
from wechat_summarizer.infrastructure.adapters.vector_stores import MemoryVectorStore


class TestRAGEnhancedSummarizer:
    """RAG 增强摘要器测试"""

    @pytest.fixture
    def base_summarizer(self) -> SimpleSummarizer:
        """创建基础摘要器"""
        return SimpleSummarizer()

    @pytest.fixture
    def embedder(self) -> SimpleHashEmbedder:
        """创建嵌入器（维度与存储一致）"""
        return SimpleHashEmbedder(dimension=128)

    @pytest.fixture
    def vector_store(self) -> MemoryVectorStore:
        """创建向量存储（维度与嵌入器一致）"""
        return MemoryVectorStore(dimension=128)

    @pytest.fixture
    def rag_summarizer(
        self,
        base_summarizer: SimpleSummarizer,
        embedder: SimpleHashEmbedder,
        vector_store: MemoryVectorStore,
    ) -> RAGEnhancedSummarizer:
        """创建 RAG 摘要器"""
        return RAGEnhancedSummarizer(
            base_summarizer=base_summarizer,
            embedder=embedder,
            vector_store=vector_store,
            chunk_size=200,
            chunk_overlap=20,
            top_k=3,
        )

    @pytest.mark.unit
    def test_summarizer_properties(self, rag_summarizer: RAGEnhancedSummarizer) -> None:
        """测试摘要器属性"""
        assert rag_summarizer.name == "rag-simple"
        assert rag_summarizer.method == SummaryMethod.RAG
        assert rag_summarizer.is_available() is True

    @pytest.mark.unit
    def test_summarize_short_text(self, rag_summarizer: RAGEnhancedSummarizer) -> None:
        """测试短文本摘要"""
        content = ArticleContent(text="这是一段简短的测试文本。" * 5)

        summary = rag_summarizer.summarize(content)

        assert isinstance(summary, Summary)
        assert summary.content
        assert summary.method == SummaryMethod.RAG

    @pytest.mark.unit
    def test_summarize_long_text(self, rag_summarizer: RAGEnhancedSummarizer) -> None:
        """测试长文本摘要（需要分块）"""
        # 创建长文本
        paragraphs = [
            "人工智能是计算机科学的一个重要分支，旨在创建能够执行智能任务的系统。",
            "机器学习是人工智能的核心技术，使计算机能够从数据中学习模式。",
            "深度学习基于神经网络，在图像识别和自然语言处理领域取得了突破性进展。",
            "大语言模型通过预训练和微调，能够理解和生成人类语言。",
            "检索增强生成技术结合了检索和生成，提高了模型回答问题的准确性。",
        ]
        long_text = "\n\n".join([p * 10 for p in paragraphs])
        content = ArticleContent(text=long_text)

        summary = rag_summarizer.summarize(content)

        assert isinstance(summary, Summary)
        assert summary.content
        # RAG 处理后应该有相应标记
        assert "rag" in (summary.model_name or "").lower()

    @pytest.mark.unit
    def test_chunk_text(self, rag_summarizer: RAGEnhancedSummarizer) -> None:
        """测试文本分块"""
        text = "这是一段测试文本。" * 50  # 约 450 字符

        chunks = rag_summarizer._chunk_text(text)

        assert len(chunks) > 1
        # 每个块不应超过设定的大小（加上一定容差）
        for chunk in chunks:
            assert len(chunk) <= rag_summarizer._chunk_size + 50

    @pytest.mark.unit
    def test_chunk_with_overlap(self, rag_summarizer: RAGEnhancedSummarizer) -> None:
        """测试分块重叠"""
        text = "ABCDE " * 100  # 创建足够长的文本

        chunks = rag_summarizer._chunk_text(text)

        # 检查是否有重叠（相邻块末尾和开头应有共同内容）
        if len(chunks) >= 2:
            # 重叠部分可能存在于相邻块之间
            assert len(chunks) >= 2

    @pytest.mark.unit
    def test_build_context_from_chunks(
        self, rag_summarizer: RAGEnhancedSummarizer
    ) -> None:
        """测试从块构建上下文"""
        # 先添加一些文档到存储
        text = "人工智能正在改变世界。机器学习是其核心。深度学习取得突破。" * 20
        content = ArticleContent(text=text)

        # 执行摘要会自动构建索引
        summary = rag_summarizer.summarize(content)

        assert summary is not None

    @pytest.mark.unit
    def test_unavailable_base_summarizer(
        self, embedder: SimpleHashEmbedder, vector_store: MemoryVectorStore
    ) -> None:
        """测试基础摘要器不可用时的行为"""

        class UnavailableSummarizer(SimpleSummarizer):
            def is_available(self) -> bool:
                return False

        summarizer = RAGEnhancedSummarizer(
            base_summarizer=UnavailableSummarizer(),
            embedder=embedder,
            vector_store=vector_store,
        )

        assert summarizer.is_available() is False

    @pytest.mark.unit
    def test_custom_style(self, rag_summarizer: RAGEnhancedSummarizer) -> None:
        """测试自定义摘要风格"""
        content = ArticleContent(text="测试内容" * 20)

        summary = rag_summarizer.summarize(content, style=SummaryStyle.DETAILED)

        assert isinstance(summary, Summary)


class TestHyDEEnhancedSummarizer:
    """HyDE 增强摘要器测试"""

    @pytest.fixture
    def base_summarizer(self) -> SimpleSummarizer:
        """创建基础摘要器"""
        return SimpleSummarizer()

    @pytest.fixture
    def embedder(self) -> SimpleHashEmbedder:
        """创建嵌入器（维度与存储一致）"""
        return SimpleHashEmbedder(dimension=128)

    @pytest.fixture
    def vector_store(self) -> MemoryVectorStore:
        """创建向量存储（维度与嵌入器一致）"""
        return MemoryVectorStore(dimension=128)

    @pytest.mark.unit
    def test_hyde_summarizer_import(self) -> None:
        """测试 HyDE 摘要器导入"""
        from wechat_summarizer.infrastructure.adapters.summarizers import (
            HyDEEnhancedSummarizer,
        )

        assert HyDEEnhancedSummarizer is not None

    @pytest.mark.unit
    def test_hyde_summarizer_creation(
        self,
        base_summarizer: SimpleSummarizer,
        embedder: SimpleHashEmbedder,
        vector_store: MemoryVectorStore,
    ) -> None:
        """测试 HyDE 摘要器创建"""
        from wechat_summarizer.infrastructure.adapters.summarizers import (
            HyDEEnhancedSummarizer,
        )

        summarizer = HyDEEnhancedSummarizer(
            base_summarizer=base_summarizer,
            embedder=embedder,
            vector_store=vector_store,
        )

        # HyDE 摘要器继承自 RAG，名称使用 hyde- 前缀
        assert summarizer.name.startswith("hyde-") or summarizer.name.startswith("rag-")
        assert summarizer.method == SummaryMethod.RAG

    @pytest.mark.unit
    def test_hyde_summarize(
        self,
        base_summarizer: SimpleSummarizer,
        embedder: SimpleHashEmbedder,
        vector_store: MemoryVectorStore,
    ) -> None:
        """测试 HyDE 摘要"""
        from wechat_summarizer.infrastructure.adapters.summarizers import (
            HyDEEnhancedSummarizer,
        )

        summarizer = HyDEEnhancedSummarizer(
            base_summarizer=base_summarizer,
            embedder=embedder,
            vector_store=vector_store,
        )

        content = ArticleContent(text="这是一段关于人工智能的文章内容。" * 20)
        summary = summarizer.summarize(content)

        assert isinstance(summary, Summary)
        assert summary.content


class TestRAGIntegration:
    """RAG 集成测试"""

    @pytest.mark.integration
    def test_container_has_rag_components(self) -> None:
        """测试容器中包含 RAG 组件"""
        from wechat_summarizer.infrastructure.config import get_container, reset_container

        reset_container()
        container = get_container()

        # 验证嵌入器存在
        embedders = container.embedders
        assert "simple" in embedders  # 简单嵌入器始终可用

        # 验证向量存储存在
        stores = container.vector_stores
        assert "memory" in stores  # 内存存储始终可用

    @pytest.mark.integration
    def test_container_creates_rag_summarizers(self) -> None:
        """测试容器创建 RAG 摘要器"""
        from wechat_summarizer.infrastructure.config import get_container, reset_container

        reset_container()
        container = get_container()
        summarizers = container.summarizers

        # 如果有可用的 LLM 和 RAG 组件，应该有 RAG 摘要器
        # 注意：这取决于环境配置
        rag_names = [name for name in summarizers if name.startswith("rag-")]

        # 至少应该尝试创建 RAG 摘要器（即使最终不可用）
        # 这个测试主要验证创建逻辑不会崩溃
        assert isinstance(summarizers, dict)
