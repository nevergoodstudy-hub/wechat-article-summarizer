"""CLI主应用 - 基于Click和Rich"""

from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ...infrastructure.config import get_container, get_settings
from ...shared.constants import VERSION
from ...shared.utils import setup_logger

console = Console()


def _process_single(
    url: str,
    method: str = "simple",
    no_summary: bool = False,
    export: str | None = None,
    output: str | None = None,
) -> None:
    """抓取并处理单篇文章（CLI/别名命令复用）"""
    container = get_container()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # 抓取文章
        task = progress.add_task("正在抓取文章...", total=None)

        try:
            article = container.fetch_use_case.execute(url)
            progress.update(task, description="[green]抓取成功")
        except Exception as e:
            console.print(f"[red]抓取失败: {e}")
            sys.exit(1)

        # 生成摘要
        if not no_summary:
            progress.update(task, description="正在生成摘要...")
            try:
                summary = container.summarize_use_case.execute(article, method=method)
                article.attach_summary(summary)
                progress.update(task, description="[green]摘要生成成功")
            except Exception as e:
                console.print(f"[yellow]摘要生成失败: {e}")

        # 导出
        if export:
            progress.update(task, description="正在导出...")
            try:
                result = container.export_use_case.execute(article, target=export, path=output)
                progress.update(task, description=f"[green]已导出: {result}")
            except Exception as e:
                console.print(f"[red]导出失败: {e}")

    # 显示结果
    _display_article(article)


@click.group()
@click.version_option(VERSION, prog_name="wechat-summarizer")
@click.option("--debug", is_flag=True, help="启用调试模式")
def cli(debug: bool):
    """微信公众号文章总结器 - 命令行工具"""
    log_level = "DEBUG" if debug else "INFO"
    setup_logger(level=log_level)


@cli.command()
@click.argument("url")
@click.option(
    "--method",
    "-m",
    default="simple",
    help="摘要方法 (simple, ollama, openai, anthropic, zhipu)",
)
@click.option("--no-summary", is_flag=True, help="不生成摘要")
@click.option(
    "--export",
    "-e",
    type=click.Choice(["html", "markdown", "word"]),
    help="导出格式",
)
@click.option("--output", "-o", type=click.Path(), help="输出文件路径")
def fetch(url: str, method: str, no_summary: bool, export: str | None, output: str | None):
    """
    抓取并处理单篇文章

    示例:
        wechat-summarizer fetch https://mp.weixin.qq.com/s/xxx
        wechat-summarizer fetch URL -m ollama -e markdown -o output.md
    """
    _process_single(url, method=method, no_summary=no_summary, export=export, output=output)


@cli.command(name="process")
@click.argument("url")
@click.option(
    "--method",
    "-m",
    default="simple",
    help="摘要方法 (simple, ollama, openai, anthropic, zhipu)",
)
@click.option("--no-summary", is_flag=True, help="不生成摘要")
@click.option(
    "--export",
    "-e",
    type=click.Choice(["html", "markdown", "word"]),
    help="导出格式",
)
@click.option("--output", "-o", type=click.Path(), help="输出文件路径")
def process(url: str, method: str, no_summary: bool, export: str | None, output: str | None):
    """process 是 fetch 的别名（为兼容旧文档/习惯写法）"""
    _process_single(url, method=method, no_summary=no_summary, export=export, output=output)


@cli.command()
@click.argument("url")
def info(url: str):
    """只抓取并展示文章信息（不生成摘要、不导出）"""
    _process_single(url, no_summary=True)


@cli.command()
def gui():
    """启动GUI"""
    try:
        from ..gui import run_gui

        run_gui()
    except ImportError as e:
        console.print(f"[red]GUI启动失败: {e}")
        console.print("请先安装GUI依赖: pip install customtkinter")


