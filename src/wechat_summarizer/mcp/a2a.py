"""A2A (Agent-to-Agent) 协议支持

实现 Google A2A 协议，支持 Agent 间协作。

参考:
- https://a2a-protocol.org/latest/specification/
- https://github.com/a2aproject/A2A
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    """任务状态"""

    PENDING = "pending"  # 待处理
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class AgentSkill:
    """Agent 技能定义"""

    name: str
    description: str
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None


@dataclass
class AgentCard:
    """Agent 卡片

    用于 Agent 能力发现和描述。
    """

    name: str
    description: str
    version: str
    endpoint: str  # Agent 服务端点
    skills: list[AgentSkill] = field(default_factory=list)
    auth_schemes: list[str] = field(default_factory=lambda: ["none"])
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "endpoint": self.endpoint,
            "skills": [
                {
                    "name": skill.name,
                    "description": skill.description,
                    "input_schema": skill.input_schema,
                    "output_schema": skill.output_schema,
                }
                for skill in self.skills
            ],
            "auth_schemes": self.auth_schemes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentCard:
        """从字典创建"""
        skills = [
            AgentSkill(
                name=skill["name"],
                description=skill["description"],
                input_schema=skill.get("input_schema"),
                output_schema=skill.get("output_schema"),
            )
            for skill in data.get("skills", [])
        ]

        return cls(
            name=data["name"],
            description=data["description"],
            version=data["version"],
            endpoint=data["endpoint"],
            skills=skills,
            auth_schemes=data.get("auth_schemes", ["none"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TaskMessage:
    """任务消息"""

    role: str  # "user" 或 "agent"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskArtifact:
    """任务产物"""

    name: str
    content_type: str  # "text/plain", "application/json", etc.
    content: Any
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class A2ATask:
    """A2A 任务

    表示 Agent 间协作的任务单元。
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    instruction: str = ""
    status: TaskStatus = TaskStatus.PENDING
    messages: list[TaskMessage] = field(default_factory=list)
    artifacts: list[TaskArtifact] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    context: str | None = None  # 上下文标识符
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        """添加消息"""
        self.messages.append(
            TaskMessage(
                role=role,
                content=content,
                metadata=metadata or {},
            )
        )
        self.updated_at = datetime.now().isoformat()

    def add_artifact(
        self,
        name: str,
        content_type: str,
        content: Any,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """添加产物"""
        self.artifacts.append(
            TaskArtifact(
                name=name,
                content_type=content_type,
                content=content,
                metadata=metadata or {},
            )
        )
        self.updated_at = datetime.now().isoformat()

    def complete(self, result: dict[str, Any] | None = None) -> None:
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.updated_at = datetime.now().isoformat()
        if result:
            self.add_artifact(
                name="result",
                content_type="application/json",
                content=result,
            )

    def fail(self, error: str) -> None:
        """标记任务失败"""
        self.status = TaskStatus.FAILED
        self.updated_at = datetime.now().isoformat()
        self.metadata["error"] = error

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "instruction": self.instruction,
            "status": self.status.value,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata,
                }
                for msg in self.messages
            ],
            "artifacts": [
                {
                    "name": art.name,
                    "content_type": art.content_type,
                    "content": art.content,
                    "metadata": art.metadata,
                }
                for art in self.artifacts
            ],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "context": self.context,
            "metadata": self.metadata,
        }


class A2AServer:
    """A2A 服务器

    处理来自其他 Agent 的任务请求。
    """

    def __init__(self, agent_card: AgentCard) -> None:
        """初始化 A2A 服务器

        Args:
            agent_card: Agent 卡片
        """
        self.agent_card = agent_card
        self.tasks: dict[str, A2ATask] = {}

    def get_agent_card(self) -> dict[str, Any]:
        """获取 Agent 卡片"""
        return self.agent_card.to_dict()

    def create_task(self, instruction: str, context: str | None = None) -> A2ATask:
        """创建新任务

        Args:
            instruction: 任务指令
            context: 上下文标识符

        Returns:
            新创建的任务
        """
        task = A2ATask(instruction=instruction, context=context)
        self.tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> A2ATask | None:
        """获取任务

        Args:
            task_id: 任务 ID

        Returns:
            任务对象，如果不存在返回 None
        """
        return self.tasks.get(task_id)

    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """更新任务状态

        Args:
            task_id: 任务 ID
            status: 新状态

        Returns:
            是否更新成功
        """
        task = self.get_task(task_id)
        if task:
            task.status = status
            task.updated_at = datetime.now().isoformat()
            return True
        return False


class A2AClient:
    """A2A 客户端

    向其他 Agent 发送任务请求。
    """

    def __init__(self, local_agent_name: str = "local-agent") -> None:
        """初始化 A2A 客户端

        Args:
            local_agent_name: 本地 Agent 名称
        """
        self.local_agent_name = local_agent_name
        self.discovered_agents: dict[str, AgentCard] = {}

    def register_agent(self, agent_card: AgentCard) -> None:
        """注册 Agent

        Args:
            agent_card: Agent 卡片
        """
        self.discovered_agents[agent_card.name] = agent_card

    def get_agent_by_skill(self, skill_name: str) -> AgentCard | None:
        """根据技能查找 Agent

        Args:
            skill_name: 技能名称

        Returns:
            Agent 卡片，如果未找到返回 None
        """
        for agent in self.discovered_agents.values():
            for skill in agent.skills:
                if skill.name == skill_name:
                    return agent
        return None

    def create_task_for_agent(
        self,
        agent_name: str,
        instruction: str,
        context: str | None = None,
    ) -> A2ATask:
        """为指定 Agent 创建任务

        Args:
            agent_name: Agent 名称
            instruction: 任务指令
            context: 上下文标识符

        Returns:
            新创建的任务
        """
        task = A2ATask(instruction=instruction, context=context)
        task.metadata["target_agent"] = agent_name
        task.metadata["source_agent"] = self.local_agent_name
        return task


def create_wechat_summarizer_agent_card() -> AgentCard:
    """创建微信文章总结器的 Agent 卡片

    Returns:
        Agent 卡片
    """
    skills = [
        AgentSkill(
            name="fetch_article",
            description="抓取微信公众号文章内容",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "文章 URL"},
                },
                "required": ["url"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "author": {"type": "string"},
                },
            },
        ),
        AgentSkill(
            name="summarize_article",
            description="生成文章摘要",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "文章 URL"},
                    "method": {"type": "string", "description": "摘要方法"},
                },
                "required": ["url"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "key_points": {"type": "array", "items": {"type": "string"}},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
            },
        ),
        AgentSkill(
            name="graph_analyze",
            description="分析文章并构建知识图谱",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "文章 URL"},
                },
                "required": ["url"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "entities": {"type": "array"},
                    "relationships": {"type": "array"},
                    "communities": {"type": "array"},
                },
            },
        ),
        AgentSkill(
            name="compare_articles",
            description="对比分析多篇文章",
            input_schema={
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "文章 URL 列表",
                    },
                },
                "required": ["urls"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "common_entities": {"type": "array"},
                    "common_tags": {"type": "array"},
                },
            },
        ),
    ]

    return AgentCard(
        name="wechat-article-summarizer",
        description="微信公众号文章抓取和摘要服务，支持多种AI摘要方法、GraphRAG知识图谱分析和文章对比",
        version="2.3.0",
        endpoint="http://localhost:8000/mcp",  # MCP 服务端点
        skills=skills,
        auth_schemes=["none", "api_key"],
        metadata={
            "supported_formats": ["html", "markdown", "json"],
            "max_article_length": 100000,
            "languages": ["zh", "en"],
        },
    )
