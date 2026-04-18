"""MCP server composition root.

This module intentionally stays thin:

- it creates the FastMCP instance
- it wires composable toolsets and resources
- it adapts transport/runtime concerns such as HTTP auth

Business behavior should live in dedicated feature slices and tool/resource
modules instead of being inlined here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from .resources import register_article_resources
from .security import (
    PermissionLevel,
    reset_current_security_context,
    set_current_security_context,
)
from .toolsets import register_analysis_tools, register_article_tools

if TYPE_CHECKING:
    from starlette.applications import Starlette


_mcp_available = True
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    _mcp_available = False
    FastMCP = None  # type: ignore[assignment,misc]


mcp: FastMCP | None = None


def _get_mcp() -> FastMCP:
    """Create the FastMCP application instance."""
    if not _mcp_available:
        raise ImportError("MCP SDK 未安装。请运行: pip install mcp>=1.2.0")
    return FastMCP("WeChat Article Summarizer")


def _register_tools(mcp_instance: FastMCP) -> None:
    """Register all MCP toolsets."""
    register_article_tools(mcp_instance)
    register_analysis_tools(mcp_instance)


def _register_resources(mcp_instance: FastMCP) -> None:
    """Register all MCP resources."""
    register_article_resources(mcp_instance)


def _ensure_mcp() -> FastMCP:
    """Lazily build the MCP application once."""
    global mcp
    if mcp is None:
        mcp = _get_mcp()
        _register_tools(mcp)
        _register_resources(mcp)
    return mcp


def _resolve_http_permission(
    request_token: str | None,
    auth_token: str | None,
    admin_token: str | None,
) -> PermissionLevel | None:
    """Resolve a request token to the effective MCP permission level."""

    if admin_token and request_token == admin_token:
        return PermissionLevel.ADMIN

    if auth_token and request_token == auth_token:
        return PermissionLevel.READ if admin_token else PermissionLevel.ADMIN

    if not auth_token and not admin_token:
        return PermissionLevel.ADMIN

    return None


def build_http_app(
    mcp_instance: FastMCP,
    auth_token: str | None = None,
    admin_token: str | None = None,
) -> Starlette:
    """Build the HTTP transport app with optional token authentication."""
    from starlette.applications import Starlette
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Mount

    class TokenAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):  # type: ignore[override]
            request_token = request.headers.get("x-mcp-token")
            permission = _resolve_http_permission(request_token, auth_token, admin_token)
            if permission is None:
                return JSONResponse(
                    {"success": False, "error": "Unauthorized"},
                    status_code=401,
                )

            client_host = request.client.host if request.client is not None else "unknown"
            context_tokens = set_current_security_context(
                permission,
                caller=f"http:{client_host}:{permission.value}",
            )
            try:
                return await call_next(request)
            finally:
                reset_current_security_context(context_tokens)

    app = Starlette(routes=[Mount("/mcp", app=mcp_instance.sse_app())])
    app.add_middleware(TokenAuthMiddleware)
    return app


def run_mcp_server(
    transport: str = "stdio",
    port: int = 8000,
    host: str = "127.0.0.1",
    auth_token: str | None = None,
    admin_token: str | None = None,
    allow_remote: bool = False,
) -> None:
    """Run the MCP server."""
    mcp_instance = _ensure_mcp()
    logger.info(f"启动 MCP 服务器 (transport={transport})")

    if transport == "stdio":
        mcp_instance.run(transport="stdio")
        return

    if transport != "http":
        raise ValueError(f"不支持的传输方式: {transport}")

    is_remote_host = host not in {"127.0.0.1", "localhost", "::1"}
    if is_remote_host and not allow_remote:
        raise ValueError("远程监听已被禁止。若确需远程访问，请显式传入 --allow-remote。")

    if is_remote_host and not (auth_token or admin_token):
        raise ValueError("远程 HTTP MCP 必须配置 auth token 或 admin token。")

    if is_remote_host:
        logger.warning("MCP HTTP 正在远程监听，请确保网络隔离与鉴权配置。")
    if auth_token and not admin_token:
        logger.warning(
            "仅配置 auth_token 时，HTTP 客户端将继承管理员权限；可额外配置 admin_token 隔离管理工具。"
        )

    import uvicorn

    app = build_http_app(
        mcp_instance,
        auth_token=auth_token,
        admin_token=admin_token,
    )
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_mcp_server()