@cli.command()
@click.argument("urls", nargs=-1, required=False)
@click.option("--method", "-m", default="simple", help="摘要方法")
@click.option("--no-summary", is_flag=True, help="不生成摘要")
@click.option(
    "--export",
    "-e",
    type=click.Choice(["html", "markdown", "word"]),
    help="导出格式",
)
@click.option("--output-dir", "-o", type=click.Path(), help="输出目录")
@click.option("--input-file", "-f", type=click.Path(exists=True), help="从文件读取URL列表（每行一个URL）")
@click.option("--from-clipboard", is_flag=True, help="从剪贴板读取URL")
@click.option("--output-format", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@click.option("--quiet", "-q", is_flag=True, help="静默模式")
def batch(
    urls: tuple[str, ...],
    method: str,
    no_summary: bool,
    export: str | None,
    output_dir: str | None,
    input_file: str | None,
    from_clipboard: bool,
    output_format: str,
    quiet: bool,
):
    """
    批量处理多篇文章

    示例:
        wechat-summarizer batch URL1 URL2 URL3
        wechat-summarizer batch -f urls.txt -e markdown -o ./output
        wechat-summarizer batch --from-clipboard
    """
    import json as json_lib

    # 收集 URLs
    url_list: list[str] = list(urls) if urls else []

    # 从文件读取
    if input_file:
        with open(input_file, "r", encoding="utf-8") as f:
            file_urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            url_list.extend(file_urls)

    # 从剪贴板读取（跨平台）
    if from_clipboard:
        try:
            import platform
            import subprocess

            system = platform.system()
            if system == "Windows":
                cmd = ["powershell", "-command", "Get-Clipboard"]
            elif system == "Darwin":
                cmd = ["pbpaste"]
            else:
                # Linux 优先使用 xclip，回退 xsel
                cmd = ["xclip", "-selection", "clipboard", "-o"]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                clipboard_urls = [
                    line.strip() for line in result.stdout.split("\n")
                    if line.strip() and ("http://" in line or "https://" in line)
                ]
                url_list.extend(clipboard_urls)
        except Exception as e:
            if not quiet:
                console.print(f"[yellow]读取剪贴板失败: {e}[/yellow]")

    if not url_list:
        console.print("[red]没有提供 URL，请通过参数、--input-file 或 --from-clipboard 提供[/red]")
        sys.exit(1)

    container = get_container()

    if not quiet:
        console.print(f"[bold]开始批量处理 {len(url_list)} 篇文章...[/bold]")

    success_count = 0
    failed_count = 0
    articles = []
    results_data = []  # 用于 JSON 输出

    with Progress(console=console, disable=quiet) as progress:
        task = progress.add_task("处理中...", total=len(url_list))

        for url in url_list:
            try:
                article = container.fetch_use_case.execute(url)

                if not no_summary:
                    try:
                        summary = container.summarize_use_case.execute(article, method=method)
                        article.attach_summary(summary)
                    except Exception:
                        pass

                articles.append(article)
                success_count += 1

                results_data.append({
                    "url": url,
                    "title": article.title,
                    "success": True,
                    "word_count": article.word_count,
                })

                if not quiet:
                    console.print(f"[green]✓[/green] {article.title[:40]}...")

            except Exception as e:
                failed_count += 1
                results_data.append({
                    "url": url,
                    "success": False,
                    "error": str(e),
                })
                if not quiet:
                    console.print(f"[red]✗[/red] {url[:50]}... - {e}")

            progress.advance(task)

    # 批量导出
    exported_files = []
    if export and articles:
        if not quiet:
            console.print("\n[bold]导出文章...[/bold]")
        for article in articles:
            try:
                result = container.export_use_case.execute(
                    article,
                    target=export,
                    path=output_dir,
                )
                exported_files.append(result)
                if not quiet:
                    console.print(f"[green]已导出:[/green] {result}")
            except Exception as e:
                if not quiet:
                    console.print(f"[red]导出失败:[/red] {e}")

    # 输出结果
    if output_format == "json":
        output_data = {
            "success_count": success_count,
            "failed_count": failed_count,
            "total": len(url_list),
            "results": results_data,
            "exported_files": exported_files,
        }
        console.print(json_lib.dumps(output_data, ensure_ascii=False, indent=2))
    elif not quiet:
        console.print(f"\n[bold]处理完成:[/bold] 成功 {success_count}, 失败 {failed_count}")


@cli.command()
@click.option("--json", "output_json", is_flag=True, help="以 JSON 格式输出")
def config(output_json: bool):
    """显示当前配置"""
    import json as json_lib

    settings = get_settings()

    config_data = {
        "调试模式": settings.debug,
        "日志级别": settings.log_level,
        "默认摘要方法": settings.default_summary_method,
        "Ollama主机": settings.ollama.host,
        "Ollama模型": settings.ollama.model,
        "OpenAI模型": settings.openai.model,
        "默认输出目录": settings.export.default_output_dir,
    }

    if output_json:
        console.print(json_lib.dumps(config_data, ensure_ascii=False, indent=2))
        return

    table = Table(title="当前配置")
    table.add_column("配置项", style="cyan")
    table.add_column("值", style="green")

    for key, value in config_data.items():
        table.add_row(key, str(value))

    console.print(table)


@cli.command(name="config-init")
def config_init():
    """交互式配置向导"""
    from pathlib import Path

    console.print("[bold]🔧 配置向导[/bold]\n")

    # Ollama 配置
    console.print("[cyan]1. Ollama 配置[/cyan]")
    ollama_host = click.prompt(
        "Ollama 主机地址",
        default="http://localhost:11434",
        show_default=True,
    )
    ollama_model = click.prompt(
        "Ollama 模型名称",
        default="qwen2.5:7b",
        show_default=True,
    )

    # OpenAI 配置
    console.print("\n[cyan]2. OpenAI 配置（可选）[/cyan]")
    openai_key = click.prompt(
        "OpenAI API Key",
        default="",
        show_default=False,
        hide_input=True,
    )

    # 输出目录
    console.print("\n[cyan]3. 导出配置[/cyan]")
    output_dir = click.prompt(
        "默认输出目录",
        default="./output",
        show_default=True,
    )

    # 生成 .env 文件
    env_content = f"""# WeChat Summarizer 配置
# Ollama
WECHAT_SUMMARIZER_OLLAMA__HOST={ollama_host}
WECHAT_SUMMARIZER_OLLAMA__MODEL={ollama_model}

# OpenAI
WECHAT_SUMMARIZER_OPENAI__API_KEY={openai_key}

# 导出
WECHAT_SUMMARIZER_EXPORT__DEFAULT_OUTPUT_DIR={output_dir}
"""

    env_path = Path(".env")
    if env_path.exists():
        if not click.confirm("\n.env 文件已存在，是否覆盖？"):
            console.print("[已取消]")
            return

    env_path.write_text(env_content, encoding="utf-8")
    console.print(f"\n[green]✓ 配置已保存到 {env_path.absolute()}[/green]")
    console.print("[dim]提示: 重新运行命令以应用新配置[/dim]")


@cli.command(name="onenote-auth")
def onenote_auth():
    """OneNote 设备码授权（Microsoft Graph），并把 token 缓存到本地。"""
    container = get_container()
    exporter = container.exporters.get("onenote")
    if exporter is None or not hasattr(exporter, "authenticate"):
        console.print("[red]OneNote 导出器不可用（未加载或版本不支持）")
        sys.exit(1)

    try:
        # OneNoteExporter.authenticate() 会阻塞直到用户完成登录或超时
        msg = exporter.authenticate()  # type: ignore[attr-defined]
        console.print(Panel(msg, title="OneNote 授权提示", border_style="green"))
        console.print("[green]授权完成：现在可以使用 -e onenote 导出。[/green]")
    except Exception as e:
        console.print(f"[red]OneNote 授权失败: {e}")
        sys.exit(1)


@cli.command(name="onenote-logout")
def onenote_logout():
    """清除本地 OneNote token 缓存（相当于退出登录）。"""
    container = get_container()
    exporter = container.exporters.get("onenote")
    if exporter is None or not hasattr(exporter, "logout"):
        console.print("[red]OneNote 导出器不可用（未加载或版本不支持）")
        sys.exit(1)

    try:
        exporter.logout()  # type: ignore[attr-defined]
        console.print("[green]已清除 OneNote token 缓存。[/green]")
    except Exception as e:
        console.print(f"[red]OneNote 退出失败: {e}")
        sys.exit(1)


@cli.command(name="batch-async")
@click.argument("urls", nargs=-1, required=True)
@click.option("--method", "-m", default="simple", help="摘要方法")
@click.option("--no-summary", is_flag=True, help="不生成摘要")
@click.option(
    "--export",
    "-e",
    type=click.Choice(["html", "markdown", "obsidian", "notion", "onenote"]),
    help="导出格式",
)
@click.option("--output-dir", "-o", type=click.Path(), help="输出目录")
@click.option("--concurrency", "-c", default=5, help="最大并发数（默认5）")
def batch_async(
    urls: tuple[str, ...],
    method: str,
    no_summary: bool,
    export: str | None,
    output_dir: str | None,
    concurrency: int,
):
    """
    异步批量处理多篇文章（高并发模式）

    示例:
        wechat-summarizer batch-async URL1 URL2 URL3
        wechat-summarizer batch-async URL1 URL2 -c 10 -e markdown -o ./output
    """
    import asyncio

    from ...application.use_cases import AsyncBatchProcessUseCase
    from ...application.ports.inbound import BatchProgress

    container = get_container()

    console.print(f"[bold]开始异步批量处理 {len(urls)} 篇文章（并发数: {concurrency}）...[/bold]")

    # 获取支持异步的抓取器
    async_scrapers = [
        s for s in container.scrapers
        if hasattr(s, "scrape_async")
    ]

    if not async_scrapers:
        console.print("[red]没有可用的异步抓取器[/red]")
        sys.exit(1)

    # 创建异步批量处理用例
    use_case = AsyncBatchProcessUseCase(
        scrapers=async_scrapers,  # type: ignore
        summarizers=container.summarizers if not no_summary else None,
        storage=container.storage,
        max_concurrent=concurrency,
    )

    # 进度显示
    with Progress(console=console) as progress:
        task = progress.add_task("处理中...", total=len(urls))

        def on_progress(p: BatchProgress):
            progress.update(task, completed=p.completed)
            if p.current_url:
                short_url = p.current_url[:50] + "..." if len(p.current_url) > 50 else p.current_url
                if p.errors and p.errors[-1][0] == p.current_url:
                    console.print(f"[red]✗[/red] {short_url}")
                else:
                    console.print(f"[green]✓[/green] {short_url}")

        # 运行异步任务
        result = asyncio.run(
            use_case.process_urls(
                list(urls),
                summarize=not no_summary,
                method=method,
                on_progress=on_progress,
            )
        )

    # 批量导出
    if export and result.articles:
        console.print("\n[bold]导出文章...[/bold]")
        for article in result.articles:
            try:
                export_result = container.export_use_case.execute(
                    article,
                    target=export,
                    path=output_dir,
                )
                console.print(f"[green]已导出:[/green] {export_result}")
            except Exception as e:
                console.print(f"[red]导出失败:[/red] {e}")

    # 显示统计
    console.print(
        f"\n[bold]处理完成:[/bold] 成功 {result.success_count}, 失败 {result.failed_count}"
    )

    if result.errors:
        console.print("\n[yellow]失败详情:[/yellow]")
        for url, error in result.errors[:5]:  # 最多显示5个
            console.print(f"  • {url[:50]}...: {error}")
        if len(result.errors) > 5:
            console.print(f"  ... 还有 {len(result.errors) - 5} 个错误")


@cli.command(name="cache-clean")
@click.option("--all", "clean_all", is_flag=True, help="清理所有缓存")
@click.option("--expired", is_flag=True, default=True, help="仅清理过期缓存（默认）")
def cache_clean(clean_all: bool, expired: bool):
    """清理本地缓存"""
    container = get_container()
    storage = container.storage

    if storage is None:
        console.print("[yellow]缓存存储不可用[/yellow]")
        return

    if clean_all:
        count = storage.clear_all()
        console.print(f"[green]已清理 {count} 条缓存[/green]")
    else:
        count = storage.cleanup_expired()
        if count > 0:
            console.print(f"[green]已清理 {count} 条过期缓存[/green]")
        else:
            console.print("[dim]没有过期缓存需要清理[/dim]")


@cli.command(name="cache-stats")
def cache_stats():
    """显示缓存统计信息"""
    container = get_container()
    storage = container.storage

    if storage is None:
        console.print("[yellow]缓存存储不可用[/yellow]")
        return

    stats = storage.get_stats()

    table = Table(title="缓存统计")
    table.add_column("统计项", style="cyan")
    table.add_column("值", style="green")

    table.add_row("缓存条目数", str(stats.total_entries))

    # 格式化大小
    size_mb = stats.total_size_bytes / (1024 * 1024)
    if size_mb >= 1:
        size_str = f"{size_mb:.2f} MB"
    else:
        size_kb = stats.total_size_bytes / 1024
        size_str = f"{size_kb:.2f} KB"
    table.add_row("总大小", size_str)

    oldest = stats.oldest_entry.strftime("%Y-%m-%d %H:%M") if stats.oldest_entry else "无"
    newest = stats.newest_entry.strftime("%Y-%m-%d %H:%M") if stats.newest_entry else "无"
    table.add_row("最早缓存", oldest)
    table.add_row("最新缓存", newest)

    console.print(table)


@cli.command(name="mcp-server")
@click.option(
    "--transport",
    "-t",
    type=click.Choice(["stdio", "http"]),
    default="stdio",
    help="传输协议 (stdio 用于 AI Agent, http 用于 Web 服务)",
)
@click.option("--port", "-p", default=8000, help="HTTP 模式端口 (默认 8000)")
def mcp_server(transport: str, port: int):
    """
    启动 MCP (Model Context Protocol) 服务器

    供 AI Agent (如 Claude Desktop、Cursor) 调用本工具能力。

    示例:
        wechat-summarizer mcp-server                   # stdio 模式
        wechat-summarizer mcp-server -t http -p 9000   # HTTP 模式
    """
    try:
        from ...mcp import run_mcp_server

        console.print(f"[bold green]启动 MCP 服务器[/bold green] (transport={transport})")
        console.print("[dim]提供工具: fetch_article, summarize_article, batch_summarize, list_available_methods[/dim]")

        if transport == "http":
            console.print(f"[cyan]HTTP 端点: http://localhost:{port}/mcp[/cyan]")

        run_mcp_server(transport=transport, port=port)
    except ImportError as e:
        console.print(f"[red]MCP 服务不可用: {e}[/red]")
        console.print("请安装 MCP 依赖: pip install 'wechat-summarizer[mcp]'")
        sys.exit(1)


@cli.command()
def check():
    """检查各组件可用性"""
    container = get_container()

    console.print("[bold]检查组件状态...[/bold]\n")

    # 检查抓取器
    console.print("[cyan]抓取器:[/cyan]")
    for scraper in container.scrapers:
        console.print(f"  • {scraper.name}: [green]可用[/green]")

    # 检查摘要器
    console.print("\n[cyan]摘要器:[/cyan]")
    for name, summarizer in container.summarizers.items():
        status = "[green]可用[/green]" if summarizer.is_available() else "[red]不可用[/red]"
        console.print(f"  • {name}: {status}")

    # 检查导出器
    console.print("\n[cyan]导出器:[/cyan]")
    for name, exporter in container.exporters.items():
        status = "[green]可用[/green]" if exporter.is_available() else "[red]不可用[/red]"
        console.print(f"  • {name}: {status}")

    # 检查缓存/存储
    console.print("\n[cyan]缓存存储:[/cyan]")
    storage_status = "[green]可用[/green]" if container.storage is not None else "[red]不可用[/red]"
    console.print(f"  • local_json: {storage_status}")


def _display_article(article):
    """显示文章信息"""
    # 文章信息面板
    info_text = f"""[bold]标题:[/bold] {article.title}
[bold]公众号:[/bold] {article.account_name or "未知"}
[bold]字数:[/bold] {article.word_count}
[bold]URL:[/bold] {article.url}"""

    console.print(Panel(info_text, title="📰 文章信息", border_style="blue"))

    # 摘要面板
    if article.summary:
        summary_text = article.summary.content

        if article.summary.key_points:
            summary_text += "\n\n[bold]📌 关键要点:[/bold]\n"
            summary_text += "\n".join(f"  • {p}" for p in article.summary.key_points)

        if article.summary.tags:
            summary_text += f"\n\n[bold]🏷️ 标签:[/bold] {', '.join(article.summary.tags)}"

        console.print(Panel(summary_text, title="📝 文章摘要", border_style="green"))

    # 内容预览
    preview = (
        article.content_text[:500] + "..."
        if len(article.content_text) > 500
        else article.content_text
    )
    console.print(Panel(preview, title="📄 内容预览", border_style="dim"))


# 注册批量获取命令组
try:
    from .batch_commands import batch_mp
    cli.add_command(batch_mp)
except ImportError:
    pass  # 如果导入失败则跳过


def run_cli():
    """运行CLI"""
    cli()


if __name__ == "__main__":
    run_cli()
