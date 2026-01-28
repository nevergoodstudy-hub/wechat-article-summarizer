"""RAG 增强摘要器 - 基于检索增强的摘要生成"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from loguru import logger

from ....application.ports.outbound import (
    EmbedderPort,
    SearchResult,
    VectorDocument,
    VectorStorePort,
)
from ....domain.entities import Summary, SummaryMethod, SummaryStyle
from ....domain.value_objects import ArticleContent
from .base import BaseSummarizer


@dataclass
class RAGContext:
    """RAG 检索上下文"""
    
    query: str
    retrieved_chunks: list[SearchResult] = field(default_factory=list)
    relevance_scores: list[float] = field(default_factory=list)


class RAGEnhancedSummarizer(BaseSummarizer):
    """
    RAG 增强摘要器
    
    通过检索相关文档片段来增强摘要生成：
    1. 将文章分块并嵌入到向量存储
    2. 生成摘要时检索相关片段
    3. 将检索结果作为上下文增强 LLM 摘要
    
    优势:
    - 减少幻觉（事实验证）
    - 支持长文档（分块处理）
    - 可引用来源
    """

    def __init__(
        self,
        base_summarizer: "BaseSummarizer",
        embedder: EmbedderPort,
        vector_store: VectorStorePort,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        top_k: int = 5,
        min_relevance_score: float = 0.3,
    ):
        """
        初始化 RAG 增强摘要器
        
        Args:
            base_summarizer: 基础摘要器（用于生成最终摘要）
            embedder: 向量嵌入器
            vector_store: 向量存储
            chunk_size: 分块大小（字符数）
            chunk_overlap: 分块重叠（字符数）
            top_k: 检索结果数量
            min_relevance_score: 最小相关性分数
        """
        self._base_summarizer = base_summarizer
        self._embedder = embedder
        self._vector_store = vector_store
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._top_k = top_k
        self._min_relevance_score = min_relevance_score

    @property
    def name(self) -> str:
        return f"rag-{self._base_summarizer.name}"

    @property
    def method(self) -> SummaryMethod:
        return SummaryMethod.RAG

    def is_available(self) -> bool:
        return (
            self._base_summarizer.is_available()
            and self._embedder.is_available()
            and self._vector_store.is_available()
        )

    def summarize(
        self,
        content: ArticleContent,
        style: SummaryStyle = SummaryStyle.CONCISE,
        max_length: int = 500,
    ) -> Summary:
        """生成 RAG 增强摘要"""
        if not self.is_available():
            raise RuntimeError("RAG 增强摘要器不可用")
        
        text = content.text
        if not text:
            raise ValueError("文章内容为空")
        
        # 1. 分块
        chunks = self._chunk_text(text)
        logger.debug(f"文章已分为 {len(chunks)} 个片段")
        
        # 2. 嵌入并存储
        article_id = str(uuid4())
        self._index_chunks(chunks, article_id)
        
        # 3. 检索相关片段
        # 使用文章的前几句作为查询
        query = self._extract_query(text)
        context = self._retrieve_context(query)
        logger.debug(f"检索到 {len(context.retrieved_chunks)} 个相关片段")
        
        # 4. 构建增强上下文
        enhanced_content = self._build_enhanced_content(content, context)
        
        # 5. 使用基础摘要器生成摘要
        try:
            summary = self._base_summarizer.summarize(
                enhanced_content,
                style=style,
                max_length=max_length,
            )
            
            # 更新摘要方法
            return Summary(
                content=summary.content,
                key_points=summary.key_points,
                tags=summary.tags,
                method=SummaryMethod.RAG,
                style=summary.style,
                model_name=f"rag-{summary.model_name}",
                input_tokens=summary.input_tokens,
                output_tokens=summary.output_tokens,
                created_at=datetime.now(),
            )
        finally:
            # 6. 清理临时索引
            self._cleanup_index(article_id)

    def _chunk_text(self, text: str) -> list[str]:
        """
        将文本分块（语义分块）
        
        按段落边界分块，确保语义完整性
        """
        # 首先按段落分割
        paragraphs = text.split("\n\n")
        
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_size = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            # 如果当前段落太大，需要进一步分割
            if para_size > self._chunk_size:
                # 先保存当前块
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # 按句子分割大段落
                sentences = self._split_sentences(para)
                for sent in sentences:
                    sent_size = len(sent)
                    if current_size + sent_size > self._chunk_size and current_chunk:
                        chunks.append(" ".join(current_chunk))
                        # 保留重叠
                        overlap_text = " ".join(current_chunk)[-self._chunk_overlap:]
                        current_chunk = [overlap_text] if overlap_text else []
                        current_size = len(overlap_text)
                    current_chunk.append(sent)
                    current_size += sent_size
            else:
                # 正常大小的段落
                if current_size + para_size > self._chunk_size and current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_size = 0
                current_chunk.append(para)
                current_size += para_size
        
        # 保存最后一块
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        
        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        """按句子分割文本"""
        import re
        
        # 中英文句子分割
        pattern = r'(?<=[。！？.!?])\s*'
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def _index_chunks(self, chunks: list[str], article_id: str) -> None:
        """将分块嵌入并索引到向量存储"""
        if not chunks:
            return
        
        # 批量嵌入
        embeddings = self._embedder.embed(chunks)
        
        # 创建文档
        documents = [
            VectorDocument(
                id=f"{article_id}_{i}",
                text=chunk,
                vector=embedding,
                metadata={
                    "article_id": article_id,
                    "chunk_index": i,
                },
            )
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
        
        # 添加到存储
        self._vector_store.add(documents)

    def _extract_query(self, text: str, max_length: int = 200) -> str:
        """提取查询文本（使用文章开头）"""
        # 取前几句作为查询
        sentences = self._split_sentences(text[:1000])
        query = " ".join(sentences[:3])
        if len(query) > max_length:
            query = query[:max_length]
        return query

    def _retrieve_context(self, query: str) -> RAGContext:
        """检索相关上下文"""
        # 嵌入查询
        query_embedding = self._embedder.embed_single(query)
        
        # 搜索相似文档
        results = self._vector_store.search(
            query_vector=query_embedding,
            top_k=self._top_k,
        )
        
        # 过滤低相关性结果
        filtered_results = [
            r for r in results
            if r.score >= self._min_relevance_score
        ]
        
        return RAGContext(
            query=query,
            retrieved_chunks=filtered_results,
            relevance_scores=[r.score for r in filtered_results],
        )

    def _build_enhanced_content(
        self,
        original_content: ArticleContent,
        context: RAGContext,
    ) -> ArticleContent:
        """构建增强内容"""
        if not context.retrieved_chunks:
            return original_content
        
        # 构建上下文提示
        context_parts = []
        for i, chunk in enumerate(context.retrieved_chunks):
            context_parts.append(f"[相关片段 {i+1}]\n{chunk.text}")
        
        context_text = "\n\n".join(context_parts)
        
        # 增强原文
        enhanced_text = f"""以下是文章的关键片段（按相关性排序）：

