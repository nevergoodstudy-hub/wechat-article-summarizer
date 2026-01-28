"""OpenAI 向量嵌入器"""

from loguru import logger

from .base import BaseEmbedder

# OpenAI 是可选依赖
_openai_available = True
try:
    import openai
except ImportError:
    _openai_available = False


class OpenAIEmbedder(BaseEmbedder):
    """
    OpenAI 向量嵌入器
    
    使用 OpenAI text-embedding-3-small 或 text-embedding-3-large 模型
    """

    # 模型维度映射
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        base_url: str | None = None,
        dimensions: int | None = None,
        batch_size: int = 100,
    ):
        """
        初始化 OpenAI 嵌入器
        
        Args:
            api_key: OpenAI API 密钥
            model: 模型名称
            base_url: API 基础 URL（可选，用于兼容其他 API）
            dimensions: 向量维度（可选，某些模型支持自定义维度）
            batch_size: 批量处理大小
        """
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._batch_size = batch_size
        
        # 确定向量维度
        if dimensions:
            self._dimension = dimensions
        else:
            self._dimension = self.MODEL_DIMENSIONS.get(model, 1536)
        
        self._client: "openai.OpenAI | None" = None
        self._init_client()

    def _init_client(self) -> None:
        """初始化 OpenAI 客户端"""
        if not _openai_available:
            logger.warning("OpenAI 库未安装，嵌入器不可用")
            return
        
        if not self._api_key:
            logger.warning("OpenAI API 密钥未配置，嵌入器不可用")
            return
        
        try:
            self._client = openai.OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )
        except Exception as e:
            logger.error(f"初始化 OpenAI 客户端失败: {e}")
            self._client = None

    @property
    def name(self) -> str:
        return f"openai-{self._model}"

    @property
    def dimension(self) -> int:
        return self._dimension

    def is_available(self) -> bool:
        return self._client is not None

    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入文本"""
        if not self.is_available():
            raise RuntimeError("OpenAI 嵌入器不可用")
        
        if not texts:
            return []
        
        # 预处理文本
        processed_texts = [self._preprocess_text(t) for t in texts]
        
        # 分批处理
        all_embeddings: list[list[float]] = []
        
        for i in range(0, len(processed_texts), self._batch_size):
            batch = processed_texts[i:i + self._batch_size]
            
            try:
                response = self._client.embeddings.create(
                    model=self._model,
                    input=batch,
                )
                
                # 按索引排序确保顺序正确
                sorted_data = sorted(response.data, key=lambda x: x.index)
                batch_embeddings = [item.embedding for item in sorted_data]
                all_embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"OpenAI 嵌入失败: {e}")
                raise RuntimeError(f"嵌入失败: {e}") from e
        
        return all_embeddings

    async def embed_async(self, texts: list[str]) -> list[list[float]]:
        """异步批量嵌入文本"""
        if not _openai_available:
            raise RuntimeError("OpenAI 库未安装")
        
        if not self._api_key:
            raise RuntimeError("OpenAI API 密钥未配置")
        
        if not texts:
            return []
        
        # 预处理文本
        processed_texts = [self._preprocess_text(t) for t in texts]
        
        async_client = openai.AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )
        
        all_embeddings: list[list[float]] = []
        
        for i in range(0, len(processed_texts), self._batch_size):
            batch = processed_texts[i:i + self._batch_size]
            
            try:
                response = await async_client.embeddings.create(
                    model=self._model,
                    input=batch,
                )
                
                sorted_data = sorted(response.data, key=lambda x: x.index)
                batch_embeddings = [item.embedding for item in sorted_data]
                all_embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"OpenAI 异步嵌入失败: {e}")
                raise RuntimeError(f"嵌入失败: {e}") from e
        
        return all_embeddings
