"""MCP 服务器入口

使用方式：
    python -m wechat_summarizer.mcp
    python -m wechat_summarizer.mcp --transport http
"""

import argparse

from ..bootstrap import build_app_runtime
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
        help="HTTP 模式绑定主机 (默认: 127.0.0.1)",
    )

    args = parser.parse_args()

    runtime = build_app_runtime()
    run_mcp_server(
        transport=args.transport,
        port=args.port,
        host=args.host,
        runtime=runtime,
    )


if __name__ == "__main__":
    main()
