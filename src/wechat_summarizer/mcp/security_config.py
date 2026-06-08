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

from ..shared.utils.network_policy import NetworkAccessPolicy

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
    # 单个主题参数最大文本长度
    "max_topic_length": 200,
    # 单个对比维度最大文本长度
    "max_aspect_length": 100,
    # 单次对比维度最大数量
    "max_aspects": 10,
    # 审计日志单次读取最大条数
    "max_audit_logs": 100,
}


def get_allowed_dirs() -> list[str]:
    """获取允许访问的目录列表"""
    return cast(list[str], MCP_SECURITY_CONFIG["allowed_dirs"])


def get_allowed_hosts() -> list[str]:
    """获取允许访问的网络主机列表"""
    return cast(list[str], MCP_SECURITY_CONFIG["allowed_network_hosts"])


def normalize_host(host: str) -> str:
    """Normalize a host name for allowlist comparisons."""
    return NetworkAccessPolicy.normalize_host(host)


def get_network_access_policy() -> NetworkAccessPolicy:
    """Build the MCP network policy from current security configuration."""
    return NetworkAccessPolicy(allowed_hosts=tuple(get_allowed_hosts()))


def is_host_allowed(host: str) -> bool:
    """Check whether a host is allowed by MCP network policy.

    Exact host names are supported by default. Entries prefixed with ``*.`` also
    allow their subdomains while excluding the bare parent domain.
    """
    return get_network_access_policy().is_host_allowed(host)


def get_int_limit(key: str) -> int:
    """获取 MCP 安全整数限制。"""
    value = MCP_SECURITY_CONFIG[key]
    if not isinstance(value, int):
        raise TypeError(f"MCP security limit {key!r} must be an integer")
    return value


def get_max_batch_urls() -> int:
    """获取单次批量 URL 数量上限。"""
    return get_int_limit("max_batch_urls")


def get_max_text_length() -> int:
    """获取单次请求文本长度上限。"""
    return get_int_limit("max_text_length")


def get_max_summary_length() -> int:
    """获取摘要长度上限。"""
    return get_int_limit("max_summary_length")


def get_max_topic_length() -> int:
    """获取主题参数长度上限。"""
    return get_int_limit("max_topic_length")


def get_max_aspect_length() -> int:
    """获取单个对比维度长度上限。"""
    return get_int_limit("max_aspect_length")


def get_max_aspects() -> int:
    """获取对比维度数量上限。"""
    return get_int_limit("max_aspects")


def get_max_audit_logs() -> int:
    """获取审计日志读取条数上限。"""
    return get_int_limit("max_audit_logs")


def is_confirmation_required(operation: str) -> bool:
    """检查操作是否需要用户确认

    Args:
        operation: 操作类型

    Returns:
        是否需要确认
    """
    required_ops = cast(list[str], MCP_SECURITY_CONFIG["require_confirmation_for"])
    return operation.lower() in required_ops


def is_human_confirmation_valid(operation: str, confirmed: bool = False) -> bool:
    """Return whether a dangerous operation has the required human confirmation."""
    return not is_confirmation_required(operation) or confirmed
