"""GraphRAG 摘要器 - 基于知识图谱的增强摘要"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from loguru import logger

from ....application.ports.outbound import (
    Community,
    Entity,
    ExtractionResult,
    KnowledgeGraph,
    SummarizerPort,
)
from ....domain.entities import Summary
from ....domain.entities.summary import SummaryMethod, SummaryStyle
from ....domain.value_objects import ArticleContent
from ..knowledge_graph import (
    LLMEntityExtractor,
    NetworkXGraphBuilder,
    SimpleCommunityDetector,
    SimpleCommunitySummarizer,
    SimpleEntityExtractor,
    SimpleGraphBuilder,
)

if TYPE_CHECKING:
    from ..knowledge_graph import (
        BaseCommunityDetector,
        BaseCommunitySummarizer,
        BaseEntityExtractor,
        BaseGraphBuilder,
    )


# GraphRAG Local Search 提示词
LOCAL_SEARCH_PROMPT = '''基于以下知识图谱上下文，请生成文章摘要。

**相关实体信息**:
{entities_context}

**实体关系**:
{relationships_context}

**原文内容**:
{text}

请根据知识图谱提供的结构化信息，生成一个准确、全面的摘要。
摘要应该：
1. 突出文章的核心主题和关键实体
2. 描述主要实体之间的关系
3. 提供文章的整体观点和结论

摘要：'''


# GraphRAG Global Search 提示词
GLOBAL_SEARCH_PROMPT = '''基于以下社区摘要信息，请回答关于文章整体的问题。

**社区摘要**:
{community_summaries}

**原始问题/摘要请求**:
请生成一个全面的文章摘要，概括文章的主要主题、核心论点和关键结论。

**要求**:
1. 综合所有社区的信息，提供全局视角
2. 识别跨社区的共同主题
3. 突出最重要的观点和发现

全局摘要：'''


class GraphRAGSummarizer:
    """
    GraphRAG 摘要器

    结合知识图谱的结构化信息与 LLM 的生成能力，
    提供更准确、更全面的文章摘要。

    支持两种搜索模式：
    - Local Search: 基于实体级别的精确查询
    - Global Search: 基于社区摘要的全局分析
    """

    def __init__(
        self,
        base_summarizer: SummarizerPort,
        entity_extractor: "BaseEntityExtractor | None" = None,
        graph_builder: "BaseGraphBuilder | None" = None,
        community_detector: "BaseCommunityDetector | None" = None,
        community_summarizer: "BaseCommunitySummarizer | None" = None,
        chunk_size: int = 2000,
        use_global_search: bool = True,
    ):
        """
        初始化 GraphRAG 摘要器

        Args:
            base_summarizer: 基础 LLM 摘要器
            entity_extractor: 实体提取器（默认使用 LLM 提取器）
            graph_builder: 图构建器（默认使用 NetworkX）
            community_detector: 社区检测器
            community_summarizer: 社区摘要器
            chunk_size: 文本分块大小
            use_global_search: 是否使用 Global Search（更全面但更慢）
        """
        self._base_summarizer = base_summarizer
        self._chunk_size = chunk_size
        self._use_global_search = use_global_search

        # 初始化组件
        if base_summarizer.is_available():
            self._entity_extractor = entity_extractor or LLMEntityExtractor(base_summarizer)
            self._graph_builder = graph_builder or NetworkXGraphBuilder()
        else:
            self._entity_extractor = entity_extractor or SimpleEntityExtractor()
            self._graph_builder = graph_builder or SimpleGraphBuilder()

        self._community_detector = community_detector or SimpleCommunityDetector()
        self._community_summarizer = community_summarizer or SimpleCommunitySummarizer()

        # 缓存
        self._current_graph: KnowledgeGraph | None = None

    @property
    def name(self) -> str:
        return f"graphrag-{self._base_summarizer.name}"

    @property
    def method(self) -> SummaryMethod:
        return SummaryMethod.GRAPHRAG

    def is_available(self) -> bool:
        """检查是否可用"""
        return self._base_summarizer.is_available()

    def summarize(
        self,
        content: ArticleContent,
        style: SummaryStyle = SummaryStyle.CONCISE,
        max_length: int | None = None,
    ) -> Summary:
        """
        生成 GraphRAG 增强摘要

        Args:
            content: 文章内容
            style: 摘要风格
            max_length: 最大长度

        Returns:
            摘要结果
        """
        text = content.text
        input_tokens = len(text)

        try:
            # 1. 构建知识图谱
            kg = self._build_knowledge_graph(text)
            self._current_graph = kg

            # 2. 检测社区
            if kg.entity_count > 0:
                communities = self._community_detector.detect(kg)
                for community in communities:
                    kg.add_community(community)

            # 3. 生成摘要
            if self._use_global_search and kg.community_count > 0:
                # Global Search: 基于社区摘要
                summary_text = self._global_search(kg, text)
            else:
                # Local Search: 基于实体上下文
                summary_text = self._local_search(kg, text)

            # 4. 提取关键点和标签
            key_points = self._extract_key_points(kg)
            tags = self._extract_tags(kg)

            return Summary(
                content=summary_text,
                key_points=tuple(key_points),
                tags=tuple(tags),
                method=SummaryMethod.GRAPHRAG,
                style=style,
                model_name=self.name,
                input_tokens=input_tokens,
                output_tokens=len(summary_text),
                created_at=datetime.now(),
            )

        except Exception as e:
            logger.error(f"GraphRAG 摘要生成失败: {e}")
            # 降级到基础摘要器
            return self._base_summarizer.summarize(content, style, max_length)

    def _build_knowledge_graph(self, text: str) -> KnowledgeGraph:
        """构建知识图谱"""
        # 分块处理长文本
        chunks = self._split_text(text)
        extractions: list[ExtractionResult] = []

        for chunk in chunks:
            try:
                extraction = self._entity_extractor.extract(chunk)
                extractions.append(extraction)
            except Exception as e:
                logger.warning(f"实体提取失败: {e}")

        # 构建图
        kg = self._graph_builder.build(extractions)

        logger.info(
            f"知识图谱构建完成: {kg.entity_count} 实体, "
            f"{kg.relationship_count} 关系"
        )

        return kg

    def _local_search(self, kg: KnowledgeGraph, text: str) -> str:
        """Local Search: 基于实体上下文生成摘要"""
        if not self._base_summarizer.is_available():
            return self._generate_simple_summary(kg, text)

        # 准备实体上下文
        entities_context = self._format_entities(kg)
        relationships_context = self._format_relationships(kg)

        # 构建提示词
        prompt = LOCAL_SEARCH_PROMPT.format(
            entities_context=entities_context or "无实体信息",
            relationships_context=relationships_context or "无关系信息",
            text=text[:3000],  # 限制文本长度
        )

        try:
            content = ArticleContent(text=prompt)
            summary = self._base_summarizer.summarize(content)
            return summary.content
        except Exception as e:
            logger.error(f"Local Search 失败: {e}")
            return self._generate_simple_summary(kg, text)

    def _global_search(self, kg: KnowledgeGraph, text: str) -> str:
        """Global Search: 基于社区摘要生成全局摘要"""
        if not self._base_summarizer.is_available():
            return self._generate_simple_summary(kg, text)

        # 生成社区摘要
        self._community_summarizer.summarize_all(kg)

        # 收集社区摘要
        community_summaries = []
        for community in sorted(kg.communities.values(), key=lambda c: c.rank, reverse=True):
            if community.summary:
                community_summaries.append(
                    f"- **{community.title}** (重要度: {community.rank:.1f}): {community.summary}"
                )

        summaries_text = "\n".join(community_summaries[:10])  # 最多10个社区

        if not summaries_text:
            return self._local_search(kg, text)

        # 构建提示词
        prompt = GLOBAL_SEARCH_PROMPT.format(
            community_summaries=summaries_text,
        )

        try:
            content = ArticleContent(text=prompt)
            summary = self._base_summarizer.summarize(content)
            return summary.content
        except Exception as e:
            logger.error(f"Global Search 失败: {e}")
            return self._local_search(kg, text)

    def _generate_simple_summary(self, kg: KnowledgeGraph, text: str) -> str:
        """生成简单摘要（不使用 LLM）"""
        summary_parts = []

        # 基于实体生成摘要
        if kg.entity_count > 0:
            # 按类型分组实体
            type_entities: dict[str, list[str]] = {}
            for entity in kg.entities.values():
                if entity.type not in type_entities:
                    type_entities[entity.type] = []
                type_entities[entity.type].append(entity.name)

            for ent_type, names in type_entities.items():
                names_str = "、".join(names[:5])
                if len(names) > 5:
                    names_str += f" 等 {len(names)} 项"
                summary_parts.append(f"涉及{ent_type}: {names_str}")

        # 添加关系信息
        if kg.relationship_count > 0:
            summary_parts.append(f"文章包含 {kg.relationship_count} 个实体关系")

        if summary_parts:
            return "。".join(summary_parts) + "。"
        else:
            # 使用文本前几句作为摘要
            sentences = text.split("。")[:3]
            return "。".join(sentences) + "。" if sentences else text[:200]

    def _format_entities(self, kg: KnowledgeGraph) -> str:
        """格式化实体信息"""
        if kg.entity_count == 0:
            return ""

        lines = []
        # 按类型分组
        type_entities: dict[str, list[Entity]] = {}
        for entity in kg.entities.values():
            if entity.type not in type_entities:
                type_entities[entity.type] = []
            type_entities[entity.type].append(entity)

        for ent_type, entities in type_entities.items():
            entities_str = ", ".join(
                f"{e.name}" + (f"({e.description[:30]}...)" if len(e.description) > 30 else f"({e.description})" if e.description else "")
                for e in entities[:10]
            )
            lines.append(f"- {ent_type}: {entities_str}")

        return "\n".join(lines)

    def _format_relationships(self, kg: KnowledgeGraph) -> str:
        """格式化关系信息"""
        if kg.relationship_count == 0:
            return ""

        lines = []
        for rel in list(kg.relationships.values())[:20]:  # 限制关系数量
            source = kg.entities.get(rel.source_id)
            target = kg.entities.get(rel.target_id)
            if source and target:
                lines.append(f"- {source.name} --[{rel.type}]--> {target.name}")

        return "\n".join(lines)

    def _extract_key_points(self, kg: KnowledgeGraph) -> list[str]:
        """从知识图谱提取关键点"""
        key_points = []

        # 基于实体生成关键点
        for entity in list(kg.entities.values())[:5]:
            if entity.description:
                key_points.append(f"{entity.name}: {entity.description}")

        # 基于社区生成关键点
        for community in list(kg.communities.values())[:3]:
            if community.summary:
                key_points.append(community.summary)

        return key_points[:5]

    def _extract_tags(self, kg: KnowledgeGraph) -> list[str]:
        """从知识图谱提取标签"""
        tags = set()

        # 使用实体类型作为标签
        for entity in kg.entities.values():
            tags.add(entity.type)

        # 使用高频实体名作为标签
        entity_names = [e.name for e in kg.entities.values()]
        for name in entity_names[:5]:
            if len(name) <= 10:  # 短名称作为标签
                tags.add(name)

        return list(tags)[:10]

    def _split_text(self, text: str) -> list[str]:
        """分割文本为块"""
        if len(text) <= self._chunk_size:
            return [text]

        chunks = []
        sentences = text.split("。")
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= self._chunk_size:
                current_chunk += sentence + "。"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence + "。"

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def get_knowledge_graph(self) -> KnowledgeGraph | None:
        """获取当前构建的知识图谱"""
        return self._current_graph
