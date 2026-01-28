"""ChromaDB 向量存储 - 持久化向量数据库"""

from pathlib import Path
from typing import Any

from loguru import logger

from ....application.ports.outbound import SearchResult, VectorDocument
from .base import BaseVectorStore

# ChromaDB 是可选依赖
_chromadb_available = True
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    _chromadb_available = False
    chromadb = None
    Settings = None


class ChromaDBStore(BaseVectorStore):
    """
    ChromaDB 向量存储
    
    使用 ChromaDB 进行持久化向量存储，适用于：
    - 中等规模数据（10K - 1M 条）
    - 需要持久化的场景
    - 本地部署，无需外部服务
    """

    def __init__(
        self,
        collection_name: str = "articles",
        persist_directory: str | Path | None = None,
        dimension: int = 384,
    ):
        """
        初始化 ChromaDB 存储
        
        Args:
            collection_name: 集合名称
            persist_directory: 持久化目录（None 表示仅内存）
            dimension: 向量维度
        """
        self._collection_name = collection_name
        self._dimension = dimension
        self._client: "chromadb.Client | None" = None
        self._collection: "chromadb.Collection | None" = None
        
        if persist_directory:
            self._persist_dir = Path(persist_directory)
            self._persist_dir.mkdir(parents=True, exist_ok=True)
        else:
            self._persist_dir = None
        
        self._init_client()

    def _init_client(self) -> None:
        """初始化 ChromaDB 客户端"""
        if not _chromadb_available:
            logger.warning("ChromaDB 库未安装，存储不可用")
            return
        
        try:
            if self._persist_dir:
                # 持久化模式
                self._client = chromadb.PersistentClient(
                    path=str(self._persist_dir),
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True,
                    ),
                )
                logger.info(f"ChromaDB 持久化存储已初始化: {self._persist_dir}")
            else:
                # 内存模式
                self._client = chromadb.Client(
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True,
                    ),
                )
                logger.info("ChromaDB 内存存储已初始化")
            
            # 获取或创建集合
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"dimension": self._dimension},
            )
            
        except Exception as e:
            logger.error(f"初始化 ChromaDB 失败: {e}")
            self._client = None
            self._collection = None

    @property
    def name(self) -> str:
        return f"chromadb-{self._collection_name}"

    def is_available(self) -> bool:
        return self._collection is not None

    def add(self, documents: list[VectorDocument]) -> None:
        """添加文档"""
        if not self.is_available():
            raise RuntimeError("ChromaDB 存储不可用")
        
        if not documents:
            return
        
        ids = [doc.id for doc in documents]
        embeddings = [doc.vector for doc in documents]
        texts = [doc.text for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        try:
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
            logger.debug(f"已添加 {len(documents)} 个文档到 ChromaDB")
        except Exception as e:
            logger.error(f"添加文档到 ChromaDB 失败: {e}")
            raise RuntimeError(f"添加文档失败: {e}") from e

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """搜索相似文档"""
        if not self.is_available():
            raise RuntimeError("ChromaDB 存储不可用")
        
        try:
            # 构建查询参数
            query_params = {
                "query_embeddings": [query_vector],
                "n_results": top_k,
            }
            
            if filter_metadata:
                # ChromaDB 使用 where 参数进行过滤
                query_params["where"] = filter_metadata
            
            results = self._collection.query(**query_params)
            
            # 转换结果
            search_results: list[SearchResult] = []
            
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    # ChromaDB 返回的距离需要转换为相似度
                    distance = results["distances"][0][i] if results["distances"] else 0
                    # 余弦距离转相似度: similarity = 1 - distance (对于 cosine 距离)
                    # 或者 L2 距离转相似度: similarity = 1 / (1 + distance)
                    score = 1 / (1 + distance)
                    
                    search_results.append(SearchResult(
                        id=doc_id,
                        text=results["documents"][0][i] if results["documents"] else "",
                        score=score,
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"ChromaDB 搜索失败: {e}")
            raise RuntimeError(f"搜索失败: {e}") from e

    def delete(self, ids: list[str]) -> None:
        """删除文档"""
        if not self.is_available():
            raise RuntimeError("ChromaDB 存储不可用")
        
        if not ids:
            return
        
        try:
            self._collection.delete(ids=ids)
            logger.debug(f"已从 ChromaDB 删除 {len(ids)} 个文档")
        except Exception as e:
            logger.error(f"从 ChromaDB 删除文档失败: {e}")
            raise RuntimeError(f"删除文档失败: {e}") from e

    def clear(self) -> None:
        """清空所有文档"""
        if not self.is_available():
            raise RuntimeError("ChromaDB 存储不可用")
        
        try:
            # 删除并重新创建集合
            self._client.delete_collection(self._collection_name)
            self._collection = self._client.create_collection(
                name=self._collection_name,
                metadata={"dimension": self._dimension},
            )
            logger.debug(f"已清空 ChromaDB 集合: {self._collection_name}")
        except Exception as e:
            logger.error(f"清空 ChromaDB 失败: {e}")
            raise RuntimeError(f"清空失败: {e}") from e

    def count(self) -> int:
        """获取文档数量"""
        if not self.is_available():
            return 0
        
        try:
            return self._collection.count()
        except Exception:
            return 0

    def get(self, doc_id: str) -> VectorDocument | None:
        """获取单个文档"""
        if not self.is_available():
            return None
        
        try:
            result = self._collection.get(
                ids=[doc_id],
                include=["documents", "embeddings", "metadatas"],
            )
            
            if result["ids"]:
                return VectorDocument(
                    id=result["ids"][0],
                    text=result["documents"][0] if result["documents"] else "",
                    vector=result["embeddings"][0] if result["embeddings"] else [],
                    metadata=result["metadatas"][0] if result["metadatas"] else {},
                )
            return None
            
        except Exception:
            return None
