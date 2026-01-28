"""MapReduce 分块摘要器

对于超长文本，采用 MapReduce 策略：
1. Map: 将文本分成多个块，分别生成摘要
2. Reduce: 合并所有块摘要，生成最终摘要

适用场景：
- 超长文章（>10000字）
- 多篇文章聚合摘要
- 需要保留更多细节的场景
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from loguru import logger

from ....domain.entities import Summary, SummaryMethod, SummaryStyle
from ....domain.value_objects import ArticleContent
from ....shared.exceptions import SummarizerError
from .base import BaseSummarizer

if TYPE_CHECKING:
    from collections.abc import Callable


class MapReduceSummarizer(BaseSummarizer):
    """
    MapReduce 分块摘要器
    
    通过分块处理超长文本，然后合并摘要。
    需要一个基础 LLM 摘要器来执行实际的摘要生成。
    
    工作流程：
    1. 将文本按语义边界分成多个块（每块约 chunk_size 字符）
    2. 对每个块生成摘要（Map 阶段）
    3. 将所有块摘要合并，生成最终摘要（Reduce 阶段）
    
    示例：
        >>> from .openai import OpenAISummarizer
        >>> base = OpenAISummarizer(api_key="...")
        >>> summarizer = MapReduceSummarizer(base_summarizer=base)
        >>> summary = summarizer.summarize(long_content)
    """
    
    # 默认块大小（字符数）
    DEFAULT_CHUNK_SIZE = 4000
    
    # 块重叠大小（保持上下文连贯性）
    DEFAULT_OVERLAP = 200
    
    # 单块摘要最大长度
    CHUNK_SUMMARY_LENGTH = 300
    
    def __init__(
        self,
        base_summarizer: BaseSummarizer,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
        max_chunks: int = 20,
    ):
        """
        初始化 MapReduce 摘要器
        
        Args:
            base_summarizer: 基础 LLM 摘要器（用于实际生成摘要）
            chunk_size: 每个块的目标大小（字符数）
            overlap: 块之间的重叠大小
            max_chunks: 最大处理块数（防止过长文本）
        """
        self._base = base_summarizer
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._max_chunks = max_chunks
    
    @property
    def name(self) -> str:
        return f"mapreduce-{self._base.name}"
    
    @property
    def method(self) -> SummaryMethod:
        # 返回基础摘要器的方法，保持一致性
        return self._base.method
    
    def is_available(self) -> bool:
        """检查基础摘要器是否可用"""
        return self._base.is_available()
    
    def summarize(
        self,
        content: ArticleContent,
        style: SummaryStyle = SummaryStyle.CONCISE,
        max_length: int = 500,
    ) -> Summary:
        """
        使用 MapReduce 策略生成摘要
        
        对于短文本（<chunk_size），直接使用基础摘要器。
        对于长文本，执行 Map-Reduce 流程。
        """
        if not self.is_available():
            raise SummarizerError(f"基础摘要器 {self._base.name} 不可用")
        
        text = content.text
        
        # 短文本直接处理
        if len(text) <= self._chunk_size:
            logger.debug(f"文本较短 ({len(text)} 字符)，直接摘要")
            return self._base.summarize(content, style, max_length)
        
        # 长文本使用 MapReduce
        logger.info(f"启用 MapReduce 模式处理长文本 ({len(text)} 字符)")
        
        # 1. 分块
        chunks = self._split_into_chunks(text)
        logger.debug(f"文本分成 {len(chunks)} 个块")
        
        # 2. Map: 对每个块生成摘要
        chunk_summaries = self._map_summarize(chunks, style)
        
        # 3. Reduce: 合并所有摘要
        final_summary = self._reduce_summaries(chunk_summaries, style, max_length)
        
        return final_summary
    
    def _split_into_chunks(self, text: str) -> list[str]:
        """
        将文本分成多个块
        
        优先在段落边界分割，保持语义完整性。
        """
        chunks: list[str] = []
        
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 如果当前块加上这段不超过限制，追加
            if len(current_chunk) + len(para) + 2 <= self._chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                # 保存当前块
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果单段超过限制，按句子分割
                if len(para) > self._chunk_size:
                    sub_chunks = self._split_long_paragraph(para)
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
                else:
                    # 添加重叠部分
                    if chunks and self._overlap > 0:
                        overlap_text = chunks[-1][-self._overlap:]
                        current_chunk = overlap_text + "\n\n" + para
                    else:
                        current_chunk = para
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
        
        # 限制最大块数
        if len(chunks) > self._max_chunks:
            logger.warning(f"块数 ({len(chunks)}) 超过限制，截断到 {self._max_chunks}")
            chunks = chunks[:self._max_chunks]
        
        return chunks
    
    def _split_long_paragraph(self, para: str) -> list[str]:
        """分割超长段落"""
        chunks: list[str] = []
        
        # 按句子分割（中文/英文句号）
        sentences = re.split(r'([。！？.!?])', para)
        
        current = ""
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punct = sentences[i + 1] if i + 1 < len(sentences) else ""
            full_sentence = sentence + punct
            
            if len(current) + len(full_sentence) <= self._chunk_size:
                current += full_sentence
            else:
                if current:
                    chunks.append(current)
                current = full_sentence
        
        if current:
            chunks.append(current)
        
        return chunks
    
    def _map_summarize(
        self,
        chunks: list[str],
        style: SummaryStyle,
    ) -> list[Summary]:
        """
        Map 阶段：对每个块生成摘要
        """
        summaries: list[Summary] = []
        
        for i, chunk in enumerate(chunks):
            logger.debug(f"处理块 {i + 1}/{len(chunks)} ({len(chunk)} 字符)")
            
            try:
                chunk_content = ArticleContent(text=chunk)
                summary = self._base.summarize(
                    chunk_content,
                    style=style,
                    max_length=self.CHUNK_SUMMARY_LENGTH,
                )
                summaries.append(summary)
            except Exception as e:
                logger.warning(f"块 {i + 1} 摘要失败: {e}")
                # 失败时使用简单截断
                summaries.append(Summary(
                    content=chunk[:self.CHUNK_SUMMARY_LENGTH] + "...",
                    method=self.method,
                    style=style,
                ))
        
        return summaries
    
    def _reduce_summaries(
        self,
        chunk_summaries: list[Summary],
        style: SummaryStyle,
        max_length: int,
    ) -> Summary:
        """
        Reduce 阶段：合并所有块摘要
        """
        if len(chunk_summaries) == 1:
            return chunk_summaries[0]
        
        # 收集所有块摘要内容
        combined_text = "\n\n---\n\n".join(
            f"【第{i+1}部分】\n{s.content}"
            for i, s in enumerate(chunk_summaries)
        )
        
        # 收集所有关键点
        all_key_points: list[str] = []
        for s in chunk_summaries:
            all_key_points.extend(s.key_points)
        
        # 收集所有标签
        all_tags: set[str] = set()
        for s in chunk_summaries:
            all_tags.update(s.tags)
        
        # 构建 Reduce prompt
        reduce_prompt = f"""以下是一篇长文章各部分的摘要，请将它们整合成一个完整、连贯的总摘要。

