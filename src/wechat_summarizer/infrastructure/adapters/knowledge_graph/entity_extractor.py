"""实体关系提取器 - 使用 LLM 从文本中提取实体和关系"""

from __future__ import annotations

import hashlib
import json
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from loguru import logger

from ....application.ports.outbound import (
    Entity,
    ExtractionResult,
    Relationship,
)

if TYPE_CHECKING:
    from ....application.ports.outbound import SummarizerPort


# 默认实体类型
DEFAULT_ENTITY_TYPES = [
    "人物",
    "组织",
    "地点",
    "事件",
    "概念",
    "技术",
    "产品",
    "时间",
]

# 默认关系类型
DEFAULT_RELATIONSHIP_TYPES = [
    "属于",
    "位于",
    "创建",
    "参与",
    "相关",
    "影响",
    "包含",
    "合作",
    "竞争",
    "继承",
]

# 实体关系提取提示词
EXTRACTION_PROMPT = '''你是一个专业的知识图谱构建助手。请从以下文本中提取实体和关系。

**任务说明**:
1. 识别文本中的重要实体（如人物、组织、地点、事件、概念、技术、产品等）
2. 识别实体之间的关系
3. 为每个实体和关系提供简短描述

**输出格式**（严格的 JSON 格式）:
```json
{
    "entities": [
        {
            "name": "实体名称",
            "type": "实体类型",
            "description": "对实体的简短描述"
        }
    ],
    "relationships": [
        {
            "source": "源实体名称",
            "target": "目标实体名称",
            "type": "关系类型",
            "description": "对关系的简短描述"
        }
    ]
}
```

**可用实体类型**: {entity_types}
**可用关系类型**: {relationship_types}

**文本内容**:
{text}

请输出 JSON 格式的提取结果：'''


class BaseEntityExtractor(ABC):
    """实体关系提取器基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """提取器名称"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查是否可用"""
        pass

    @abstractmethod
    def extract(
        self,
        text: str,
        entity_types: list[str] | None = None,
        relationship_types: list[str] | None = None,
    ) -> ExtractionResult:
        """从文本中提取实体和关系"""
        pass

    def _generate_entity_id(self, name: str, entity_type: str) -> str:
        """生成实体 ID"""
        key = f"{entity_type}:{name}"
        return hashlib.md5(key.encode()).hexdigest()[:12]

    def _generate_relationship_id(
        self, source_id: str, target_id: str, rel_type: str
    ) -> str:
        """生成关系 ID"""
        key = f"{source_id}-{rel_type}-{target_id}"
        return hashlib.md5(key.encode()).hexdigest()[:12]

    def _parse_extraction_response(
        self, response: str, source_text: str
    ) -> ExtractionResult:
        """解析 LLM 提取响应"""
        entities: list[Entity] = []
        relationships: list[Relationship] = []
        entity_name_to_id: dict[str, str] = {}

        try:
            # 尝试提取 JSON 部分
            json_match = re.search(r"\{[\s\S]*\}", response)
            if not json_match:
                logger.warning("无法从响应中提取 JSON")
                return ExtractionResult(entities=[], relationships=[], source_text=source_text)

            json_str = json_match.group()
            data = json.loads(json_str)

            # 解析实体
            for ent in data.get("entities", []):
                name = ent.get("name", "").strip()
                ent_type = ent.get("type", "概念").strip()
                description = ent.get("description", "").strip()

                if not name:
                    continue

                entity_id = self._generate_entity_id(name, ent_type)
                entity_name_to_id[name] = entity_id

                entities.append(
                    Entity(
                        id=entity_id,
                        name=name,
                        type=ent_type,
                        description=description,
                    )
                )

            # 解析关系
            for rel in data.get("relationships", []):
                source_name = rel.get("source", "").strip()
                target_name = rel.get("target", "").strip()
                rel_type = rel.get("type", "相关").strip()
                description = rel.get("description", "").strip()

                if not source_name or not target_name:
                    continue

                # 确保源和目标实体存在
                if source_name not in entity_name_to_id:
                    source_id = self._generate_entity_id(source_name, "概念")
                    entity_name_to_id[source_name] = source_id
                    entities.append(
                        Entity(
                            id=source_id,
                            name=source_name,
                            type="概念",
                            description="",
                        )
                    )
                else:
                    source_id = entity_name_to_id[source_name]

                if target_name not in entity_name_to_id:
                    target_id = self._generate_entity_id(target_name, "概念")
                    entity_name_to_id[target_name] = target_id
                    entities.append(
                        Entity(
                            id=target_id,
                            name=target_name,
                            type="概念",
                            description="",
                        )
                    )
                else:
                    target_id = entity_name_to_id[target_name]

                rel_id = self._generate_relationship_id(source_id, target_id, rel_type)
                relationships.append(
                    Relationship(
                        id=rel_id,
                        source_id=source_id,
                        target_id=target_id,
                        type=rel_type,
                        description=description,
                    )
                )

            logger.debug(f"提取到 {len(entities)} 个实体，{len(relationships)} 个关系")

        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {e}")
        except Exception as e:
            logger.error(f"解析提取响应失败: {e}")

        return ExtractionResult(
            entities=entities,
            relationships=relationships,
            source_text=source_text,
        )


