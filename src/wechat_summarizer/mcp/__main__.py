"""MCP 服务器入口

使用方式：
    python -m wechat_summarizer.mcp
    python -m wechat_summarizer.mcp --transport http
"""

import argparse
import os

from .server import run_mcp_server


def main():
    parser = argparse.ArgumentParser(description="微信公众号文章总结器 - MCP 服务器")
    parser.add_argument(
        "--transport",
        "-t",
        choices=["stdio", "http"],
        default="stdio",
        help="传输方式 (默认: stdio)",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="HTTP 模式端口 (默认: 8000)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP 模式监听地址 (默认: 127.0.0.1)",
    )
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="允许监听非本机地址（高风险，需配合防火墙和鉴权）",
    )
    parser.add_argument(
        "--auth-token",
        default=None,
        help="HTTP 模式访问 token（请求头: X-MCP-Token）",
    )
    parser.add_argument(
        "--admin-token",
        default=None,
        help="HTTP 模式管理员 token（请求头: X-MCP-Token）",
    )

    args = parser.parse_args()

    auth_token = args.auth_token or os.environ.get("WECHAT_SUMMARIZER_MCP_AUTH_TOKEN")
    admin_token = args.admin_token or os.environ.get("WECHAT_SUMMARIZER_MCP_ADMIN_TOKEN")

    run_mcp_server(
        transport=args.transport,
        port=args.port,
        host=args.host,
        auth_token=auth_token,
        admin_token=admin_token,
        allow_remote=args.allow_remote,
    )


if __name__ == "__main__":
    main()
