"""社区摘要器 - 为知识图谱社区生成摘要"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loguru import logger

from ....application.ports.outbound import (
    Community,
    Entity,
    KnowledgeGraph,
    Relationship,
)

if TYPE_CHECKING:
    from ....application.ports.outbound import SummarizerPort


# 社区摘要提示词
COMMUNITY_SUMMARY_PROMPT = '''请为以下知识图谱社区生成一个简洁的摘要。

**社区信息**:
- 社区名称: {community_title}
- 成员数量: {member_count}

**社区中的实体**:
{entities_text}

**实体间的关系**:
{relationships_text}

请生成一个 2-3 句话的摘要，概括这个社区的主要内容和主题。
摘要应该：
1. 说明社区涉及的主要主题或领域
2. 提及最重要的实体
3. 描述实体之间的主要关系

摘要：'''


class BaseCommunitySummarizer(ABC):
    """社区摘要器基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """摘要器名称"""
        pass

    @abstractmethod
    def summarize(
        self,
        community: Community,
        entities: list[Entity],
        relationships: list[Relationship],
    ) -> str:
        """为社区生成摘要"""
        pass

    @abstractmethod
    def summarize_all(
        self,
        graph: KnowledgeGraph,
    ) -> dict[str, str]:
        """为所有社区生成摘要"""
        pass


class LLMCommunitySummarizer(BaseCommunitySummarizer):
    """
    基于 LLM 的社区摘要器

    使用 LLM 为每个社区生成摘要描述。
    """

    def __init__(
        self,
        summarizer: SummarizerPort,
        max_entities_per_summary: int = 20,
        max_relationships_per_summary: int = 30,
    ):
        """
        初始化 LLM 社区摘要器

        Args:
            summarizer: 用于生成摘要的摘要器
            max_entities_per_summary: 每个摘要最多包含的实体数
            max_relationships_per_summary: 每个摘要最多包含的关系数
        """
        self._summarizer = summarizer
        self._max_entities = max_entities_per_summary
        self._max_relationships = max_relationships_per_summary

    @property
    def name(self) -> str:
        return f"llm-community-summarizer-{self._summarizer.name}"

    def is_available(self) -> bool:
        """检查是否可用"""
        return self._summarizer.is_available()

    def summarize(
        self,
        community: Community,
        entities: list[Entity],
        relationships: list[Relationship],
    ) -> str:
        """为社区生成摘要"""
        if not self.is_available():
            return self._generate_simple_summary(community, entities, relationships)

        # 限制实体和关系数量
        limited_entities = entities[: self._max_entities]
        limited_relationships = relationships[: self._max_relationships]

        # 格式化实体文本
        entities_text = "\n".join(
            f"- {e.name} ({e.type}): {e.description or '无描述'}"
            for e in limited_entities
        )

        # 格式化关系文本
        relationships_text = "\n".join(
            f"- {self._get_entity_name(e, entities)} --[{r.type}]--> {self._get_target_name(r, entities)}"
            for r in limited_relationships
            for e in entities
            if e.id == r.source_id
        )

        if not relationships_text:
            relationships_text = "无明确关系"

        # 构建提示词
        prompt = COMMUNITY_SUMMARY_PROMPT.format(
            community_title=community.title,
            member_count=len(community.entity_ids),
            entities_text=entities_text or "无实体",
            relationships_text=relationships_text,
        )

        try:
            from ....domain.value_objects import ArticleContent

            content = ArticleContent(text=prompt)
            summary = self._summarizer.summarize(content)
            return summary.content.strip()

        except Exception as e:
            logger.error(f"社区摘要生成失败: {e}")
            return self._generate_simple_summary(community, entities, relationships)

    def summarize_all(
        self,
        graph: KnowledgeGraph,
    ) -> dict[str, str]:
        """为所有社区生成摘要"""
        summaries: dict[str, str] = {}

        for community in graph.communities.values():
            # 获取社区中的实体
            entities = [
                graph.entities[eid]
                for eid in community.entity_ids
                if eid in graph.entities
            ]

            # 获取社区相关的关系
            relationships = self._get_community_relationships(community, graph)

            # 生成摘要
            summary = self.summarize(community, entities, relationships)
            summaries[community.id] = summary

            # 更新社区对象
            community.summary = summary

        logger.info(f"已为 {len(summaries)} 个社区生成摘要")
        return summaries

    def _get_entity_name(self, entity: Entity, entities: list[Entity]) -> str:
        """获取实体名称"""
        return entity.name

    def _get_target_name(self, rel: Relationship, entities: list[Entity]) -> str:
        """获取关系目标实体名称"""
        for e in entities:
            if e.id == rel.target_id:
                return e.name
        return rel.target_id

    def _get_community_relationships(
        self, community: Community, graph: KnowledgeGraph
    ) -> list[Relationship]:
        """获取社区相关的关系"""
        entity_ids = set(community.entity_ids)
        relationships = []

        for rel in graph.relationships.values():
            if rel.source_id in entity_ids or rel.target_id in entity_ids:
                relationships.append(rel)

        return relationships

    def _generate_simple_summary(
        self,
        community: Community,
        entities: list[Entity],
        relationships: list[Relationship],
    ) -> str:
        """生成简单摘要（不使用 LLM）"""
        # 统计实体类型
        type_counts: dict[str, int] = {}
        for e in entities:
            type_counts[e.type] = type_counts.get(e.type, 0) + 1

        # 找出最常见的类型
        top_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        types_str = "、".join(f"{t[0]}({t[1]}个)" for t in top_types)

        # 生成简单摘要
        summary = f"该社区包含 {len(entities)} 个实体"
        if types_str:
            summary += f"，主要类型为 {types_str}"
        if relationships:
            summary += f"，共有 {len(relationships)} 个关系"
        summary += "。"

        return summary