class LLMEntityExtractor(BaseEntityExtractor):
    """
    基于 LLM 的实体关系提取器

    使用摘要器作为 LLM 后端进行实体关系提取。
    """

    def __init__(
        self,
        summarizer: SummarizerPort,
        entity_types: list[str] | None = None,
        relationship_types: list[str] | None = None,
        max_text_length: int = 4000,
    ):
        """
        初始化 LLM 实体提取器

        Args:
            summarizer: 用于 LLM 调用的摘要器
            entity_types: 默认实体类型
            relationship_types: 默认关系类型
            max_text_length: 最大文本长度
        """
        self._summarizer = summarizer
        self._default_entity_types = entity_types or DEFAULT_ENTITY_TYPES
        self._default_relationship_types = relationship_types or DEFAULT_RELATIONSHIP_TYPES
        self._max_text_length = max_text_length

    @property
    def name(self) -> str:
        return f"llm-extractor-{self._summarizer.name}"

    def is_available(self) -> bool:
        return self._summarizer.is_available()

    def extract(
        self,
        text: str,
        entity_types: list[str] | None = None,
        relationship_types: list[str] | None = None,
    ) -> ExtractionResult:
        """从文本中提取实体和关系"""
        if not self.is_available():
            logger.warning("LLM 提取器不可用")
            return ExtractionResult(entities=[], relationships=[], source_text=text)

        # 使用提供的类型或默认类型
        ent_types = entity_types or self._default_entity_types
        rel_types = relationship_types or self._default_relationship_types

        # 截断过长文本
        if len(text) > self._max_text_length:
            text = text[: self._max_text_length]
            logger.debug(f"文本已截断至 {self._max_text_length} 字符")

        # 构建提示词
        prompt = EXTRACTION_PROMPT.format(
            entity_types=", ".join(ent_types),
            relationship_types=", ".join(rel_types),
            text=text,
        )

        try:
            # 使用摘要器的底层 LLM 进行提取
            # 这里我们需要直接调用 LLM，而不是摘要功能
            from ....domain.value_objects import ArticleContent

            content = ArticleContent(text=prompt)
            summary = self._summarizer.summarize(content)
            response = summary.content

            return self._parse_extraction_response(response, text)

        except Exception as e:
            logger.error(f"实体提取失败: {e}")
            return ExtractionResult(entities=[], relationships=[], source_text=text)


class SimpleEntityExtractor(BaseEntityExtractor):
    """
    简单实体提取器（基于规则）

    用于测试和不需要 LLM 的场景。
    使用简单的正则表达式匹配提取实体。
    """

    # 常见的中文人名模式
    PERSON_PATTERNS = [
        r"(?:由|被|让|使|向|对|跟|同|和|与|给|替|为|把|将|得|的)([^\s,，。！？、：；""'']{2,4})[说道讲表示认为提出]",
        r"([^\s,，。！？、：；""'']{2,4})(?:先生|女士|教授|博士|老师|同学|院士|专家)",
    ]

    # 组织名模式
    ORG_PATTERNS = [
        r"([^\s,，。！？、：；""'']+(?:公司|集团|大学|学院|研究院|中心|组织|协会|委员会|政府|部门))",
    ]

    # 技术/概念模式
    TECH_PATTERNS = [
        r"([A-Za-z][A-Za-z0-9\-\.]+(?:\s+[A-Za-z][A-Za-z0-9\-\.]+)*)",  # 英文技术术语
    ]

    def __init__(self):
        """初始化简单提取器"""
        pass

    @property
    def name(self) -> str:
        return "simple-extractor"

    def is_available(self) -> bool:
        return True

    def extract(
        self,
        text: str,
        entity_types: list[str] | None = None,
        relationship_types: list[str] | None = None,
    ) -> ExtractionResult:
        """从文本中提取实体（基于规则）"""
        entities: list[Entity] = []
        entity_names: set[str] = set()

        # 提取人名
        for pattern in self.PERSON_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                name = match.strip()
                if name and len(name) >= 2 and name not in entity_names:
                    entity_names.add(name)
                    entities.append(
                        Entity(
                            id=self._generate_entity_id(name, "人物"),
                            name=name,
                            type="人物",
                            description="",
                        )
                    )

        # 提取组织名
        for pattern in self.ORG_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                name = match.strip()
                if name and len(name) >= 3 and name not in entity_names:
                    entity_names.add(name)
                    entities.append(
                        Entity(
                            id=self._generate_entity_id(name, "组织"),
                            name=name,
                            type="组织",
                            description="",
                        )
                    )

        # 提取技术术语
        for pattern in self.TECH_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                name = match.strip()
                if name and len(name) >= 2 and name not in entity_names:
                    # 过滤常见词
                    if name.lower() not in {"the", "a", "an", "is", "are", "was", "were"}:
                        entity_names.add(name)
                        entities.append(
                            Entity(
                                id=self._generate_entity_id(name, "技术"),
                                name=name,
                                type="技术",
                                description="",
                            )
                        )

        logger.debug(f"简单提取器提取到 {len(entities)} 个实体")

        # 简单提取器不提取关系
        return ExtractionResult(
            entities=entities[:50],  # 限制实体数量
            relationships=[],
            source_text=text,
        )
