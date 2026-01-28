"""MCP (Model Context Protocol) 服务模块

让本工具可以被 AI Agent（如 Claude、ChatGPT）直接调用。

使用方式：
    # 启动 MCP 服务
    python -m wechat_summarizer.mcp

    # 或通过 CLI
    wechat-summarizer mcp-server
"""

from .a2a import (
    A2AClient,
    A2AServer,
    A2ATask,
    AgentCard,
    create_wechat_summarizer_agent_card,
)
from .security import (
    AuditLogger,
    PermissionLevel,
    RateLimiter,
    SecurityManager,
    get_security_manager,
    require_permission,
    reset_security_manager,
)
from .server import mcp, run_mcp_server

__all__ = [
    # 服务器
    "mcp",
    "run_mcp_server",
    # 安全
    "PermissionLevel",
    "AuditLogger",
    "RateLimiter",
    "SecurityManager",
    "get_security_manager",
    "reset_security_manager",
    "require_permission",
    # A2A
    "AgentCard",
    "A2ATask",
    "A2AClient",
    "A2AServer",
    "create_wechat_summarizer_agent_card",
]
