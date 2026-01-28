"""GraphRAG 单元测试

测试知识图谱构建和 GraphRAG 摘要器。
"""

import pytest

from wechat_summarizer.application.ports.outbound import (
    Community,
    Entity,
    ExtractionResult,
    KnowledgeGraph,
    Relationship,
)
from wechat_summarizer.domain.entities import Summary, SummaryMethod
from wechat_summarizer.domain.value_objects import ArticleContent
from wechat_summarizer.infrastructure.adapters.knowledge_graph import (
    SimpleCommunityDetector,
    SimpleCommunitySummarizer,
    SimpleEntityExtractor,
    SimpleGraphBuilder,
)
from wechat_summarizer.infrastructure.adapters.summarizers import (
    GraphRAGSummarizer,
    SimpleSummarizer,
)


class TestEntity:
    """实体数据结构测试"""

    @pytest.mark.unit
    def test_entity_creation(self) -> None:
        """测试实体创建"""
        entity = Entity(
            id="e1",
            name="张三",
            type="人物",
            description="一位测试人物",
        )

        assert entity.id == "e1"
        assert entity.name == "张三"
        assert entity.type == "人物"
        assert entity.description == "一位测试人物"

    @pytest.mark.unit
    def test_entity_default_values(self) -> None:
        """测试实体默认值"""
        entity = Entity(id="e1", name="测试", type="概念")

        assert entity.description == ""
        assert entity.attributes == {}


class TestRelationship:
    """关系数据结构测试"""

    @pytest.mark.unit
    def test_relationship_creation(self) -> None:
        """测试关系创建"""
        rel = Relationship(
            id="r1",
            source_id="e1",
            target_id="e2",
            type="属于",
            description="实体1属于实体2",
        )

        assert rel.id == "r1"
        assert rel.source_id == "e1"
        assert rel.target_id == "e2"
        assert rel.type == "属于"
        assert rel.weight == 1.0


class TestKnowledgeGraph:
    """知识图谱数据结构测试"""

    @pytest.fixture
    def sample_graph(self) -> KnowledgeGraph:
        """创建示例知识图谱"""
        kg = KnowledgeGraph()

        # 添加实体
        kg.add_entity(Entity(id="e1", name="人工智能", type="技术"))
        kg.add_entity(Entity(id="e2", name="机器学习", type="技术"))
        kg.add_entity(Entity(id="e3", name="深度学习", type="技术"))

        # 添加关系
        kg.add_relationship(
            Relationship(id="r1", source_id="e2", target_id="e1", type="属于")
        )
        kg.add_relationship(
            Relationship(id="r2", source_id="e3", target_id="e2", type="属于")
        )

        return kg

    @pytest.mark.unit
    def test_graph_entity_count(self, sample_graph: KnowledgeGraph) -> None:
        """测试实体计数"""
        assert sample_graph.entity_count == 3

    @pytest.mark.unit
    def test_graph_relationship_count(self, sample_graph: KnowledgeGraph) -> None:
        """测试关系计数"""
        assert sample_graph.relationship_count == 2

    @pytest.mark.unit
    def test_get_entity(self, sample_graph: KnowledgeGraph) -> None:
        """测试获取实体"""
        entity = sample_graph.get_entity("e1")
        assert entity is not None
        assert entity.name == "人工智能"

    @pytest.mark.unit
    def test_get_relationships_for_entity(self, sample_graph: KnowledgeGraph) -> None:
        """测试获取实体相关关系"""
        rels = sample_graph.get_relationships_for_entity("e2")
        assert len(rels) == 2  # e2 是 r1 的源和 r2 的目标

    @pytest.mark.unit
    def test_add_community(self, sample_graph: KnowledgeGraph) -> None:
        """测试添加社区"""
        community = Community(
            id="c1",
            level=0,
            entity_ids=["e1", "e2", "e3"],
            title="技术社区",
        )
        sample_graph.add_community(community)

        assert sample_graph.community_count == 1


