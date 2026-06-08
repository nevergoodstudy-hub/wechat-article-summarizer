"""Shared MCP response helpers."""

from __future__ import annotations

from typing import Any

from ..shared.utils.security import sanitize_error_message
from .input_validator import MCPValidationError

VALIDATION_ERROR_CODE = "MCP_VALIDATION_ERROR"
BUSINESS_ERROR_CODE = "MCP_BUSINESS_ERROR"
RATE_LIMIT_ERROR_CODE = "MCP_RATE_LIMITED"
AUTHORIZATION_ERROR_CODE = "MCP_UNAUTHORIZED"


def _tool_error_response(
    *,
    error_code: str,
    error_type: str,
    message: str,
) -> dict[str, Any]:
    """Build a machine-readable MCP tool execution error response."""
    safe_message = sanitize_error_message(message)
    return {
        "success": False,
        "isError": True,
        "error_code": error_code,
        "error_type": error_type,
        "error": safe_message,
    }


def validation_error_response(exc: MCPValidationError) -> dict[str, Any]:
    """Build a consistent response for MCP input validation failures."""
    return _tool_error_response(
        error_code=VALIDATION_ERROR_CODE,
        error_type="validation",
        message=f"参数校验失败: {exc}",
    )


def business_error_response(error: Exception | str) -> dict[str, Any]:
    """Build a consistent response for recoverable business/tool execution failures."""
    return _tool_error_response(
        error_code=BUSINESS_ERROR_CODE,
        error_type="business",
        message=str(error),
    )


def rate_limit_error_response(message: str) -> dict[str, Any]:
    """Build a consistent response for MCP tool rate limiting."""
    return _tool_error_response(
        error_code=RATE_LIMIT_ERROR_CODE,
        error_type="rate_limit",
        message=message,
    )


def authorization_error_response(message: str = "Unauthorized") -> dict[str, Any]:
    """Build a consistent response for MCP HTTP transport authorization failures."""
    return _tool_error_response(
        error_code=AUTHORIZATION_ERROR_CODE,
        error_type="authorization",
        message=message,
    )


def validation_error_text(exc: MCPValidationError) -> str:
    """Build a consistent text response for MCP resources."""
    return f"参数校验失败: {exc}"
