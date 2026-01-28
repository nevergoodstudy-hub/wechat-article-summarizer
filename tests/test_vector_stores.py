"""向量存储测试

测试 VectorStorePort 的各种实现。
"""

import pytest

from wechat_summarizer.application.ports.outbound import VectorDocument, SearchResult
from wechat_summarizer.infrastructure.adapters.embedders import SimpleHashEmbedder
from wechat_summarizer.infrastructure.adapters.vector_stores import MemoryVectorStore


class TestMemoryVectorStore:
    """内存向量存储测试"""

    @pytest.fixture
    def embedder(self) -> SimpleHashEmbedder:
        """创建简单哈希嵌入器（维度与存储一致）"""
        return SimpleHashEmbedder(dimension=384)

    @pytest.fixture
    def store(self) -> MemoryVectorStore:
        """创建内存向量存储"""
        return MemoryVectorStore(dimension=384)

    @pytest.fixture
    def sample_documents(self, embedder: SimpleHashEmbedder) -> list[VectorDocument]:
        """创建示例文档"""
        texts = [
            "人工智能正在改变世界",
            "机器学习是人工智能的子领域",
            "深度学习使用神经网络",
            "自然语言处理处理文本数据",
            "计算机视觉处理图像数据",
        ]
        return [
            VectorDocument(
                id=f"doc_{i}",
                text=text,
                vector=embedder.embed_single(text),
                metadata={"index": i},
            )
            for i, text in enumerate(texts)
        ]

    @pytest.mark.unit
    def test_add_single_document(
        self, store: MemoryVectorStore, embedder: SimpleHashEmbedder
    ) -> None:
        """测试添加单个文档"""
        doc = VectorDocument(
            id="test_doc",
            text="测试内容",
            vector=embedder.embed_single("测试内容"),
            metadata={"type": "test"},
        )

        store.add([doc])  # add 接受列表

        assert store.count() == 1

    @pytest.mark.unit
    def test_add_multiple_documents(
        self, store: MemoryVectorStore, sample_documents: list[VectorDocument]
    ) -> None:
        """测试批量添加文档"""
        store.add(sample_documents)

        assert store.count() == len(sample_documents)

    @pytest.mark.unit
    def test_search_similar(
        self,
        store: MemoryVectorStore,
        sample_documents: list[VectorDocument],
        embedder: SimpleHashEmbedder,
    ) -> None:
        """测试相似性搜索"""
        store.add(sample_documents)

        # 搜索与 "AI" 相关的内容
        query_embedding = embedder.embed_single("AI 人工智能技术")
        results = store.search(query_embedding, top_k=3)

        assert len(results) == 3
        # 结果应该按相似度排序（余弦相似度范围 [-1, 1]）
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(-1 <= r.score <= 1 for r in results)

    @pytest.mark.unit
    def test_search_empty_store(
        self, store: MemoryVectorStore, embedder: SimpleHashEmbedder
    ) -> None:
        """测试空存储搜索"""
        query_embedding = embedder.embed_single("测试查询")
        results = store.search(query_embedding, top_k=5)

        assert len(results) == 0

    @pytest.mark.unit
    def test_delete_document(
        self, store: MemoryVectorStore, sample_documents: list[VectorDocument]
    ) -> None:
        """测试删除文档"""
        store.add(sample_documents)
        initial_count = store.count()

        store.delete(["doc_0"])  # delete 接受 ID 列表

        assert store.count() == initial_count - 1

    @pytest.mark.unit
    def test_delete_nonexistent_document(self, store: MemoryVectorStore) -> None:
        """测试删除不存在的文档"""
        # 应该不抛出异常
        store.delete(["nonexistent_id"])

    @pytest.mark.unit
    def test_clear_store(
        self, store: MemoryVectorStore, sample_documents: list[VectorDocument]
    ) -> None:
        """测试清空存储"""
        store.add(sample_documents)
        assert store.count() > 0

        store.clear()

        assert store.count() == 0

    @pytest.mark.unit
    def test_get_document_by_id(
        self, store: MemoryVectorStore, sample_documents: list[VectorDocument]
    ) -> None:
        """测试按 ID 获取文档"""
        store.add(sample_documents)

        doc = store.get("doc_0")

        assert doc is not None
        assert doc.id == "doc_0"
        assert doc.text == "人工智能正在改变世界"

    @pytest.mark.unit
    def test_get_nonexistent_document(self, store: MemoryVectorStore) -> None:
        """测试获取不存在的文档"""
        doc = store.get("nonexistent_id")

        assert doc is None

    @pytest.mark.unit
    def test_search_with_filter(
        self,
        store: MemoryVectorStore,
        embedder: SimpleHashEmbedder,
    ) -> None:
        """测试带过滤条件的搜索"""
        # 添加带不同元数据的文档
        docs = [
            VectorDocument(
                id="doc_a",
                text="文档A内容",
                vector=embedder.embed_single("文档A内容"),
                metadata={"category": "tech"},
            ),
            VectorDocument(
                id="doc_b",
                text="文档B内容",
                vector=embedder.embed_single("文档B内容"),
                metadata={"category": "science"},
            ),
        ]
        store.add(docs)

        # 使用过滤器搜索
        query_embedding = embedder.embed_single("文档内容")
        results = store.search(
            query_embedding, top_k=10, filter_metadata={"category": "tech"}
        )

        assert len(results) == 1
        assert results[0].metadata["category"] == "tech"


class TestVectorStoreInterface:
    """向量存储接口测试"""

    @pytest.mark.unit
    def test_vector_store_port_interface(self) -> None:
        """测试 VectorStorePort 接口定义"""
        from wechat_summarizer.application.ports.outbound import VectorStorePort

        # 验证接口定义了必要的方法
        assert hasattr(VectorStorePort, "add")
        assert hasattr(VectorStorePort, "search")
        assert hasattr(VectorStorePort, "delete")
        assert hasattr(VectorStorePort, "clear")
        assert hasattr(VectorStorePort, "count")

    @pytest.mark.unit
    def test_memory_store_implements_interface(self) -> None:
        """测试 MemoryVectorStore 实现了 VectorStorePort 接口"""
        from wechat_summarizer.application.ports.outbound import VectorStorePort

        store = MemoryVectorStore()
        assert isinstance(store, VectorStorePort)


class TestVectorDocument:
    """VectorDocument 测试"""

    @pytest.mark.unit
    def test_document_creation(self) -> None:
        """测试文档创建"""
        doc = VectorDocument(
            id="test",
            text="内容",
            vector=[0.1, 0.2, 0.3],
            metadata={"key": "value"},
        )

        assert doc.id == "test"
        assert doc.text == "内容"
        assert len(doc.vector) == 3
        assert doc.metadata["key"] == "value"

    @pytest.mark.unit
    def test_document_default_metadata(self) -> None:
        """测试文档默认元数据"""
        doc = VectorDocument(
            id="test",
            text="内容",
            vector=[0.1, 0.2],
        )

        # 默认应该是空字典
        assert doc.metadata == {}


class TestChromaDBStoreOptional:
    """ChromaDB 存储测试（可选依赖）"""

    @pytest.mark.unit
    def test_chromadb_store_import(self) -> None:
        """测试 ChromaDB 存储导入"""
        try:
            from wechat_summarizer.infrastructure.adapters.vector_stores import ChromaDBStore

            assert ChromaDBStore is not None
        except ImportError:
            pytest.skip("chromadb 未安装")