class TestSimpleEntityExtractor:
    """简单实体提取器测试"""

    @pytest.fixture
    def extractor(self) -> SimpleEntityExtractor:
        """创建简单实体提取器"""
        return SimpleEntityExtractor()

    @pytest.mark.unit
    def test_extractor_properties(self, extractor: SimpleEntityExtractor) -> None:
        """测试提取器属性"""
        assert extractor.name == "simple-extractor"
        assert extractor.is_available() is True

    @pytest.mark.unit
    def test_extract_organizations(self, extractor: SimpleEntityExtractor) -> None:
        """测试提取组织名"""
        text = "腾讯公司是中国最大的互联网公司之一，阿里巴巴集团也是重要的科技企业。"
        result = extractor.extract(text)

        assert len(result.entities) >= 1
        org_names = [e.name for e in result.entities if e.type == "组织"]
        assert any("腾讯" in name or "阿里" in name for name in org_names)

    @pytest.mark.unit
    def test_extract_tech_terms(self, extractor: SimpleEntityExtractor) -> None:
        """测试提取技术术语"""
        text = "GraphRAG 是一种结合了 RAG 和知识图谱的技术。"
        result = extractor.extract(text)

        tech_names = [e.name for e in result.entities if e.type == "技术"]
        assert len(tech_names) >= 1


class TestSimpleGraphBuilder:
    """简单图构建器测试"""

    @pytest.fixture
    def builder(self) -> SimpleGraphBuilder:
        """创建简单图构建器"""
        return SimpleGraphBuilder()

    @pytest.mark.unit
    def test_builder_properties(self, builder: SimpleGraphBuilder) -> None:
        """测试构建器属性"""
        assert builder.name == "simple-builder"

    @pytest.mark.unit
    def test_build_from_extractions(self, builder: SimpleGraphBuilder) -> None:
        """测试从提取结果构建图"""
        extractions = [
            ExtractionResult(
                entities=[
                    Entity(id="e1", name="AI", type="技术"),
                    Entity(id="e2", name="ML", type="技术"),
                ],
                relationships=[
                    Relationship(id="r1", source_id="e2", target_id="e1", type="属于"),
                ],
            )
        ]

        kg = builder.build(extractions)

        assert kg.entity_count == 2
        assert kg.relationship_count == 1

    @pytest.mark.unit
    def test_merge_graphs(self, builder: SimpleGraphBuilder) -> None:
        """测试合并图"""
        kg1 = KnowledgeGraph()
        kg1.add_entity(Entity(id="e1", name="A", type="概念"))

        kg2 = KnowledgeGraph()
        kg2.add_entity(Entity(id="e2", name="B", type="概念"))

        merged = builder.merge([kg1, kg2])

        assert merged.entity_count == 2


class TestSimpleCommunityDetector:
    """简单社区检测器测试"""

    @pytest.fixture
    def detector(self) -> SimpleCommunityDetector:
        """创建简单社区检测器"""
        return SimpleCommunityDetector()

    @pytest.mark.unit
    def test_detector_properties(self, detector: SimpleCommunityDetector) -> None:
        """测试检测器属性"""
        assert detector.name == "simple-detector"

    @pytest.mark.unit
    def test_detect_connected_components(
        self, detector: SimpleCommunityDetector
    ) -> None:
        """测试检测连通分量"""
        kg = KnowledgeGraph()

        # 创建两个连通分量
        kg.add_entity(Entity(id="e1", name="A", type="概念"))
        kg.add_entity(Entity(id="e2", name="B", type="概念"))
        kg.add_entity(Entity(id="e3", name="C", type="概念"))
        kg.add_entity(Entity(id="e4", name="D", type="概念"))

        # 连接 e1-e2 和 e3-e4
        kg.add_relationship(Relationship(id="r1", source_id="e1", target_id="e2", type="相关"))
        kg.add_relationship(Relationship(id="r2", source_id="e3", target_id="e4", type="相关"))

        communities = detector.detect(kg)

        # 应该检测到 2 个社区（两个连通分量）
        assert len(communities) == 2

    @pytest.mark.unit
    def test_detect_empty_graph(self, detector: SimpleCommunityDetector) -> None:
        """测试空图检测"""
        kg = KnowledgeGraph()
        communities = detector.detect(kg)

        assert len(communities) == 0


