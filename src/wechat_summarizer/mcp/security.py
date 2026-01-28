"""MCP 安全框架

提供工具权限控制、审计日志、速率限制等安全功能。
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from pathlib import Path
from threading import Lock
from typing import Any, Callable, TypeVar

from loguru import logger
from platformdirs import user_data_dir

F = TypeVar("F", bound=Callable[..., Any])


class PermissionLevel(str, Enum):
    """权限级别"""

    READ = "read"  # 只读（查询、获取信息）
    WRITE = "write"  # 读写（创建、修改、删除）
    ADMIN = "admin"  # 管理员（配置、审计）


@dataclass
class AuditEntry:
    """审计日志条目"""

    timestamp: str
    tool_name: str
    permission: str
    caller: str
    arguments: dict[str, Any]
    result: str  # "success" 或 "error"
    error_message: str | None = None
    execution_time_ms: float = 0.0


class AuditLogger:
    """审计日志记录器"""

    def __init__(self, log_dir: Path | None = None) -> None:
        """初始化审计日志记录器

        Args:
            log_dir: 日志目录（默认使用用户数据目录）
        """
        if log_dir is None:
            log_dir = Path(user_data_dir("wechat_summarizer")) / "audit_logs"

        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def log(self, entry: AuditEntry) -> None:
        """记录审计日志

        Args:
            entry: 审计日志条目
        """
        with self._lock:
            # 按日期分文件
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"mcp_audit_{date_str}.jsonl"

            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    json.dump(
                        {
                            "timestamp": entry.timestamp,
                            "tool_name": entry.tool_name,
                            "permission": entry.permission,
                            "caller": entry.caller,
                            "arguments": self._sanitize_args(entry.arguments),
                            "result": entry.result,
                            "error_message": entry.error_message,
                            "execution_time_ms": entry.execution_time_ms,
                        },
                        f,
                        ensure_ascii=False,
                    )
                    f.write("\n")
            except Exception as e:
                logger.error(f"写入审计日志失败: {e}")

    def _sanitize_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """清洗参数（移除敏感信息）

        Args:
            args: 原始参数

        Returns:
            清洗后的参数
        """
        sanitized = {}
        sensitive_keys = {"api_key", "token", "password", "secret"}

        for key, value in args.items():
            if any(sk in key.lower() for sk in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, (str, int, float, bool, type(None))):
                sanitized[key] = value
            else:
                sanitized[key] = str(type(value).__name__)

        return sanitized

    def get_recent_logs(self, limit: int = 100) -> list[dict[str, Any]]:
        """获取最近的审计日志

        Args:
            limit: 返回条数限制

        Returns:
            审计日志列表
        """
        logs = []
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"mcp_audit_{date_str}.jsonl"

        if not log_file.exists():
            return logs

        try:
            with open(log_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))

            # 返回最近的 N 条
            return logs[-limit:]
        except Exception as e:
            logger.error(f"读取审计日志失败: {e}")
            return []


@dataclass
class RateLimiter:
    """速率限制器（令牌桶算法）"""

    max_tokens: int = 100  # 桶容量
    refill_rate: float = 10.0  # 每秒补充令牌数
    _tokens: float = field(default=100.0, init=False)
    _last_refill: float = field(default_factory=time.time, init=False)
    _lock: Lock = field(default_factory=Lock, init=False)

    def consume(self, tokens: int = 1) -> bool:
        """消费令牌

        Args:
            tokens: 消费令牌数

        Returns:
            是否成功消费
        """
        with self._lock:
            now = time.time()
            elapsed = now - self._last_refill

            # 补充令牌
            self._tokens = min(
                self.max_tokens, self._tokens + elapsed * self.refill_rate
            )
            self._last_refill = now

            # 尝试消费
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True

            return False

    def get_wait_time(self, tokens: int = 1) -> float:
        """获取等待时间（秒）

        Args:
            tokens: 需要的令牌数

        Returns:
            需要等待的秒数
        """
        with self._lock:
            if self._tokens >= tokens:
                return 0.0

            needed = tokens - self._tokens
            return needed / self.refill_rate


class SecurityManager:
    """MCP 安全管理器"""

    def __init__(
        self,
        enable_audit: bool = True,
        enable_rate_limit: bool = True,
        rate_limit_config: dict[str, Any] | None = None,
    ) -> None:
        """初始化安全管理器

        Args:
            enable_audit: 是否启用审计日志
            enable_rate_limit: 是否启用速率限制
            rate_limit_config: 速率限制配置
        """
        self.enable_audit = enable_audit
        self.enable_rate_limit = enable_rate_limit

        # 审计日志
        self.audit_logger = AuditLogger() if enable_audit else None

        # 速率限制器（按工具分别限制）
        self.rate_limiters: dict[str, RateLimiter] = defaultdict(
            lambda: RateLimiter(**(rate_limit_config or {}))
        )

        # 工具权限映射
        self.tool_permissions: dict[str, PermissionLevel] = {}

    def register_tool_permission(
        self, tool_name: str, permission: PermissionLevel
    ) -> None:
        """注册工具权限

        Args:
            tool_name: 工具名称
            permission: 权限级别
        """
        self.tool_permissions[tool_name] = permission

    def check_permission(
        self, tool_name: str, required_permission: PermissionLevel
    ) -> bool:
        """检查工具权限

        Args:
            tool_name: 工具名称
            required_permission: 需要的权限级别

        Returns:
            是否有权限
        """
        tool_perm = self.tool_permissions.get(tool_name, PermissionLevel.READ)

        # 权限等级: ADMIN > WRITE > READ
        perm_levels = {
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.ADMIN: 3,
        }

        return perm_levels[tool_perm] >= perm_levels[required_permission]

    def check_rate_limit(self, tool_name: str, tokens: int = 1) -> tuple[bool, float]:
        """检查速率限制

        Args:
            tool_name: 工具名称
            tokens: 消费令牌数

        Returns:
            (是否通过限制, 等待时间)
        """
        if not self.enable_rate_limit:
            return True, 0.0

        limiter = self.rate_limiters[tool_name]
        if limiter.consume(tokens):
            return True, 0.0

        wait_time = limiter.get_wait_time(tokens)
        return False, wait_time

    def log_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        result: str,
        execution_time_ms: float,
        error_message: str | None = None,
        caller: str = "unknown",
    ) -> None:
        """记录工具调用

        Args:
            tool_name: 工具名称
            arguments: 调用参数
            result: 调用结果（success/error）
            execution_time_ms: 执行时间（毫秒）
            error_message: 错误信息
            caller: 调用者标识
        """
        if not self.enable_audit or self.audit_logger is None:
            return

        permission = self.tool_permissions.get(tool_name, PermissionLevel.READ)

        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            tool_name=tool_name,
            permission=permission.value,
            caller=caller,
            arguments=arguments,
            result=result,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
        )

        self.audit_logger.log(entry)


# 全局安全管理器实例
_security_manager: SecurityManager | None = None


def get_security_manager() -> SecurityManager:
    """获取全局安全管理器"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


