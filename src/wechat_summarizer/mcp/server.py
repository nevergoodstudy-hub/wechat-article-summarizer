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


def build_http_app(mcp_instance: FastMCP, auth_token: str | None = None) -> Starlette:
    """Build the HTTP transport app with optional token authentication."""
    from starlette.applications import Starlette
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Mount

    class TokenAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):  # type: ignore[override]
            if auth_token:
                request_token = request.headers.get("x-mcp-token")
                if request_token != auth_token:
                    return JSONResponse(
                        {"success": False, "error": "Unauthorized"},
                        status_code=401,
                    )
            return await call_next(request)

    app = Starlette(routes=[Mount("/mcp", app=mcp_instance.sse_app())])
    app.add_middleware(TokenAuthMiddleware)
    return app


def run_mcp_server(
    transport: str = "stdio",
    port: int = 8000,
    host: str = "127.0.0.1",
    auth_token: str | None = None,
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

    if is_remote_host:
        logger.warning("MCP HTTP 正在远程监听，请确保网络隔离与鉴权配置。")

    import uvicorn

    app = build_http_app(mcp_instance, auth_token=auth_token)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_mcp_server()
