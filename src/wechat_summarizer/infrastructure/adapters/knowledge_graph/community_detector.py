"""社区检测器 - 使用 Leiden 算法检测知识图谱中的社区"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from collections import defaultdict

from loguru import logger

from ....application.ports.outbound import Community, KnowledgeGraph

# 尝试导入依赖
try:
    import networkx as nx

    _nx_available = True
except ImportError:
    _nx_available = False
    nx = None  # type: ignore

try:
    import igraph as ig
    import leidenalg

    _leiden_available = True
except ImportError:
    _leiden_available = False
    ig = None  # type: ignore
    leidenalg = None  # type: ignore


class BaseCommunityDetector(ABC):
    """社区检测器基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """检测器名称"""
        pass

    @abstractmethod
    def detect(
        self,
        graph: KnowledgeGraph,
        resolution: float = 1.0,
        max_levels: int = 3,
    ) -> list[Community]:
        """检测社区"""
        pass


class LeidenCommunityDetector(BaseCommunityDetector):
    """
    基于 Leiden 算法的社区检测器

    Leiden 算法是一种改进的模块化最优化算法，
    能够高效地发现图中的社区结构。
    """

    def __init__(self, seed: int | None = None):
        """
        初始化 Leiden 检测器

        Args:
            seed: 随机种子
        """
        self._seed = seed

        if not _leiden_available:
            logger.warning("leidenalg 或 igraph 未安装，Leiden 检测器不可用")

    @property
    def name(self) -> str:
        return "leiden-detector"

    def is_available(self) -> bool:
        """检查是否可用"""
        return _leiden_available and _nx_available

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
            max_levels: 最大层级数（层次聚类）

        Returns:
            检测到的社区列表
        """
        if not self.is_available():
            logger.warning("Leiden 检测器不可用，返回空社区列表")
            return []

        if graph.entity_count == 0:
            return []

        # 将知识图谱转换为 igraph
        ig_graph = self._to_igraph(graph)

        if ig_graph.vcount() == 0:
            return []

        communities: list[Community] = []

        try:
            # 执行 Leiden 社区检测
            partition = leidenalg.find_partition(
                ig_graph,
                leidenalg.RBConfigurationVertexPartition,
                resolution_parameter=resolution,
                seed=self._seed,
            )

            # 解析社区
            entity_ids = list(graph.entities.keys())
            for level in range(min(max_levels, 1)):  # 单层检测
                for idx, members in enumerate(partition):
                    if len(members) == 0:
                        continue

                    community_id = self._generate_community_id(level, idx)
                    member_entity_ids = [entity_ids[m] for m in members if m < len(entity_ids)]

                    if member_entity_ids:
                        community = Community(
                            id=community_id,
                            level=level,
                            entity_ids=member_entity_ids,
                            title=f"社区 {idx + 1}",
                            rank=len(member_entity_ids),  # 以成员数作为初始排名
                        )
                        communities.append(community)

            logger.info(f"Leiden 检测完成: {len(communities)} 个社区")

        except Exception as e:
            logger.error(f"Leiden 社区检测失败: {e}")

        return communities

    def _to_igraph(self, kg: KnowledgeGraph) -> "ig.Graph":
        """将知识图谱转换为 igraph 图"""
        # 创建节点 ID 映射
        entity_ids = list(kg.entities.keys())
        id_to_idx = {eid: idx for idx, eid in enumerate(entity_ids)}

        # 创建边列表
        edges = []
        for rel in kg.relationships.values():
            if rel.source_id in id_to_idx and rel.target_id in id_to_idx:
                edges.append((id_to_idx[rel.source_id], id_to_idx[rel.target_id]))

        # 创建 igraph 图
        g = ig.Graph(n=len(entity_ids), edges=edges, directed=False)

        return g

    def _generate_community_id(self, level: int, idx: int) -> str:
        """生成社区 ID"""
        key = f"community-{level}-{idx}"
        return hashlib.md5(key.encode()).hexdigest()[:12]


class SimpleCommunityDetector(BaseCommunityDetector):
    """
    简单社区检测器

    使用连通分量作为社区，不依赖外部库。
    """

    def __init__(self):
        """初始化简单检测器"""
        pass

    @property
    def name(self) -> str:
        return "simple-detector"

    def detect(
        self,
        graph: KnowledgeGraph,
        resolution: float = 1.0,
        max_levels: int = 3,
    ) -> list[Community]:
        """检测社区（使用连通分量）"""
        if graph.entity_count == 0:
            return []

        # 构建邻接表
        adjacency: dict[str, set[str]] = defaultdict(set)
        for rel in graph.relationships.values():
            adjacency[rel.source_id].add(rel.target_id)
            adjacency[rel.target_id].add(rel.source_id)

        # 找出所有连通分量
        visited: set[str] = set()
        communities: list[Community] = []
        community_idx = 0

        for entity_id in graph.entities:
            if entity_id in visited:
                continue

            # BFS 找出连通分量
            component: list[str] = []
            queue = [entity_id]

            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue

                visited.add(current)
                component.append(current)

                for neighbor in adjacency.get(current, []):
                    if neighbor not in visited:
                        queue.append(neighbor)

            if component:
                community = Community(
                    id=f"simple-{community_idx}",
                    level=0,
                    entity_ids=component,
                    title=f"组 {community_idx + 1}",
                    rank=len(component),
                )
                communities.append(community)
                community_idx += 1

        # 为孤立节点创建单独的社区
        for entity_id in graph.entities:
            if entity_id not in visited:
                community = Community(
                    id=f"simple-{community_idx}",
                    level=0,
                    entity_ids=[entity_id],
                    title=f"孤立实体 {community_idx + 1}",
                    rank=1,
                )
                communities.append(community)
                community_idx += 1

        logger.debug(f"简单检测完成: {len(communities)} 个社区")

        return communities
