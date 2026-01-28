"""内存向量存储 - 用于测试和小规模使用"""

from typing import Any

from loguru import logger

from ....application.ports.outbound import SearchResult, VectorDocument
from .base import BaseVectorStore


class MemoryVectorStore(BaseVectorStore):
    """
    内存向量存储
    
    将向量存储在内存中，适用于：
    - 单元测试
    - 小规模数据（< 10000 条）
    - 不需要持久化的场景
    """

    def __init__(self, dimension: int = 384):
        """
        初始化内存存储
        
        Args:
            dimension: 向量维度
        """
        self._dimension = dimension
        self._documents: dict[str, VectorDocument] = {}
        logger.debug(f"内存向量存储已初始化 (维度: {dimension})")

    @property
    def name(self) -> str:
        return "memory"

    def is_available(self) -> bool:
        return True

    def add(self, documents: list[VectorDocument]) -> None:
        """添加文档"""
        for doc in documents:
            if len(doc.vector) != self._dimension:
                raise ValueError(
                    f"向量维度不匹配: 期望 {self._dimension}, 实际 {len(doc.vector)}"
                )
            self._documents[doc.id] = doc
        logger.debug(f"已添加 {len(documents)} 个文档，当前总数: {len(self._documents)}")

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """搜索相似文档"""
        if len(query_vector) != self._dimension:
            raise ValueError(
                f"查询向量维度不匹配: 期望 {self._dimension}, 实际 {len(query_vector)}"
            )
        
        results: list[tuple[str, float, VectorDocument]] = []
        
        for doc_id, doc in self._documents.items():
            # 元数据过滤
            if filter_metadata:
                if not self._match_metadata(doc.metadata, filter_metadata):
                    continue
            
            # 计算相似度
            score = self._cosine_similarity(query_vector, doc.vector)
            results.append((doc_id, score, doc))
        
        # 按相似度降序排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        # 返回 top_k 结果
        return [
            SearchResult(
                id=doc_id,
                text=doc.text,
                score=score,
                metadata=doc.metadata,
            )
            for doc_id, score, doc in results[:top_k]
        ]

    def delete(self, ids: list[str]) -> None:
        """删除文档"""
        for doc_id in ids:
            if doc_id in self._documents:
                del self._documents[doc_id]
        logger.debug(f"已删除 {len(ids)} 个文档")

    def clear(self) -> None:
        """清空所有文档"""
        count = len(self._documents)
        self._documents.clear()
        logger.debug(f"已清空 {count} 个文档")

    def count(self) -> int:
        """获取文档数量"""
        return len(self._documents)

    def get(self, doc_id: str) -> VectorDocument | None:
        """获取单个文档"""
        return self._documents.get(doc_id)

    def _match_metadata(
        self,
        doc_metadata: dict[str, Any],
        filter_metadata: dict[str, Any],
    ) -> bool:
        """检查文档元数据是否匹配过滤条件"""
        for key, value in filter_metadata.items():
            if key not in doc_metadata:
                return False
            if doc_metadata[key] != value:
                return False
        return True
