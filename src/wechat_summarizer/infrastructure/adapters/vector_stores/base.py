"""向量存储基类"""

from abc import ABC, abstractmethod
from typing import Any

from ....application.ports.outbound import SearchResult, VectorDocument


class BaseVectorStore(ABC):
    """向量存储抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """存储名称"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查是否可用"""
        pass

    @abstractmethod
    def add(self, documents: list[VectorDocument]) -> None:
        """添加文档"""
        pass

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """搜索相似文档"""
        pass

    @abstractmethod
    def delete(self, ids: list[str]) -> None:
        """删除文档"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空所有文档"""
        pass

    @abstractmethod
    def count(self) -> int:
        """获取文档数量"""
        pass

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
