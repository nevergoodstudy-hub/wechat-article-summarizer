"""MCP 安全配置

定义 MCP 服务器的安全策略:
- 允许访问的目录白名单
- 允许访问的网络主机白名单
- 文件大小限制
- 需要确认的危险操作列表

覆盖审计问题:
- P1-7: MCP 服务器无沙箱/权限限制
"""

from __future__ import annotations

from typing import Any, cast

# MCP 安全配置（可通过环境变量或配置文件覆盖）
MCP_SECURITY_CONFIG: dict[str, Any] = {
    # 允许 MCP 工具访问的目录（相对路径和绝对路径均可）
    "allowed_dirs": [
        "./output",
        "./exports",
        "./cache",
        "./.cache",
    ],
    # 允许 MCP 工具发起网络请求的主机白名单
    "allowed_network_hosts": [
        # LLM API 端点
        "api.openai.com",
        "api.anthropic.com",
        "open.bigmodel.cn",
        "api.deepseek.com",
        # 微信文章域名
        "mp.weixin.qq.com",
        "mmbiz.qpic.cn",
        # 其他支持的文章来源
        "zhuanlan.zhihu.com",
        "www.zhihu.com",
        "www.toutiao.com",
    ],
    # 文件大小限制 (MB)
    "max_file_size_mb": 50,
    # 需要人机确认的危险操作类型
    "require_confirmation_for": [
        "export",
        "delete",
        "write",
    ],
    # 单次批量操作最大 URL 数量
    "max_batch_urls": 10,
    # 单次请求最大文本长度
    "max_text_length": 100_000,
    # 摘要最大长度上限
    "max_summary_length": 10_000,
}


def get_allowed_dirs() -> list[str]:
    """获取允许访问的目录列表"""
    return cast(list[str], MCP_SECURITY_CONFIG["allowed_dirs"])


def get_allowed_hosts() -> list[str]:
    """获取允许访问的网络主机列表"""
    return cast(list[str], MCP_SECURITY_CONFIG["allowed_network_hosts"])


def is_confirmation_required(operation: str) -> bool:
    """检查操作是否需要用户确认

    Args:
        operation: 操作类型

    Returns:
        是否需要确认
    """
    required_ops = cast(list[str], MCP_SECURITY_CONFIG["require_confirmation_for"])
    return operation.lower() in required_ops
