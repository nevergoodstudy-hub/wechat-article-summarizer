"""MCP 安全框架测试

覆盖：
- SecurityManager: 权限注册/检查、速率限制委托、审计日志
- RateLimiter: 令牌桶消费、补充、等待时间
- require_permission 装饰器: 权限检查 + 速率限制 + 审计
- AuditLogger: 参数清洗、日志读写
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from wechat_summarizer.mcp.security import (
    AuditEntry,
    AuditLogger,
    PermissionLevel,
    RateLimiter,
    SecurityManager,
    get_security_manager,
    require_permission,
    reset_security_manager,
)

# ============== RateLimiter ==============


class TestRateLimiter:
    """令牌桶速率限制器测试"""

    def test_consume_within_capacity(self):
        """桶内有足够令牌时消费成功"""
        limiter = RateLimiter(max_tokens=10, refill_rate=1.0)
        assert limiter.consume(1) is True

    def test_consume_exact_capacity(self):
        """消费恰好等于桶容量时成功"""
        limiter = RateLimiter(max_tokens=5, refill_rate=0.0)
        assert limiter.consume(5) is True

    def test_consume_exceeds_capacity(self):
        """消费超过桶容量时失败"""
        limiter = RateLimiter(max_tokens=5, refill_rate=0.0)
        assert limiter.consume(6) is False

    def test_consume_drains_tokens(self):
        """连续消费耗尽令牌后失败"""
        limiter = RateLimiter(max_tokens=3, refill_rate=0.0)
        assert limiter.consume(1) is True
        assert limiter.consume(1) is True
        assert limiter.consume(1) is True
        assert limiter.consume(1) is False

    def test_refill_restores_tokens(self):
        """等待后令牌自动补充"""
        limiter = RateLimiter(max_tokens=10, refill_rate=1000.0)
        # 耗尽所有令牌
        limiter.consume(10)
        assert limiter.consume(1) is False

        # 等待一小段时间让令牌补充
        time.sleep(0.02)
        assert limiter.consume(1) is True

    def test_refill_does_not_exceed_max(self):
        """补充不会超过桶容量"""
        limiter = RateLimiter(max_tokens=5, refill_rate=1000.0)
        time.sleep(0.05)
        # 即使等待了很久，也只能消费 max_tokens
        assert limiter.consume(5) is True
        assert limiter.consume(1) is False

    def test_get_wait_time_zero_when_available(self):
        """有令牌时等待时间为 0"""
        limiter = RateLimiter(max_tokens=10, refill_rate=1.0)
        assert limiter.get_wait_time(1) == 0.0

    def test_get_wait_time_positive_when_empty(self):
        """耗尽令牌后等待时间 > 0"""
        limiter = RateLimiter(max_tokens=1, refill_rate=10.0)
        limiter.consume(1)
        wait = limiter.get_wait_time(1)
        assert wait > 0.0


# ============== SecurityManager ==============


class TestSecurityManager:
    """安全管理器测试"""

    def test_register_and_check_permission(self):
        """注册权限后可以正确检查"""
        mgr = SecurityManager(enable_audit=False, enable_rate_limit=False)
        mgr.register_tool_permission("fetch_article", PermissionLevel.READ)

        assert mgr.check_permission("fetch_article", PermissionLevel.READ) is True
        assert mgr.check_permission("fetch_article", PermissionLevel.WRITE) is False

    def test_permission_hierarchy(self):
        """ADMIN > WRITE > READ 权限层级"""
        mgr = SecurityManager(enable_audit=False, enable_rate_limit=False)
        mgr.register_tool_permission("admin_tool", PermissionLevel.ADMIN)

        assert mgr.check_permission("admin_tool", PermissionLevel.READ) is True
        assert mgr.check_permission("admin_tool", PermissionLevel.WRITE) is True
        assert mgr.check_permission("admin_tool", PermissionLevel.ADMIN) is True

    def test_unregistered_tool_defaults_to_read(self):
        """未注册的工具默认 READ 权限"""
        mgr = SecurityManager(enable_audit=False, enable_rate_limit=False)

        assert mgr.check_permission("unknown_tool", PermissionLevel.READ) is True
        assert mgr.check_permission("unknown_tool", PermissionLevel.WRITE) is False

    def test_rate_limit_integration(self):
        """安全管理器正确委托速率限制"""
        mgr = SecurityManager(
            enable_audit=False,
            enable_rate_limit=True,
            rate_limit_config={"max_tokens": 2, "refill_rate": 0.0},
        )

        ok1, _ = mgr.check_rate_limit("tool_a")
        ok2, _ = mgr.check_rate_limit("tool_a")
        ok3, wait = mgr.check_rate_limit("tool_a")

        assert ok1 is True
        assert ok2 is True
        assert ok3 is False
        assert wait > 0.0

    def test_rate_limit_disabled(self):
        """禁用速率限制时始终通过"""
        mgr = SecurityManager(enable_audit=False, enable_rate_limit=False)

        for _ in range(200):
            ok, _ = mgr.check_rate_limit("tool_a")
            assert ok is True

    def test_rate_limit_per_tool_isolation(self):
        """不同工具的速率限制互相隔离"""
        mgr = SecurityManager(
            enable_audit=False,
            enable_rate_limit=True,
            rate_limit_config={"max_tokens": 1, "refill_rate": 0.0},
        )

        ok_a, _ = mgr.check_rate_limit("tool_a")
        ok_b, _ = mgr.check_rate_limit("tool_b")

        assert ok_a is True
        assert ok_b is True

        # 各自耗尽后互不影响
        ok_a2, _ = mgr.check_rate_limit("tool_a")
        ok_b2, _ = mgr.check_rate_limit("tool_b")
        assert ok_a2 is False
        assert ok_b2 is False

    def test_log_tool_call_with_audit_disabled(self):
        """审计关闭时 log_tool_call 不报错"""
        mgr = SecurityManager(enable_audit=False)
        # 应该不抛异常
        mgr.log_tool_call(
            tool_name="test",
            arguments={"url": "https://example.com"},
            result="success",
            execution_time_ms=10.0,
        )

    def test_log_tool_call_with_audit_enabled(self, tmp_path: Path):
        """审计开启时正确写入日志"""
        mgr = SecurityManager(enable_audit=True, enable_rate_limit=False)
        mgr.audit_logger = AuditLogger(log_dir=tmp_path)
        mgr.register_tool_permission("test_tool", PermissionLevel.READ)

        mgr.log_tool_call(
            tool_name="test_tool",
            arguments={"url": "https://example.com"},
            result="success",
            execution_time_ms=42.5,
            caller="test_client",
        )

        logs = mgr.audit_logger.get_recent_logs()
        assert len(logs) == 1
        assert logs[0]["tool_name"] == "test_tool"
        assert logs[0]["result"] == "success"
        assert logs[0]["execution_time_ms"] == 42.5
        assert logs[0]["caller"] == "test_client"


# ============== AuditLogger ==============


class TestAuditLogger:
    """审计日志记录器测试"""

    def test_sanitize_redacts_sensitive_keys(self, tmp_path: Path):
        """参数清洗移除敏感字段"""
        audit = AuditLogger(log_dir=tmp_path)
        sanitized = audit._sanitize_args(
            {
                "api_key": "sk-secret",
                "url": "https://example.com",
                "password": "123",
                "authorization": "Bearer abcdefghijklmnopqrstuvwxyz",
                "cookie": "sessionid=secret",
            }
        )

        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["authorization"] == "***REDACTED***"
        assert sanitized["cookie"] == "***REDACTED***"
        assert sanitized["url"] == "https://example.com"

    def test_log_redacts_sensitive_error_message(self, tmp_path: Path):
        """写入审计日志时会脱敏错误消息中的敏感值"""
        audit = AuditLogger(log_dir=tmp_path)
        entry = AuditEntry(
            timestamp="2025-01-01T00:00:00",
            tool_name="fetch",
            permission="read",
            caller="test",
            arguments={},
            result="error",
            error_message="request failed: api_key=sk-super-secret-token",
            execution_time_ms=12.0,
        )

        audit.log(entry)
        logs = audit.get_recent_logs()

        assert len(logs) == 1
        assert logs[0]["error_message"] is not None
        assert "REDACTED" in logs[0]["error_message"]
        assert "sk-super-secret-token" not in logs[0]["error_message"]

    def test_sanitize_handles_complex_types(self, tmp_path: Path):
        """清洗复杂类型时转为类型名"""
        audit = AuditLogger(log_dir=tmp_path)
        sanitized = audit._sanitize_args({"data": [1, 2, 3], "count": 42, "flag": True})

        assert sanitized["data"] == [1, 2, 3]
        assert sanitized["count"] == 42
        assert sanitized["flag"] is True

    def test_log_and_read_roundtrip(self, tmp_path: Path):
        """写入后可以正确读取"""
        audit = AuditLogger(log_dir=tmp_path)
        entry = AuditEntry(
            timestamp="2025-01-01T00:00:00",
            tool_name="fetch",
            permission="read",
            caller="test",
            arguments={"url": "https://example.com"},
            result="success",
            execution_time_ms=100.0,
        )

        audit.log(entry)
        logs = audit.get_recent_logs()

        assert len(logs) == 1
        assert logs[0]["tool_name"] == "fetch"
        assert logs[0]["arguments"]["url"] == "https://example.com"

    def test_get_recent_logs_respects_limit(self, tmp_path: Path):
        """limit 参数正确限制返回条数"""
        audit = AuditLogger(log_dir=tmp_path)

        for i in range(10):
            entry = AuditEntry(
                timestamp=f"2025-01-01T00:00:{i:02d}",
                tool_name=f"tool_{i}",
                permission="read",
                caller="test",
                arguments={},
                result="success",
            )
            audit.log(entry)

        logs = audit.get_recent_logs(limit=3)
        assert len(logs) == 3
        # 应该是最近的 3 条
        assert logs[0]["tool_name"] == "tool_7"

    def test_get_recent_logs_empty_dir(self, tmp_path: Path):
        """空目录返回空列表"""
        audit = AuditLogger(log_dir=tmp_path)
        assert audit.get_recent_logs() == []


# ============== require_permission decorator ==============


class TestRequirePermission:
    """require_permission 装饰器测试"""

    def setup_method(self):
        """每个测试前重置全局安全管理器"""
        reset_security_manager()

    def teardown_method(self):
        """每个测试后清理"""
        reset_security_manager()

    def test_decorator_allows_execution(self):
        """正常调用时装饰器不阻止执行"""

        @require_permission(PermissionLevel.READ)
        async def my_tool(url: str = "") -> dict:
            return {"success": True, "url": url}

        result = asyncio.run(my_tool(url="https://example.com"))
        assert result["success"] is True
        assert result["url"] == "https://example.com"

    def test_decorator_registers_permission(self):
        """装饰器自动注册工具权限"""

        @require_permission(PermissionLevel.WRITE)
        async def write_tool() -> dict:
            return {"done": True}

        asyncio.run(write_tool())

        mgr = get_security_manager()
        assert mgr.tool_permissions["write_tool"] == PermissionLevel.WRITE

    def test_decorator_rate_limited(self):
        """装饰器集成速率限制"""
        # 配置一个极小的令牌桶
        reset_security_manager()
        mgr = SecurityManager(
            enable_audit=False,
            enable_rate_limit=True,
            rate_limit_config={"max_tokens": 1, "refill_rate": 0.0},
        )

        # 替换全局安全管理器
        with patch("wechat_summarizer.mcp.security.get_security_manager", return_value=mgr):

            @require_permission(PermissionLevel.READ)
            async def limited_tool() -> dict:
                return {"ok": True}

            # 第一次调用成功
            r1 = asyncio.run(limited_tool())
            assert r1["ok"] is True

            # 第二次应被速率限制
            r2 = asyncio.run(limited_tool())
            assert r2.get("success") is False
            assert "速率限制" in r2.get("error", "")

    def test_decorator_propagates_exceptions(self):
        """装饰器正确传播异常"""

        @require_permission(PermissionLevel.READ)
        async def failing_tool() -> dict:
            raise ValueError("测试错误")

        with pytest.raises(ValueError, match="测试错误"):
            asyncio.run(failing_tool())


# ============== get/reset security manager ==============


class TestSecurityManagerSingleton:
    """全局安全管理器单例测试"""

    def setup_method(self):
        reset_security_manager()

    def teardown_method(self):
        reset_security_manager()

    def test_get_returns_same_instance(self):
        """多次获取返回相同实例"""
        mgr1 = get_security_manager()
        mgr2 = get_security_manager()
        assert mgr1 is mgr2

    def test_reset_creates_new_instance(self):
        """重置后返回新实例"""
        mgr1 = get_security_manager()
        reset_security_manager()
        mgr2 = get_security_manager()
        assert mgr1 is not mgr2
