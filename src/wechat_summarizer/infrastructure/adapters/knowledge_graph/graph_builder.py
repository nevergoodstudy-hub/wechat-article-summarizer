"""知识图谱构建器 - 使用 networkx 构建和管理知识图谱"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any

from loguru import logger

from ....application.ports.outbound import (
    Entity,
    ExtractionResult,
    KnowledgeGraph,
    Relationship,
)

# 尝试导入 networkx
try:
    import networkx as nx

    _nx_available = True
except ImportError:
    _nx_available = False
    nx = None  # type: ignore


class BaseGraphBuilder(ABC):
    """知识图谱构建器基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """构建器名称"""
        pass

    @abstractmethod
    def build(self, extractions: list[ExtractionResult]) -> KnowledgeGraph:
        """从提取结果构建知识图谱"""
        pass

    @abstractmethod
    def merge(self, graphs: list[KnowledgeGraph]) -> KnowledgeGraph:
        """合并多个知识图谱"""
        pass


class NetworkXGraphBuilder(BaseGraphBuilder):
    """
    基于 NetworkX 的知识图谱构建器

    将提取的实体和关系构建为 NetworkX 图结构。
    """

    def __init__(
        self,
        merge_similar_entities: bool = True,
        similarity_threshold: float = 0.8,
    ):
        """
        初始化图构建器

        Args:
            merge_similar_entities: 是否合并相似实体
            similarity_threshold: 相似度阈值
        """
        self._merge_similar = merge_similar_entities
        self._similarity_threshold = similarity_threshold

        if not _nx_available:
            logger.warning("networkx 未安装，图构建器功能将受限")

    @property
    def name(self) -> str:
        return "networkx-builder"

    def build(self, extractions: list[ExtractionResult]) -> KnowledgeGraph:
        """从提取结果构建知识图谱"""
        kg = KnowledgeGraph()

        # 收集所有实体和关系
        all_entities: dict[str, Entity] = {}
        all_relationships: list[Relationship] = []

        for extraction in extractions:
            for entity in extraction.entities:
                # 使用实体 ID 作为键，后出现的覆盖先出现的
                if entity.id not in all_entities:
                    all_entities[entity.id] = entity
                else:
                    # 合并描述
                    existing = all_entities[entity.id]
                    if entity.description and not existing.description:
                        all_entities[entity.id] = Entity(
                            id=existing.id,
                            name=existing.name,
                            type=existing.type,
                            description=entity.description,
                            attributes={**existing.attributes, **entity.attributes},
                        )

            all_relationships.extend(extraction.relationships)

        # 合并相似实体
        if self._merge_similar:
            all_entities = self._merge_similar_entities(all_entities)

        # 添加实体到知识图谱
        for entity in all_entities.values():
            kg.add_entity(entity)

        # 去重并添加关系
        seen_relationships: set[str] = set()
        for rel in all_relationships:
            # 检查源和目标实体是否存在
            if rel.source_id not in kg.entities or rel.target_id not in kg.entities:
                continue

            # 使用关系键去重
            rel_key = f"{rel.source_id}-{rel.type}-{rel.target_id}"
            if rel_key in seen_relationships:
                continue

            seen_relationships.add(rel_key)
            kg.add_relationship(rel)

        logger.info(
            f"图构建完成: {kg.entity_count} 实体, {kg.relationship_count} 关系"
        )

        return kg

    def merge(self, graphs: list[KnowledgeGraph]) -> KnowledgeGraph:
        """合并多个知识图谱"""
        merged = KnowledgeGraph()

        for graph in graphs:
            # 合并实体
            for entity in graph.entities.values():
                if entity.id not in merged.entities:
                    merged.add_entity(entity)

            # 合并关系
            for rel in graph.relationships.values():
                if rel.id not in merged.relationships:
                    merged.add_relationship(rel)

            # 合并社区
            for community in graph.communities.values():
                if community.id not in merged.communities:
                    merged.add_community(community)

        logger.info(
            f"图合并完成: {merged.entity_count} 实体, "
            f"{merged.relationship_count} 关系, {merged.community_count} 社区"
        )

        return merged

    def _merge_similar_entities(
        self, entities: dict[str, Entity]
    ) -> dict[str, Entity]:
        """合并相似实体（基于名称相似度）"""
        # 按名称分组
        name_to_entities: dict[str, list[Entity]] = defaultdict(list)
        for entity in entities.values():
            # 标准化名称
            normalized_name = entity.name.lower().strip()
            name_to_entities[normalized_name].append(entity)

        # 合并同名实体
        merged: dict[str, Entity] = {}
        for name, ent_list in name_to_entities.items():
            if len(ent_list) == 1:
                merged[ent_list[0].id] = ent_list[0]
            else:
                # 选择描述最丰富的实体
                best_entity = max(ent_list, key=lambda e: len(e.description))
                # 合并属性
                combined_attrs: dict[str, Any] = {}
                for ent in ent_list:
                    combined_attrs.update(ent.attributes)

                merged_entity = Entity(
                    id=best_entity.id,
                    name=best_entity.name,
                    type=best_entity.type,
                    description=best_entity.description,
                    attributes=combined_attrs,
                )
                merged[merged_entity.id] = merged_entity

        return merged

    def to_networkx(self, kg: KnowledgeGraph) -> "nx.Graph":
        """将知识图谱转换为 NetworkX 图"""
        if not _nx_available:
            raise RuntimeError("networkx 未安装")

        G = nx.Graph()

        # 添加节点
        for entity in kg.entities.values():
            G.add_node(
                entity.id,
                name=entity.name,
                type=entity.type,
                description=entity.description,
                **entity.attributes,
            )

        # 添加边
        for rel in kg.relationships.values():
            G.add_edge(
                rel.source_id,
                rel.target_id,
                id=rel.id,
                type=rel.type,
                description=rel.description,
                weight=rel.weight,
                **rel.attributes,
            )

        return G

    def from_networkx(self, G: "nx.Graph") -> KnowledgeGraph:
        """从 NetworkX 图创建知识图谱"""
        kg = KnowledgeGraph()

        # 添加实体
        for node_id, attrs in G.nodes(data=True):
            entity = Entity(
                id=str(node_id),
                name=attrs.get("name", str(node_id)),
                type=attrs.get("type", "概念"),
                description=attrs.get("description", ""),
                attributes={
                    k: v
                    for k, v in attrs.items()
                    if k not in {"name", "type", "description"}
                },
            )
            kg.add_entity(entity)

        # 添加关系
        for source, target, attrs in G.edges(data=True):
            rel = Relationship(
                id=attrs.get("id", f"{source}-{target}"),
                source_id=str(source),
                target_id=str(target),
                type=attrs.get("type", "相关"),
                description=attrs.get("description", ""),
                weight=attrs.get("weight", 1.0),
                attributes={
                    k: v
                    for k, v in attrs.items()
                    if k not in {"id", "type", "description", "weight"}
                },
            )
            kg.add_relationship(rel)

        return kg


