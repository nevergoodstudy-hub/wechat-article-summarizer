"""MCP server 参数预处理与白名单约束测试。"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from wechat_summarizer.mcp import server
from wechat_summarizer.mcp.input_validator import MCPValidationError


def test_validate_mcp_url_accepts_allowed_host() -> None:
    """允许主机白名单内的 URL。"""
    with (
        patch(
            "wechat_summarizer.mcp.input_validator.MCPInputValidator.validate_url",
            return_value="https://mp.weixin.qq.com/s/abc123",
        ),
        patch.dict(
            "wechat_summarizer.mcp.security_config.MCP_SECURITY_CONFIG",
            {"allowed_network_hosts": ["mp.weixin.qq.com"]},
        ),
    ):
        assert server._validate_mcp_url("https://mp.weixin.qq.com/s/abc123") == (
            "https://mp.weixin.qq.com/s/abc123"
        )


def test_validate_mcp_url_rejects_disallowed_host() -> None:
    """拒绝 MCP 白名单外的 URL 主机。"""
    with (
        patch(
            "wechat_summarizer.mcp.input_validator.MCPInputValidator.validate_url",
            return_value="https://example.com/article",
        ),
        patch.dict(
            "wechat_summarizer.mcp.security_config.MCP_SECURITY_CONFIG",
            {"allowed_network_hosts": ["mp.weixin.qq.com"]},
        ),
        pytest.raises(MCPValidationError, match="not allowed"),
    ):
        server._validate_mcp_url("https://example.com/article")


def test_validate_mcp_urls_respects_configured_batch_limit() -> None:
    """批量 URL 校验应使用 MCP 安全配置里的数量上限。"""
    urls = [f"https://mp.weixin.qq.com/s/{i}" for i in range(3)]

    with (
        patch(
            "wechat_summarizer.mcp.input_validator.MCPInputValidator.validate_urls",
            side_effect=lambda values, max_count: values if max_count == 2 else [],
        ) as mock_validate_urls,
        patch(
            "wechat_summarizer.mcp.input_validator.MCPInputValidator.validate_url",
            side_effect=lambda url: url,
        ),
        patch.dict(
            "wechat_summarizer.mcp.security_config.MCP_SECURITY_CONFIG",
            {"allowed_network_hosts": ["mp.weixin.qq.com"], "max_batch_urls": 2},
        ),
    ):
        result = server._validate_mcp_urls(urls)

    mock_validate_urls.assert_called_once_with(urls, max_count=2)
    assert result == urls


def test_sanitize_mcp_text_allows_none() -> None:
    """可选文本字段为 None 时保持 None。"""
    assert server._sanitize_mcp_text(None) is None


def test_sanitize_mcp_text_uses_configured_length_limit() -> None:
    """文本清理应遵守配置中的长度上限。"""
    with (
        patch.dict(
            "wechat_summarizer.mcp.security_config.MCP_SECURITY_CONFIG",
            {"max_summary_length": 10_000},
        ),
        pytest.raises(MCPValidationError, match="too long"),
    ):
        server._sanitize_mcp_text("a" * 10_001, max_length_key="max_summary_length")
