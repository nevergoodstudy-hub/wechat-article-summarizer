"""MCP 安全配置测试

测试 security_config 模块的配置读取与权限判断。
"""

from __future__ import annotations

import pytest

from wechat_summarizer.mcp.security_config import (
    MCP_SECURITY_CONFIG,
    get_allowed_dirs,
    get_allowed_hosts,
    get_int_limit,
    get_max_aspect_length,
    get_max_aspects,
    get_max_audit_logs,
    get_max_batch_urls,
    get_max_summary_length,
    get_max_text_length,
    get_max_topic_length,
    get_network_access_policy,
    is_confirmation_required,
    is_host_allowed,
    is_human_confirmation_valid,
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

    @pytest.mark.unit
    def test_host_allowlist_requires_exact_match_by_default(self) -> None:
        """默认主机白名单使用精确匹配，避免后缀混淆"""
        assert is_host_allowed("mp.weixin.qq.com") is True
        assert is_host_allowed("MP.WEIXIN.QQ.COM.") is True
        assert is_host_allowed("evil-mp.weixin.qq.com") is False
        assert is_host_allowed("example.com") is False

    @pytest.mark.unit
    def test_host_allowlist_supports_explicit_wildcards(self) -> None:
        """显式通配符只允许子域名，不允许裸域名"""
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setitem(MCP_SECURITY_CONFIG, "allowed_network_hosts", ["*.example.com"])
            assert is_host_allowed("api.example.com") is True
            assert is_host_allowed("deep.api.example.com") is True
            assert is_host_allowed("example.com") is False

    @pytest.mark.unit
    def test_network_policy_uses_configured_allowed_hosts(self) -> None:
        """MCP 主机策略应由统一网络策略入口提供。"""
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setitem(MCP_SECURITY_CONFIG, "allowed_network_hosts", ["api.example.com"])
            policy = get_network_access_policy()

            assert policy.is_host_allowed("api.example.com") is True
            assert policy.is_host_allowed("other.example.com") is False

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

    @pytest.mark.unit
    def test_human_confirmation_policy(self) -> None:
        """危险操作需要显式确认，普通操作直接通过"""
        assert is_human_confirmation_valid("export", confirmed=False) is False
        assert is_human_confirmation_valid("export", confirmed=True) is True
        assert is_human_confirmation_valid("read", confirmed=False) is True

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

    @pytest.mark.unit
    def test_named_limit_helpers_return_config_values(self) -> None:
        """命名限制 helper 应直接反映安全配置"""
        assert get_max_batch_urls() == MCP_SECURITY_CONFIG["max_batch_urls"]
        assert get_max_text_length() == MCP_SECURITY_CONFIG["max_text_length"]
        assert get_max_summary_length() == MCP_SECURITY_CONFIG["max_summary_length"]
        assert get_max_topic_length() == MCP_SECURITY_CONFIG["max_topic_length"]
        assert get_max_aspect_length() == MCP_SECURITY_CONFIG["max_aspect_length"]
        assert get_max_aspects() == MCP_SECURITY_CONFIG["max_aspects"]
        assert get_max_audit_logs() == MCP_SECURITY_CONFIG["max_audit_logs"]

    @pytest.mark.unit
    def test_get_int_limit_rejects_non_integer_config(self) -> None:
        """安全限制必须是整数，避免运行期静默降级"""
        with (
            pytest.MonkeyPatch.context() as monkeypatch,
            pytest.raises(TypeError, match="must be an integer"),
        ):
            monkeypatch.setitem(MCP_SECURITY_CONFIG, "max_batch_urls", "10")
            get_int_limit("max_batch_urls")