{combined_text}

要求：
1. 提炼核心观点，去除重复内容
2. 保持逻辑连贯
3. 总摘要不超过 {max_length} 字
4. 按照原文结构组织内容"""
        
        # 生成最终摘要
        try:
            reduce_content = ArticleContent(text=reduce_prompt)
            final = self._base.summarize(
                reduce_content,
                style=style,
                max_length=max_length,
            )
            
            # 合并关键点和标签
            merged_key_points = self._merge_key_points(
                list(final.key_points) + all_key_points
            )
            merged_tags = self._merge_tags(list(final.tags) + list(all_tags))
            
            # 计算总 token 数
            total_input = sum(s.input_tokens for s in chunk_summaries) + final.input_tokens
            total_output = sum(s.output_tokens for s in chunk_summaries) + final.output_tokens
            
            return Summary(
                content=final.content,
                key_points=tuple(merged_key_points[:10]),  # 限制关键点数量
                tags=tuple(merged_tags[:10]),  # 限制标签数量
                method=self.method,
                style=style,
                model_name=f"mapreduce-{final.model_name}",
                input_tokens=total_input,
                output_tokens=total_output,
            )
        except Exception as e:
            logger.error(f"Reduce 阶段失败: {e}")
            # 降级：直接拼接块摘要
            fallback_content = "\n\n".join(s.content for s in chunk_summaries)
            if len(fallback_content) > max_length:
                fallback_content = fallback_content[:max_length] + "..."
            
            return Summary(
                content=fallback_content,
                key_points=tuple(all_key_points[:10]),
                tags=tuple(sorted(all_tags)[:10]),
                method=self.method,
                style=style,
                model_name=f"mapreduce-{self._base.name}",
            )
    
    def _merge_key_points(self, points: list[str]) -> list[str]:
        """合并并去重关键点"""
        seen: set[str] = set()
        merged: list[str] = []
        
        for point in points:
            # 简单去重：转小写比较
            normalized = point.lower().strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                merged.append(point)
        
        return merged
    
    def _merge_tags(self, tags: list[str]) -> list[str]:
        """合并并去重标签"""
        seen: set[str] = set()
        merged: list[str] = []
        
        for tag in tags:
            normalized = tag.lower().strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                merged.append(tag)
        
        return merged
