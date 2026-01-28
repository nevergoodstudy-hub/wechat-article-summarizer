"""MCP 服务器入口

使用方式：
    python -m wechat_summarizer.mcp
    python -m wechat_summarizer.mcp --transport http
"""

import argparse

from .server import run_mcp_server


def main():
    parser = argparse.ArgumentParser(
        description="微信公众号文章总结器 - MCP 服务器"
    )
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
    
    args = parser.parse_args()
    
    run_mcp_server(transport=args.transport)


if __name__ == "__main__":
    main()
