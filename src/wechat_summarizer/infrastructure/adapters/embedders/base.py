"""向量嵌入器基类"""

from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    """向量嵌入器抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """嵌入器名称"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查是否可用"""
        pass

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入文本"""
        pass

    def embed_single(self, text: str) -> list[float]:
        """嵌入单个文本"""
        results = self.embed([text])
        if results:
            return results[0]
        return []

    def _preprocess_text(self, text: str, max_length: int = 8000) -> str:
        """预处理文本
        
        Args:
            text: 原始文本
            max_length: 最大字符数
            
        Returns:
            处理后的文本
        """
        # 移除多余空白
        text = " ".join(text.split())
        # 截断过长文本
        if len(text) > max_length:
            text = text[:max_length]
        return text
