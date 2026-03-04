"""MCP 安全配置测试

测试 security_config 模块的配置读取与权限判断。
"""

from __future__ import annotations

import pytest

from wechat_summarizer.mcp.security_config import (
    MCP_SECURITY_CONFIG,
    get_allowed_dirs,
    get_allowed_hosts,
    is_confirmation_required,
)


class TestMCPSecurityConfig:
    """MCP 安全配置测试"""

    # ---- get_allowed_dirs ----

    @pytest.mark.unit
    def test_allowed_dirs_returns_list(self) -> None:
        """返回列表类型"""
        dirs = get_allowed_dirs()
        assert isinstance(dirs, list)
        assert len(dirs) > 0

    @pytest.mark.unit
    def test_allowed_dirs_contains_expected_paths(self) -> None:
        """包含预期的目录路径"""
        dirs = get_allowed_dirs()
        assert "./output" in dirs
        assert "./exports" in dirs

    # ---- get_allowed_hosts ----

    @pytest.mark.unit
    def test_allowed_hosts_returns_list(self) -> None:
        """返回列表类型"""
        hosts = get_allowed_hosts()
        assert isinstance(hosts, list)
        assert len(hosts) > 0

    @pytest.mark.unit
    def test_allowed_hosts_contains_wechat(self) -> None:
        """包含微信域名"""
        hosts = get_allowed_hosts()
        assert "mp.weixin.qq.com" in hosts

    @pytest.mark.unit
    def test_allowed_hosts_contains_llm_endpoints(self) -> None:
        """包含 LLM API 端点"""
        hosts = get_allowed_hosts()
        assert "api.openai.com" in hosts
        assert "api.anthropic.com" in hosts

    # ---- is_confirmation_required ----

    @pytest.mark.unit
    def test_export_requires_confirmation(self) -> None:
        """export 操作需要确认"""
        assert is_confirmation_required("export") is True

    @pytest.mark.unit
    def test_delete_requires_confirmation(self) -> None:
        """delete 操作需要确认"""
        assert is_confirmation_required("delete") is True

    @pytest.mark.unit
    def test_write_requires_confirmation(self) -> None:
        """write 操作需要确认"""
        assert is_confirmation_required("write") is True

    @pytest.mark.unit
    def test_read_does_not_require_confirmation(self) -> None:
        """read 操作不需要确认"""
        assert is_confirmation_required("read") is False

    @pytest.mark.unit
    def test_case_insensitive(self) -> None:
        """操作名称大小写不敏感"""
        assert is_confirmation_required("EXPORT") is True
        assert is_confirmation_required("Delete") is True
        assert is_confirmation_required("WRITE") is True

    @pytest.mark.unit
    def test_unknown_operation_no_confirmation(self) -> None:
        """未知操作不需要确认"""
        assert is_confirmation_required("summarize") is False
        assert is_confirmation_required("fetch") is False

    # ---- config limits ----

    @pytest.mark.unit
    def test_max_batch_urls_limit(self) -> None:
        """批量 URL 数量上限"""
        assert MCP_SECURITY_CONFIG["max_batch_urls"] > 0

    @pytest.mark.unit
    def test_max_text_length_limit(self) -> None:
        """文本长度上限"""
        assert MCP_SECURITY_CONFIG["max_text_length"] > 0

    @pytest.mark.unit
    def test_max_file_size_limit(self) -> None:
        """文件大小上限"""
        assert MCP_SECURITY_CONFIG["max_file_size_mb"] > 0
