"""MCP 输入验证器测试

覆盖 mcp/input_validator.py 中的:
- MCPInputValidator.validate_url: URL 安全验证
- MCPInputValidator.validate_urls: 批量 URL 验证
- MCPInputValidator.validate_file_path: 文件路径安全验证
- MCPInputValidator.sanitize_text: 文本清理
- MCPInputValidator.validate_method: 摘要方法白名单
- MCPInputValidator.validate_max_length: 长度参数范围校验
- MCPInputValidator.validate_no_shell_injection: shell 注入检测
- MCPInputValidator.validate_aspects: 对比维度列表验证
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from wechat_summarizer.mcp.input_validator import MCPInputValidator, MCPValidationError

# ── validate_url ───────────────────────────────────────


class TestValidateUrl:
    """URL 验证测试"""

    def test_rejects_empty_url(self):
        with pytest.raises(MCPValidationError, match="non-empty string"):
            MCPInputValidator.validate_url("")

    def test_rejects_none_url(self):
        with pytest.raises(MCPValidationError, match="non-empty string"):
            MCPInputValidator.validate_url(None)

    def test_rejects_too_long_url(self):
        url = "https://example.com/" + "a" * 2100
        with pytest.raises(MCPValidationError, match="too long"):
            MCPInputValidator.validate_url(url)

    def test_rejects_non_http_scheme(self):
        with pytest.raises(MCPValidationError, match="Disallowed URL scheme"):
            MCPInputValidator.validate_url("ftp://example.com/file")
        with pytest.raises(MCPValidationError, match="Disallowed URL scheme"):
            MCPInputValidator.validate_url("file:///etc/passwd")

    def test_rejects_missing_hostname(self):
        with pytest.raises(MCPValidationError, match="missing hostname"):
            MCPInputValidator.validate_url("http://")

    def test_rejects_shell_chars_in_hostname(self):
        with pytest.raises(MCPValidationError, match="Suspicious character"):
            MCPInputValidator.validate_url("https://evil.com;rm -rf/")

    def test_strips_invisible_unicode(self):
        """移除零宽字符后仍应正确验证"""
        with patch(
            "wechat_summarizer.shared.utils.ssrf_protection.SSRFSafeTransport.validate_url",
            return_value="https://example.com/article",
        ):
            result = MCPInputValidator.validate_url(
                "https://example.com/\u200barticle"
            )
            assert "\u200b" not in result

    def test_accepts_valid_https_url(self):
        """接受有效的 HTTPS URL（mock SSRF 检查）"""
        with patch(
            "wechat_summarizer.shared.utils.ssrf_protection.SSRFSafeTransport.validate_url",
            return_value="https://mp.weixin.qq.com/s/abc123",
        ):
            result = MCPInputValidator.validate_url(
                "https://mp.weixin.qq.com/s/abc123"
            )
            assert result == "https://mp.weixin.qq.com/s/abc123"


# ── validate_urls ──────────────────────────────────────


class TestValidateUrls:
    """批量 URL 验证测试"""

    def test_rejects_non_list(self):
        with pytest.raises(MCPValidationError, match="must be a list"):
            MCPInputValidator.validate_urls("not-a-list")

    def test_rejects_too_many_urls(self):
        urls = [f"https://example.com/{i}" for i in range(15)]
        with pytest.raises(MCPValidationError, match="Too many URLs"):
            MCPInputValidator.validate_urls(urls, max_count=10)

    def test_validates_each_url(self):
        """每个 URL 都经过验证"""
        with pytest.raises(MCPValidationError):
            MCPInputValidator.validate_urls(
                ["https://example.com/ok", "ftp://evil.com/bad"]
            )

    def test_accepts_valid_url_list(self):
        with patch(
            "wechat_summarizer.shared.utils.ssrf_protection.SSRFSafeTransport.validate_url",
            side_effect=lambda u: u,
        ):
            urls = ["https://example.com/1", "https://example.com/2"]
            result = MCPInputValidator.validate_urls(urls)
            assert len(result) == 2


# ── validate_file_path ─────────────────────────────────


class TestValidateFilePath:
    """文件路径验证测试"""

    def test_rejects_empty_path(self):
        with pytest.raises(MCPValidationError, match="non-empty string"):
            MCPInputValidator.validate_file_path("")

    def test_rejects_path_traversal(self):
        with pytest.raises(MCPValidationError, match="Path traversal"):
            MCPInputValidator.validate_file_path("../../etc/passwd")
        with pytest.raises(MCPValidationError, match="Path traversal"):
            MCPInputValidator.validate_file_path("..\\..\\windows\\system32")

    def test_rejects_null_byte(self):
        with pytest.raises(MCPValidationError, match="Null byte"):
            MCPInputValidator.validate_file_path("file\x00.txt")

    def test_rejects_path_outside_whitelist(self):
        """拒绝白名单目录外的路径"""
        with pytest.raises(MCPValidationError, match="outside allowed"):
            MCPInputValidator.validate_file_path("/etc/shadow")

    def test_accepts_path_in_whitelist(self):
        """接受白名单目录内的路径（需匹配规范化后的前缀）"""
        # PureWindowsPath("./output/x").as_posix() => "output/x",
        # 白名单 "./output" 不匹配。用 mock 设置规范化后的白名单。
        with patch.dict(
            "wechat_summarizer.mcp.security_config.MCP_SECURITY_CONFIG",
            {"allowed_dirs": ["output", "exports", "cache"]},
        ):
            result = MCPInputValidator.validate_file_path("output/report.md")
            assert result == "output/report.md"

    def test_rejects_prefix_confusion_outside_whitelist(self):
        """拒绝仅前缀相似但不在白名单目录下的路径"""
        with patch.dict(
            "wechat_summarizer.mcp.security_config.MCP_SECURITY_CONFIG",
            {"allowed_dirs": ["output"]},
        ), pytest.raises(MCPValidationError, match="outside allowed"):
            MCPInputValidator.validate_file_path("output_evil/report.md")


# ── sanitize_text ──────────────────────────────────────


class TestSanitizeText:
    """文本清理测试"""

    def test_rejects_non_string(self):
        with pytest.raises(MCPValidationError, match="must be a string"):
            MCPInputValidator.sanitize_text(123)

    def test_rejects_too_long_text(self):
        with pytest.raises(MCPValidationError, match="too long"):
            MCPInputValidator.sanitize_text("a" * 20_000, max_length=10_000)

    def test_removes_null_bytes(self):
        result = MCPInputValidator.sanitize_text("hello\x00world")
        assert "\x00" not in result
        assert "helloworld" in result

    def test_removes_invisible_unicode(self):
        result = MCPInputValidator.sanitize_text("hello\u200bworld")
        assert "\u200b" not in result

    def test_preserves_normal_text(self):
        text = "这是一篇中文文章，包含正常内容。\nHello World!"
        result = MCPInputValidator.sanitize_text(text)
        assert "中文文章" in result
        assert "Hello World!" in result

    def test_preserves_whitespace(self):
        text = "line1\nline2\ttab"
        result = MCPInputValidator.sanitize_text(text)
        assert "\n" in result
        assert "\t" in result


# ── validate_method ────────────────────────────────────


class TestValidateMethod:
    """摘要方法白名单验证测试"""

    @pytest.mark.parametrize(
        "method",
        ["simple", "textrank", "ollama", "openai", "anthropic", "zhipu", "deepseek"],
    )
    def test_accepts_valid_methods(self, method: str):
        assert MCPInputValidator.validate_method(method) == method

    def test_accepts_compound_methods(self):
        assert MCPInputValidator.validate_method("mapreduce-openai") == "mapreduce-openai"
        assert MCPInputValidator.validate_method("rag-deepseek") == "rag-deepseek"
        assert MCPInputValidator.validate_method("graphrag-ollama") == "graphrag-ollama"

    def test_normalizes_case(self):
        assert MCPInputValidator.validate_method("SIMPLE") == "simple"
        assert MCPInputValidator.validate_method("OpenAI") == "openai"

    def test_strips_whitespace(self):
        assert MCPInputValidator.validate_method("  simple  ") == "simple"

    def test_rejects_empty_method(self):
        with pytest.raises(MCPValidationError, match="non-empty string"):
            MCPInputValidator.validate_method("")

    def test_rejects_invalid_method(self):
        with pytest.raises(MCPValidationError, match="Invalid method"):
            MCPInputValidator.validate_method("injection; rm -rf /")

    def test_rejects_unknown_method(self):
        with pytest.raises(MCPValidationError, match="Invalid method"):
            MCPInputValidator.validate_method("not-a-real-method")


# ── validate_max_length ────────────────────────────────


class TestValidateMaxLength:
    """长度参数验证测试"""

    def test_accepts_in_range(self):
        assert MCPInputValidator.validate_max_length(100) == 100
        assert MCPInputValidator.validate_max_length(50, lower=50) == 50
        assert MCPInputValidator.validate_max_length(10_000, upper=10_000) == 10_000

    def test_rejects_below_lower(self):
        with pytest.raises(MCPValidationError, match="must be integer"):
            MCPInputValidator.validate_max_length(10, lower=50)

    def test_rejects_above_upper(self):
        with pytest.raises(MCPValidationError, match="must be integer"):
            MCPInputValidator.validate_max_length(20_000, upper=10_000)

    def test_rejects_non_integer(self):
        with pytest.raises(MCPValidationError, match="must be integer"):
            MCPInputValidator.validate_max_length("100")

    def test_rejects_float(self):
        with pytest.raises(MCPValidationError, match="must be integer"):
            MCPInputValidator.validate_max_length(100.5)


# ── validate_no_shell_injection ────────────────────────


class TestValidateNoShellInjection:
    """Shell 注入检测测试"""

    @pytest.mark.parametrize(
        "payload",
        [
            "normal; rm -rf /",
            "value | cat /etc/passwd",
            "input & malicious",
            "test`whoami`",
            "$(id)",
            "result > /dev/null",
        ],
    )
    def test_rejects_shell_metacharacters(self, payload: str):
        with pytest.raises(MCPValidationError, match="Shell injection"):
            MCPInputValidator.validate_no_shell_injection(payload)

    def test_accepts_safe_strings(self):
        safe_strings = [
            "normal text",
            "中文内容",
            "hello-world_123",
            "file.name.txt",
        ]
        for s in safe_strings:
            assert MCPInputValidator.validate_no_shell_injection(s) == s

    def test_rejects_non_string(self):
        with pytest.raises(MCPValidationError, match="must be a string"):
            MCPInputValidator.validate_no_shell_injection(42)


# ── validate_aspects ───────────────────────────────────


class TestValidateAspects:
    """对比维度列表验证测试"""

    def test_returns_defaults_for_none(self):
        result = MCPInputValidator.validate_aspects(None)
        assert result == ["主题", "观点", "实体"]

    def test_rejects_non_list(self):
        with pytest.raises(MCPValidationError, match="must be a list"):
            MCPInputValidator.validate_aspects("not-a-list")

    def test_rejects_too_many_aspects(self):
        aspects = [f"aspect_{i}" for i in range(15)]
        with pytest.raises(MCPValidationError, match="Too many aspects"):
            MCPInputValidator.validate_aspects(aspects, max_count=10)

    def test_sanitizes_each_aspect(self):
        """每个维度都经过文本清理"""
        result = MCPInputValidator.validate_aspects(["主题\x00", "\u200b观点"])
        assert "\x00" not in result[0]
        assert "\u200b" not in result[1]

    def test_accepts_valid_aspects(self):
        result = MCPInputValidator.validate_aspects(["主题", "情感", "实体"])
        assert len(result) == 3
