"""向量存储适配器"""

from __future__ import annotations

from .base import BaseVectorStore
from .memory_store import MemoryVectorStore

__all__ = [
    "BaseVectorStore",
    "ChromaDBStore",
    "MemoryVectorStore",
]


def __getattr__(name: str):
    """按需延迟导入可选组件。"""
    if name == "ChromaDBStore":
        from .chromadb_store import ChromaDBStore

        return ChromaDBStore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