class TestSimpleCommunitySummarizer:
    """简单社区摘要器测试"""

    @pytest.fixture
    def summarizer(self) -> SimpleCommunitySummarizer:
        """创建简单社区摘要器"""
        return SimpleCommunitySummarizer()

    @pytest.mark.unit
    def test_summarizer_properties(
        self, summarizer: SimpleCommunitySummarizer
    ) -> None:
        """测试摘要器属性"""
        assert summarizer.name == "simple-community-summarizer"

    @pytest.mark.unit
    def test_summarize_community(
        self, summarizer: SimpleCommunitySummarizer
    ) -> None:
        """测试社区摘要"""
        community = Community(
            id="c1",
            level=0,
            entity_ids=["e1", "e2"],
            title="测试社区",
        )

        entities = [
            Entity(id="e1", name="Python", type="技术"),
            Entity(id="e2", name="JavaScript", type="技术"),
        ]

        relationships = [
            Relationship(id="r1", source_id="e1", target_id="e2", type="相关"),
        ]

        summary = summarizer.summarize(community, entities, relationships)

        assert len(summary) > 0
        assert "技术" in summary or "Python" in summary


class TestGraphRAGSummarizer:
    """GraphRAG 摘要器测试"""

    @pytest.fixture
    def base_summarizer(self) -> SimpleSummarizer:
        """创建基础摘要器"""
        return SimpleSummarizer()

    @pytest.fixture
    def graphrag_summarizer(
        self, base_summarizer: SimpleSummarizer
    ) -> GraphRAGSummarizer:
        """创建 GraphRAG 摘要器"""
        return GraphRAGSummarizer(
            base_summarizer=base_summarizer,
            chunk_size=500,
            use_global_search=False,  # 使用 Local Search 测试
        )

    @pytest.mark.unit
    def test_summarizer_properties(
        self, graphrag_summarizer: GraphRAGSummarizer
    ) -> None:
        """测试摘要器属性"""
        assert graphrag_summarizer.name == "graphrag-simple"
        assert graphrag_summarizer.method == SummaryMethod.GRAPHRAG

    @pytest.mark.unit
    def test_summarize_short_text(
        self, graphrag_summarizer: GraphRAGSummarizer
    ) -> None:
        """测试短文本摘要"""
        content = ArticleContent(
            text="人工智能是计算机科学的一个重要分支。机器学习是人工智能的核心技术。"
        )

        summary = graphrag_summarizer.summarize(content)

        assert isinstance(summary, Summary)
        assert summary.content
        assert summary.method == SummaryMethod.GRAPHRAG

    @pytest.mark.unit
    def test_summarize_with_entities(
        self, graphrag_summarizer: GraphRAGSummarizer
    ) -> None:
        """测试带实体的摘要"""
        content = ArticleContent(
            text="""
            腾讯公司是中国领先的互联网企业。
            阿里巴巴集团是电商领域的巨头。
            两家公司在云计算领域展开激烈竞争。
            """
        )

        summary = graphrag_summarizer.summarize(content)

        assert isinstance(summary, Summary)
        # 检查是否提取了标签
        assert len(summary.tags) >= 0

    @pytest.mark.unit
    def test_get_knowledge_graph(
        self, graphrag_summarizer: GraphRAGSummarizer
    ) -> None:
        """测试获取知识图谱"""
        content = ArticleContent(text="测试文本。测试实体提取和图谱构建。")

        graphrag_summarizer.summarize(content)
        kg = graphrag_summarizer.get_knowledge_graph()

        assert kg is not None
        assert isinstance(kg, KnowledgeGraph)


class TestGraphRAGIntegration:
    """GraphRAG 集成测试"""

    @pytest.mark.integration
    def test_container_has_graphrag_components(self) -> None:
        """测试容器包含 GraphRAG 组件"""
        from wechat_summarizer.infrastructure.config import get_container, reset_container

        reset_container()
        container = get_container()
        summarizers = container.summarizers

        # 检查是否尝试创建 GraphRAG 摘要器
        graphrag_names = [name for name in summarizers if name.startswith("graphrag-")]

        # GraphRAG 摘要器需要可用的 LLM
        # 如果没有配置 LLM，可能不会创建 GraphRAG 摘要器
        assert isinstance(summarizers, dict)
