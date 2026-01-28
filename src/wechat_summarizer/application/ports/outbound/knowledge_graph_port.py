"""知识图谱出站端口 - 定义知识图谱相关接口"""

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class Entity:
    """实体"""

    id: str
    name: str
    type: str
    description: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class Relationship:
    """关系"""

    id: str
    source_id: str
    target_id: str
    type: str
    description: str = ""
    weight: float = 1.0
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class Community:
    """社区（实体聚类）"""

    id: str
    level: int
    entity_ids: list[str]
    title: str = ""
    summary: str = ""
    rank: float = 0.0


@dataclass
class KnowledgeGraph:
    """知识图谱数据结构"""

    entities: dict[str, Entity] = field(default_factory=dict)
    relationships: dict[str, Relationship] = field(default_factory=dict)
    communities: dict[str, Community] = field(default_factory=dict)

    def add_entity(self, entity: Entity) -> None:
        """添加实体"""
        self.entities[entity.id] = entity

    def add_relationship(self, relationship: Relationship) -> None:
        """添加关系"""
        self.relationships[relationship.id] = relationship

    def add_community(self, community: Community) -> None:
        """添加社区"""
        self.communities[community.id] = community

    def get_entity(self, entity_id: str) -> Entity | None:
        """获取实体"""
        return self.entities.get(entity_id)

    def get_relationships_for_entity(self, entity_id: str) -> list[Relationship]:
        """获取实体相关的所有关系"""
        return [
            rel
            for rel in self.relationships.values()
            if rel.source_id == entity_id or rel.target_id == entity_id
        ]

    def get_community_for_entity(self, entity_id: str) -> Community | None:
        """获取实体所属的社区"""
        for community in self.communities.values():
            if entity_id in community.entity_ids:
                return community
        return None

    @property
    def entity_count(self) -> int:
        """实体数量"""
        return len(self.entities)

    @property
    def relationship_count(self) -> int:
        """关系数量"""
        return len(self.relationships)

    @property
    def community_count(self) -> int:
        """社区数量"""
        return len(self.communities)


@dataclass
class ExtractionResult:
    """实体关系提取结果"""

    entities: list[Entity]
    relationships: list[Relationship]
    source_text: str = ""


@runtime_checkable
class EntityExtractorPort(Protocol):
    """
    实体关系提取器端口

    使用 LLM 从文本中提取实体和关系。
    """

    @property
    def name(self) -> str:
        """提取器名称"""
        ...

    def is_available(self) -> bool:
        """检查是否可用"""
        ...

    def extract(
        self,
        text: str,
        entity_types: list[str] | None = None,
        relationship_types: list[str] | None = None,
    ) -> ExtractionResult:
        """
        从文本中提取实体和关系

        Args:
            text: 输入文本
            entity_types: 要提取的实体类型（如 ["人物", "组织", "地点"]）
            relationship_types: 要提取的关系类型

        Returns:
            提取结果
        """
        ...


@runtime_checkable
class GraphBuilderPort(Protocol):
    """
    知识图谱构建器端口

    将提取的实体和关系构建为图结构。
    """

    @property
    def name(self) -> str:
        """构建器名称"""
        ...

    def build(self, extractions: list[ExtractionResult]) -> KnowledgeGraph:
        """
        从提取结果构建知识图谱

        Args:
            extractions: 实体关系提取结果列表

        Returns:
            知识图谱
        """
        ...

    def merge(self, graphs: list[KnowledgeGraph]) -> KnowledgeGraph:
        """
        合并多个知识图谱

        Args:
            graphs: 知识图谱列表

        Returns:
            合并后的知识图谱
        """
        ...


@runtime_checkable
class CommunityDetectorPort(Protocol):
    """
    社区检测器端口

    在知识图谱中检测社区结构。
    """

    @property
    def name(self) -> str:
        """检测器名称"""
        ...

    def detect(
        self,
        graph: KnowledgeGraph,
        resolution: float = 1.0,
        max_levels: int = 3,
    ) -> list[Community]:
        """
        检测社区

        Args:
            graph: 知识图谱
            resolution: 分辨率参数（越大社区越小）
            max_levels: 最大层级数

        Returns:
            检测到的社区列表
        """
        ...


@runtime_checkable
class CommunitySummarizerPort(Protocol):
    """
    社区摘要器端口

    为社区生成摘要。
    """

    @property
    def name(self) -> str:
        """摘要器名称"""
        ...

    def summarize(
        self,
        community: Community,
        entities: list[Entity],
        relationships: list[Relationship],
    ) -> str:
        """
        为社区生成摘要

        Args:
            community: 社区
            entities: 社区中的实体
            relationships: 社区相关的关系

        Returns:
            社区摘要
        """
        ...

    def summarize_all(
        self,
        graph: KnowledgeGraph,
    ) -> dict[str, str]:
        """
        为所有社区生成摘要

        Args:
            graph: 知识图谱

        Returns:
            社区ID到摘要的映射
        """
        ...