class SimpleCommunitySummarizer(BaseCommunitySummarizer):
    """
    简单社区摘要器

    不使用 LLM，仅基于统计信息生成摘要。
    """

    def __init__(self):
        """初始化简单摘要器"""
        pass

    @property
    def name(self) -> str:
        return "simple-community-summarizer"

    def summarize(
        self,
        community: Community,
        entities: list[Entity],
        relationships: list[Relationship],
    ) -> str:
        """为社区生成简单摘要"""
        # 统计实体类型
        type_counts: dict[str, int] = {}
        entity_names: list[str] = []

        for e in entities[:10]:  # 最多取10个实体名
            type_counts[e.type] = type_counts.get(e.type, 0) + 1
            entity_names.append(e.name)

        # 找出最常见的类型
        top_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        types_str = "、".join(t[0] for t in top_types)

        # 构建摘要
        summary_parts = []

        if entity_names:
            names_preview = "、".join(entity_names[:5])
            if len(entity_names) > 5:
                names_preview += f" 等 {len(entities)} 个实体"
            summary_parts.append(f"包含 {names_preview}")

        if types_str:
            summary_parts.append(f"主要涉及 {types_str}")

        if relationships:
            summary_parts.append(f"实体间有 {len(relationships)} 个关系")

        return "。".join(summary_parts) + "。" if summary_parts else "空社区"

    def summarize_all(
        self,
        graph: KnowledgeGraph,
    ) -> dict[str, str]:
        """为所有社区生成摘要"""
        summaries: dict[str, str] = {}

        for community in graph.communities.values():
            entities = [
                graph.entities[eid]
                for eid in community.entity_ids
                if eid in graph.entities
            ]

            relationships = []
            entity_ids = set(community.entity_ids)
            for rel in graph.relationships.values():
                if rel.source_id in entity_ids or rel.target_id in entity_ids:
                    relationships.append(rel)

            summary = self.summarize(community, entities, relationships)
            summaries[community.id] = summary
            community.summary = summary

        return summaries
