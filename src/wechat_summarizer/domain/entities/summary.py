"""摘要实体"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ...shared.utils import utc_now


class SummaryMethod(str, Enum):
    """摘要生成方法"""

    SIMPLE = "simple"  # 简单规则提取
    TEXTRANK = "textrank"  # TextRank算法提取
    OLLAMA = "ollama"  # 本地Ollama
    OPENAI = "openai"  # OpenAI GPT
    DEEPSEEK = "deepseek"  # DeepSeek
    ANTHROPIC = "anthropic"  # Claude
    ZHIPU = "zhipu"  # 智谱AI
    RAG = "rag"  # RAG 检索增强摘要
    GRAPHRAG = "graphrag"  # GraphRAG 知识图谱摘要


class SummaryStyle(str, Enum):
    """摘要风格"""

    CONCISE = "concise"  # 简洁
    DETAILED = "detailed"  # 详细
    ACADEMIC = "academic"  # 学术
    BUSINESS = "business"  # 商业
    BULLET_POINTS = "bullet"  # 要点列表


@dataclass(frozen=True)
class Summary:
    """
    摘要值对象

    值对象是不可变的，通过其属性值来定义身份，
    而不是通过唯一标识符。
    """

    # 核心内容
    content: str
    key_points: tuple[str, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)

    # 元数据
    method: SummaryMethod = SummaryMethod.SIMPLE
    style: SummaryStyle = SummaryStyle.CONCISE
    model_name: str | None = None

    # Token信息
    input_tokens: int = 0
    output_tokens: int = 0

    # 时间戳
    created_at: datetime = field(default_factory=utc_now)

    @property
    def total_tokens(self) -> int:
        """总Token数"""
        return self.input_tokens + self.output_tokens

    @property
    def key_points_text(self) -> str:
        """关键点文本"""
        return "\n".join(f"• {point}" for point in self.key_points)

    @property
    def tags_text(self) -> str:
        """标签文本"""
        return ", ".join(self.tags)

    def with_key_points(self, key_points: list[str]) -> Summary:
        """创建带有新关键点的摘要副本"""
        return Summary(
            content=self.content,
            key_points=tuple(key_points),
            tags=self.tags,
            method=self.method,
            style=self.style,
            model_name=self.model_name,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            created_at=self.created_at,
        )

    def with_tags(self, tags: list[str]) -> Summary:
        """创建带有新标签的摘要副本"""
        return Summary(
            content=self.content,
            key_points=self.key_points,
            tags=tuple(tags),
            method=self.method,
            style=self.style,
            model_name=self.model_name,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            created_at=self.created_at,
        )
