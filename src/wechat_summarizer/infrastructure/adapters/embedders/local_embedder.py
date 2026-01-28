"""本地向量嵌入器 - 使用 sentence-transformers"""

from loguru import logger

from .base import BaseEmbedder

# sentence-transformers 是可选依赖
_st_available = True
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    _st_available = False
    SentenceTransformer = None


class LocalEmbedder(BaseEmbedder):
    """
    本地向量嵌入器
    
    使用 sentence-transformers 库加载本地模型，无需 API 调用。
    支持中英文的推荐模型：
    - paraphrase-multilingual-MiniLM-L12-v2 (384维，多语言)
    - all-MiniLM-L6-v2 (384维，英文)
    - BAAI/bge-small-zh-v1.5 (512维，中文)
    """

    # 常用模型及其维度
    MODEL_DIMENSIONS = {
        "paraphrase-multilingual-MiniLM-L12-v2": 384,
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
        "BAAI/bge-small-zh-v1.5": 512,
        "BAAI/bge-base-zh-v1.5": 768,
        "shibing624/text2vec-base-chinese": 768,
    }

    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        device: str | None = None,
        batch_size: int = 32,
        normalize: bool = True,
    ):
        """
        初始化本地嵌入器
        
        Args:
            model_name: 模型名称或路径
            device: 设备（cpu/cuda/mps）
            batch_size: 批量处理大小
            normalize: 是否归一化向量
        """
        self._model_name = model_name
        self._device = device
        self._batch_size = batch_size
        self._normalize = normalize
        
        # 确定向量维度
        self._dimension = self.MODEL_DIMENSIONS.get(model_name, 384)
        
        self._model: "SentenceTransformer | None" = None
        self._init_model()

    def _init_model(self) -> None:
        """初始化模型"""
        if not _st_available:
            logger.warning("sentence-transformers 库未安装，本地嵌入器不可用")
            return
        
        try:
            self._model = SentenceTransformer(
                self._model_name,
                device=self._device,
            )
            # 更新实际维度
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"本地嵌入模型已加载: {self._model_name} (维度: {self._dimension})")
        except Exception as e:
            logger.error(f"加载本地嵌入模型失败: {e}")
            self._model = None

    @property
    def name(self) -> str:
        return f"local-{self._model_name.split('/')[-1]}"

    @property
    def dimension(self) -> int:
        return self._dimension

    def is_available(self) -> bool:
        return self._model is not None

    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入文本"""
        if not self.is_available():
            raise RuntimeError("本地嵌入器不可用")
        
        if not texts:
            return []
        
        # 预处理文本
        processed_texts = [self._preprocess_text(t) for t in texts]
        
        try:
            embeddings = self._model.encode(
                processed_texts,
                batch_size=self._batch_size,
                normalize_embeddings=self._normalize,
                show_progress_bar=False,
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"本地嵌入失败: {e}")
            raise RuntimeError(f"嵌入失败: {e}") from e


class SimpleHashEmbedder(BaseEmbedder):
    """
    简单哈希嵌入器（用于测试和降级）
    
    使用简单的哈希函数生成固定维度的向量，不依赖任何外部库。
    注意：此嵌入器不具备语义理解能力，仅用于测试或无法使用其他嵌入器时的降级方案。
    """

    def __init__(self, dimension: int = 384):
        """
        初始化简单哈希嵌入器
        
        Args:
            dimension: 向量维度
        """
        self._dimension = dimension

    @property
    def name(self) -> str:
        return "simple-hash"

    @property
    def dimension(self) -> int:
        return self._dimension

    def is_available(self) -> bool:
        return True

    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入文本"""
        return [self._hash_text(t) for t in texts]

    def _hash_text(self, text: str) -> list[float]:
        """使用哈希函数生成伪向量"""
        import hashlib
        
        # 预处理
        text = self._preprocess_text(text)
        
        # 生成多个哈希值以填充向量
        vector = []
        for i in range(self._dimension):
            # 每个维度使用不同的种子
            seed_text = f"{text}_{i}"
            hash_bytes = hashlib.sha256(seed_text.encode()).digest()
            # 将哈希字节转换为浮点数
            value = int.from_bytes(hash_bytes[:4], byteorder="big")
            # 归一化到 [-1, 1]
            normalized = (value / (2**31)) - 1
            vector.append(normalized)
        
        # 归一化向量长度
        norm = sum(v**2 for v in vector) ** 0.5
        if norm > 0:
            vector = [v / norm for v in vector]
        
        return vector
