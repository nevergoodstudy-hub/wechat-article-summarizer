"""向量嵌入器测试

测试 EmbedderPort 的各种实现。
"""

import pytest

from wechat_summarizer.infrastructure.adapters.embedders import (
    SimpleHashEmbedder,
)


class TestSimpleHashEmbedder:
    """SimpleHashEmbedder 测试"""

    @pytest.fixture
    def embedder(self) -> SimpleHashEmbedder:
        """创建简单哈希嵌入器"""
        return SimpleHashEmbedder(dimension=128)

    @pytest.mark.unit
    def test_embed_single_text(self, embedder: SimpleHashEmbedder) -> None:
        """测试单文本嵌入"""
        text = "这是一段测试文本"
        embedding = embedder.embed_single(text)

        assert len(embedding) == 128
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.unit
    def test_embed_batch(self, embedder: SimpleHashEmbedder) -> None:
        """测试批量嵌入"""
        texts = ["文本1", "文本2", "文本3"]
        embeddings = embedder.embed(texts)

        assert len(embeddings) == 3
        assert all(len(e) == 128 for e in embeddings)

    @pytest.mark.unit
    def test_deterministic_embedding(self, embedder: SimpleHashEmbedder) -> None:
        """测试嵌入的确定性（相同输入应产生相同输出）"""
        text = "测试文本"
        embedding1 = embedder.embed_single(text)
        embedding2 = embedder.embed_single(text)

        assert embedding1 == embedding2

    @pytest.mark.unit
    def test_different_texts_different_embeddings(self, embedder: SimpleHashEmbedder) -> None:
        """测试不同文本产生不同嵌入"""
        text1 = "这是第一段文本"
        text2 = "这是第二段完全不同的文本"

        embedding1 = embedder.embed_single(text1)
        embedding2 = embedder.embed_single(text2)

        # 不同文本的嵌入应该不同
        assert embedding1 != embedding2

    @pytest.mark.unit
    def test_embedder_properties(self, embedder: SimpleHashEmbedder) -> None:
        """测试嵌入器属性"""
        assert embedder.dimension == 128
        assert embedder.name == "simple-hash"
        assert embedder.is_available() is True

    @pytest.mark.unit
    def test_empty_text_embedding(self, embedder: SimpleHashEmbedder) -> None:
        """测试空文本嵌入"""
        embedding = embedder.embed_single("")

        assert len(embedding) == 128
        # 空文本应该有有效的嵌入向量
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.unit
    def test_custom_dimension(self) -> None:
        """测试自定义维度"""
        embedder = SimpleHashEmbedder(dimension=256)
        embedding = embedder.embed_single("测试")

        assert len(embedding) == 256


class TestEmbedderInterface:
    """嵌入器接口测试"""

    @pytest.mark.unit
    def test_embedder_port_interface(self) -> None:
        """测试 EmbedderPort 接口定义"""
        from wechat_summarizer.application.ports.outbound import EmbedderPort

        # 验证接口定义了必要的方法
        assert hasattr(EmbedderPort, "embed")
        assert hasattr(EmbedderPort, "embed_single")
        assert hasattr(EmbedderPort, "dimension")
        assert hasattr(EmbedderPort, "name")
        assert hasattr(EmbedderPort, "is_available")

    @pytest.mark.unit
    def test_simple_embedder_implements_interface(self) -> None:
        """测试 SimpleHashEmbedder 实现了 EmbedderPort 接口"""
        from wechat_summarizer.application.ports.outbound import EmbedderPort

        embedder = SimpleHashEmbedder()
        assert isinstance(embedder, EmbedderPort)


class TestLocalEmbedderOptional:
    """本地嵌入器测试（可选依赖）"""

    @pytest.mark.unit
    def test_local_embedder_import(self) -> None:
        """测试本地嵌入器导入（可能因依赖缺失而失败）"""
        try:
            from wechat_summarizer.infrastructure.adapters.embedders import LocalEmbedder

            # 如果导入成功，验证类存在
            assert LocalEmbedder is not None
        except ImportError:
            # sentence-transformers 未安装，跳过
            pytest.skip("sentence-transformers 未安装")


class TestOpenAIEmbedderOptional:
    """OpenAI 嵌入器测试（可选依赖）"""

    @pytest.mark.unit
    def test_openai_embedder_import(self) -> None:
        """测试 OpenAI 嵌入器导入"""
        from wechat_summarizer.infrastructure.adapters.embedders import OpenAIEmbedder

        assert OpenAIEmbedder is not None

    @pytest.mark.unit
    def test_openai_embedder_without_key(self) -> None:
        """测试无 API 密钥时的 OpenAI 嵌入器"""
        from wechat_summarizer.infrastructure.adapters.embedders import OpenAIEmbedder

        embedder = OpenAIEmbedder(api_key="")
        assert embedder.is_available() is False
