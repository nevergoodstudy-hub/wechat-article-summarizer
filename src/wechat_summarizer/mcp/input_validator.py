"""MCP 工具参数输入验证器

为所有 MCP 工具参数提供严格的输入验证和清理，
防止命令注入、路径遍历、隐藏指令等攻击。

覆盖审计问题:
- P0-4: MCP 服务器缺少输入验证/命令注入风险
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath, PureWindowsPath
from urllib.parse import urlparse

from .security_config import MCP_SECURITY_CONFIG


class MCPValidationError(Exception):
    """MCP 输入验证异常"""


class MCPInputValidator:
    """MCP 工具参数验证器

    提供 URL、文件路径、文本、shell 注入等验证方法。
    所有验证方法均为类方法，无状态，可直接调用。
    """

    # 允许的 URL scheme
    ALLOWED_SCHEMES: frozenset[str] = frozenset({"http", "https"})

    # 路径遍历检测模式
    PATH_TRAVERSAL_PATTERN: re.Pattern[str] = re.compile(r"\.\.[/\\]")

    # Shell 危险字符（用于普通文本字段，不用于 URL 主机名校验）
    SHELL_DANGEROUS_CHARS: frozenset[str] = frozenset(";|&`$(){}[]!#~<>'\"\\")

    # 不可见 Unicode 控制字符（可能用于隐藏指令）
    INVISIBLE_UNICODE_PATTERN: re.Pattern[str] = re.compile(
        r"[\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff\u00ad]"
    )

    # 允许的摘要方法名（白名单）
    ALLOWED_METHODS: frozenset[str] = frozenset(
        {
            "simple",
            "textrank",
            "ollama",
            "openai",
            "anthropic",
            "zhipu",
            "deepseek",
            "mapreduce-openai",
            "mapreduce-anthropic",
            "mapreduce-zhipu",
            "mapreduce-deepseek",
            "mapreduce-ollama",
            "rag-openai",
            "rag-anthropic",
            "rag-zhipu",
            "rag-deepseek",
            "rag-ollama",
            "hyde-openai",
            "hyde-anthropic",
            "hyde-deepseek",
            "graphrag-openai",
            "graphrag-anthropic",
            "graphrag-zhipu",
            "graphrag-deepseek",
            "graphrag-ollama",
        }
    )

    @classmethod
    def validate_url(cls, url: str) -> str:
        """验证 URL 安全性

        检查 scheme 白名单、主机名有效性、SSRF 防护。

        Args:
            url: 待验证的 URL

        Returns:
            验证通过的 URL

        Raises:
            MCPValidationError: URL 不安全
        """
        if not url or not isinstance(url, str):
            raise MCPValidationError("URL must be a non-empty string")

        url = url.strip()
        if len(url) > 2048:
            raise MCPValidationError(f"URL too long: {len(url)} > 2048")

        # 移除不可见字符
        url = cls.INVISIBLE_UNICODE_PATTERN.sub("", url)

        parsed = urlparse(url)

        if parsed.scheme not in cls.ALLOWED_SCHEMES:
            raise MCPValidationError(f"Disallowed URL scheme: {parsed.scheme!r}")

        if not parsed.hostname:
            raise MCPValidationError("URL missing hostname")

        # URL 主机名格式校验（允许 IPv6 bracket 形式）
        netloc = parsed.netloc

        # 优先检测典型命令注入分隔符，便于给出明确安全错误
        suspicious_host_chars = set(";|&`$(){}!~")
        if any(ch in suspicious_host_chars for ch in netloc):
            raise MCPValidationError("Suspicious character in URL hostname")

        if any(c.isspace() for c in netloc):
            raise MCPValidationError("Invalid whitespace in URL hostname")

        # 明显非法字符（RFC 主机名场景下不应出现）
        invalid_host_chars = set("\"'<>\\^")
        if any(ch in invalid_host_chars for ch in netloc):
            raise MCPValidationError("Invalid character in URL hostname")

        # SSRF 防护（延迟导入避免循环依赖）
        from ..shared.utils.ssrf_protection import SSRFBlockedError, SSRFSafeTransport

        try:
            SSRFSafeTransport.validate_url(url)
        except SSRFBlockedError as e:
            raise MCPValidationError(f"URL blocked by SSRF protection: {e}") from e

        return url

    @classmethod
    def validate_urls(cls, urls: list[str], max_count: int = 10) -> list[str]:
        """批量验证 URL 列表

        Args:
            urls: URL 列表
            max_count: 最大允许数量

        Returns:
            验证通过的 URL 列表
        """
        if not isinstance(urls, list):
            raise MCPValidationError("URLs must be a list")

        if len(urls) > max_count:
            raise MCPValidationError(f"Too many URLs: {len(urls)} > {max_count}")

        return [cls.validate_url(url) for url in urls]

    @classmethod
    def validate_file_path(cls, path: str) -> str:
        """验证文件路径安全性

        检查路径遍历、白名单目录、shell 注入。

        Args:
            path: 文件路径

        Returns:
            验证通过的路径

        Raises:
            MCPValidationError: 路径不安全
        """
        if not path or not isinstance(path, str):
            raise MCPValidationError("Path must be a non-empty string")

        path = path.strip()

        # 路径遍历检测
        if cls.PATH_TRAVERSAL_PATTERN.search(path):
            raise MCPValidationError(f"Path traversal detected: {path}")

        # Null 字节检测
        if "\x00" in path:
            raise MCPValidationError("Null byte in path")

        # 解析路径（支持 Windows 和 POSIX）
        def _normalize_for_policy(value: str) -> str:
            try:
                normalized = PureWindowsPath(value).as_posix()
            except Exception:
                normalized = PurePosixPath(value).as_posix()
            normalized = normalized.replace("\\", "/").strip()
            normalized = normalized.lstrip("./")
            return normalized.rstrip("/")

        resolved = _normalize_for_policy(path)

        # 检查白名单目录
        allowed_dirs = MCP_SECURITY_CONFIG["allowed_dirs"]
        normalized_allowed_dirs = [_normalize_for_policy(d) for d in allowed_dirs]
        if normalized_allowed_dirs and not any(
            resolved == allowed_dir or resolved.startswith(f"{allowed_dir}/")
            for allowed_dir in normalized_allowed_dirs
            if allowed_dir
        ):
            raise MCPValidationError(f"Path outside allowed directories: {path}")

        return path

    @classmethod
    def sanitize_text(cls, text: str, max_length: int = 10_000) -> str:
        """清理文本输入

        移除 null 字节、不可见 Unicode 字符，截断过长文本。

        Args:
            text: 原始文本
            max_length: 最大长度

        Returns:
            清理后的文本

        Raises:
            MCPValidationError: 文本不安全
        """
        if not isinstance(text, str):
            raise MCPValidationError("Text must be a string")

        if len(text) > max_length:
            raise MCPValidationError(f"Input too long: {len(text)} > {max_length}")

        # 移除 null 字节
        text = text.replace("\x00", "")

        # 移除不可见 Unicode 控制字符（可能用于隐藏指令）
        text = cls.INVISIBLE_UNICODE_PATTERN.sub("", text)

        # 保留可打印字符和常见空白
        text = "".join(c for c in text if c.isprintable() or c in "\n\r\t")

        return text

    @classmethod
    def validate_method(cls, method: str) -> str:
        """验证摘要方法名（白名单校验）

        Args:
            method: 摘要方法名

        Returns:
            验证通过的方法名

        Raises:
            MCPValidationError: 方法名无效
        """
        if not method or not isinstance(method, str):
            raise MCPValidationError("Method must be a non-empty string")

        method = method.strip().lower()

        if method not in cls.ALLOWED_METHODS:
            raise MCPValidationError(
                f"Invalid method: {method!r}. Allowed: {', '.join(sorted(cls.ALLOWED_METHODS))}"
            )

        return method

    @classmethod
    def validate_max_length(cls, value: int, lower: int = 50, upper: int = 10_000) -> int:
        """验证长度参数在合理范围内

        Args:
            value: 长度值
            lower: 允许的最小值
            upper: 允许的最大值

        Returns:
            验证通过的长度值
        """
        if not isinstance(value, int) or value < lower or value > upper:
            raise MCPValidationError(
                f"max_length must be integer in [{lower}, {upper}], got {value}"
            )
        return value

    @classmethod
    def validate_int_range(
        cls,
        value: int,
        *,
        field_name: str,
        lower: int,
        upper: int,
    ) -> int:
        """验证整数参数在指定范围内"""
        if not isinstance(value, int):
            raise MCPValidationError(f"{field_name} must be an integer")
        if value < lower or value > upper:
            raise MCPValidationError(f"{field_name} must be in [{lower}, {upper}]")
        return value

    @classmethod
    def validate_no_shell_injection(cls, value: str) -> str:
        """确保值不包含 shell 注入字符

        Args:
            value: 待检查的字符串

        Returns:
            验证通过的字符串

        Raises:
            MCPValidationError: 检测到 shell 注入字符
        """
        if not isinstance(value, str):
            raise MCPValidationError("Value must be a string")

        dangerous = cls.SHELL_DANGEROUS_CHARS.intersection(value)
        if dangerous:
            raise MCPValidationError(f"Shell injection characters detected: {dangerous}")

        return value

    @classmethod
    def validate_aspects(cls, aspects: list[str] | None, max_count: int = 10) -> list[str]:
        """验证对比维度列表

        Args:
            aspects: 维度列表（可为 None）
            max_count: 最大允许数量

        Returns:
            验证通过的维度列表
        """
        if aspects is None:
            return ["主题", "观点", "实体"]

        if not isinstance(aspects, list):
            raise MCPValidationError("Aspects must be a list")

        if len(aspects) > max_count:
            raise MCPValidationError(f"Too many aspects: {len(aspects)} > {max_count}")

        return [cls.sanitize_text(a, max_length=100) for a in aspects]