{context_text}

---

基于以上关键片段，请总结文章的主要内容：

{original_content.text[:3000]}"""
        
        return ArticleContent(
            text=enhanced_text,
            html=original_content.html,
        )

    def _cleanup_index(self, article_id: str) -> None:
        """清理临时索引"""
        try:
            # 获取所有相关文档 ID
            # 由于我们使用了 article_id 前缀，可以通过元数据过滤删除
            # 但为了简单起见，这里假设我们知道分块数量
            # 实际应用中可以使用元数据过滤
            
            # 尝试删除（忽略错误）
            for i in range(100):  # 假设最多 100 个分块
                doc_id = f"{article_id}_{i}"
                try:
                    self._vector_store.delete([doc_id])
                except Exception:
                    break
        except Exception as e:
            logger.warning(f"清理索引时出错: {e}")


class HyDEEnhancedSummarizer(RAGEnhancedSummarizer):
    """
    HyDE (Hypothetical Document Embeddings) 增强摘要器
    
    先生成假设性摘要，然后用它来检索相关文档，
    最后基于检索结果生成最终摘要。
    """

    def _extract_query(self, text: str, max_length: int = 200) -> str:
        """使用 HyDE 策略：先生成假设性答案作为查询"""
        # 生成假设性摘要
        try:
            # 使用基础摘要器生成简短摘要
            temp_content = ArticleContent(
                text=text[:2000],  # 使用部分文本
                html="",
            )
            temp_summary = self._base_summarizer.summarize(
                temp_content,
                style=SummaryStyle.CONCISE,
                max_length=100,
            )
            return temp_summary.content
        except Exception as e:
            logger.warning(f"HyDE 假设生成失败，回退到标准查询: {e}")
            return super()._extract_query(text, max_length)
