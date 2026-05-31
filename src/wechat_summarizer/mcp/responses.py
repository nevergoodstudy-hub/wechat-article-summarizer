"""Shared MCP response helpers."""

from __future__ import annotations

from typing import Any

from .input_validator import MCPValidationError

VALIDATION_ERROR_CODE = "MCP_VALIDATION_ERROR"


def validation_error_response(exc: MCPValidationError) -> dict[str, Any]:
    """Build a consistent response for MCP input validation failures."""
    return {
        "success": False,
        "error_code": VALIDATION_ERROR_CODE,
        "error": f"参数校验失败: {exc}",
    }


def validation_error_text(exc: MCPValidationError) -> str:
    """Build a consistent text response for MCP resources."""
    return f"参数校验失败: {exc}"