class SimpleGraphBuilder(BaseGraphBuilder):
    """
    简单图构建器

    不依赖 networkx，用于测试和简单场景。
    """

    def __init__(self):
        """初始化简单图构建器"""
        pass

    @property
    def name(self) -> str:
        return "simple-builder"

    def build(self, extractions: list[ExtractionResult]) -> KnowledgeGraph:
        """从提取结果构建知识图谱"""
        kg = KnowledgeGraph()

        for extraction in extractions:
            for entity in extraction.entities:
                if entity.id not in kg.entities:
                    kg.add_entity(entity)

            for rel in extraction.relationships:
                if rel.id not in kg.relationships:
                    # 确保源和目标实体存在
                    if rel.source_id in kg.entities and rel.target_id in kg.entities:
                        kg.add_relationship(rel)

        logger.debug(
            f"简单图构建完成: {kg.entity_count} 实体, {kg.relationship_count} 关系"
        )

        return kg

    def merge(self, graphs: list[KnowledgeGraph]) -> KnowledgeGraph:
        """合并多个知识图谱"""
        merged = KnowledgeGraph()

        for graph in graphs:
            for entity in graph.entities.values():
                if entity.id not in merged.entities:
                    merged.add_entity(entity)

            for rel in graph.relationships.values():
                if rel.id not in merged.relationships:
                    merged.add_relationship(rel)

            for community in graph.communities.values():
                if community.id not in merged.communities:
                    merged.add_community(community)

        return merged