def reset_security_manager() -> None:
    """重置安全管理器（用于测试）"""
    global _security_manager
    _security_manager = None


def require_permission(permission: PermissionLevel) -> Callable[[F], F]:
    """工具权限装饰器

    Args:
        permission: 需要的权限级别

    Returns:
        装饰器函数
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            manager = get_security_manager()
            tool_name = func.__name__

            # 注册工具权限
            manager.register_tool_permission(tool_name, permission)

            # 检查速率限制
            allowed, wait_time = manager.check_rate_limit(tool_name)
            if not allowed:
                error_msg = f"速率限制：请等待 {wait_time:.2f} 秒"
                logger.warning(f"{tool_name} 触发速率限制")
                manager.log_tool_call(
                    tool_name=tool_name,
                    arguments=kwargs,
                    result="error",
                    execution_time_ms=0.0,
                    error_message=error_msg,
                )
                return {"success": False, "error": error_msg}

            # 执行工具
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time_ms = (time.time() - start_time) * 1000

                # 记录成功调用
                manager.log_tool_call(
                    tool_name=tool_name,
                    arguments=kwargs,
                    result="success",
                    execution_time_ms=execution_time_ms,
                )

                return result

            except Exception as e:
                execution_time_ms = (time.time() - start_time) * 1000

                # 记录失败调用
                manager.log_tool_call(
                    tool_name=tool_name,
                    arguments=kwargs,
                    result="error",
                    execution_time_ms=execution_time_ms,
                    error_message=str(e),
                )

                raise

        return wrapper  # type: ignore

    return decorator
