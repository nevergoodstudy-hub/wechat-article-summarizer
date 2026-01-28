"""批量获取CLI命令

提供微信公众号批量文章获取和导出的命令行接口。
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.prompt import Confirm

console = Console()


def _get_components():
    """获取批量获取组件（延迟导入）"""
    from ...infrastructure.adapters.wechat_batch import (
        WechatAuthManager,
        FileCredentialStorage,
        WechatArticleFetcher,
        ArticleListCache,
        LinkExporter,
    )
    
    storage = FileCredentialStorage()
    auth = WechatAuthManager(storage)
    cache = ArticleListCache()
    
    return {
        "storage": storage,
        "auth": auth,
        "fetcher": WechatArticleFetcher(auth, cache=cache),
        "cache": cache,
        "exporter": LinkExporter(),
    }


@click.group(name="mp")
def batch_mp():
    """微信公众号批量获取命令组
    
    支持登录公众平台、查看状态和缓存管理等功能。
    
    使用前需要先登录（扫码）:
        wechat-summarizer mp login
    """
    pass


@batch_mp.command()
def login():
    """登录微信公众平台（扫码）
    
    使用自己的公众号账号扫码登录，登录后可以搜索和获取其他公众号的文章。
    """
    components = _get_components()
    auth = components["auth"]
    
    if auth.is_authenticated:
        console.print("[green]已登录[/green]")
        if auth.credentials and auth.credentials.user_info:
            nickname = auth.credentials.user_info.get("nickname", "未知")
            console.print(f"当前账号: {nickname}")
        
        if not Confirm.ask("是否重新登录?"):
            return
    
    async def do_login():
        console.print("[yellow]正在获取登录二维码...[/yellow]")
        
        try:
            qr_data = await auth.get_qrcode()
            
            console.print()
            console.print(Panel(
                f"[bold]请使用微信扫描二维码登录[/bold]\n\n"
                f"二维码地址: {qr_data.qrcode_url}\n\n"
                f"[dim]提示: 请使用您自己的公众号管理员微信扫码[/dim]",
                title="登录二维码",
                border_style="blue",
            ))
            
            # 轮询扫码状态
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("等待扫码...", total=None)
                
                max_attempts = 60  # 最多等待5分钟
                for _ in range(max_attempts):
                    status, credentials = await auth.poll_scan_status(qr_data.uuid)
                    
                    if status == 0:
                        progress.update(task, description="等待扫码...")
                    elif status == 1:
                        progress.update(task, description="[yellow]已扫码，请在手机上确认...[/yellow]")
                    elif status == 2:
                        progress.update(task, description="[green]登录成功![/green]")
                        break
                    elif status == -1:
                        progress.update(task, description="[red]二维码已过期[/red]")
                        console.print("[red]登录失败：二维码已过期，请重试[/red]")
                        return
                    
                    await asyncio.sleep(2)
                else:
                    console.print("[red]登录超时，请重试[/red]")
                    return
            
            console.print()
            console.print("[green]✓ 登录成功![/green]")
            if credentials and credentials.user_info:
                console.print(f"欢迎, {credentials.user_info.get('nickname', '用户')}")
            
        except Exception as e:
            console.print(f"[red]登录失败: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(do_login())


@batch_mp.command()
def logout():
    """登出微信公众平台"""
    components = _get_components()
    auth = components["auth"]
    
    if not auth.is_authenticated:
        console.print("[yellow]当前未登录[/yellow]")
        return
    
    async def do_logout():
        await auth.logout()
        console.print("[green]✓ 已登出[/green]")
    
    asyncio.run(do_logout())


@batch_mp.command()
def status():
    """查看登录状态"""
    components = _get_components()
    auth = components["auth"]
    cache = components["cache"]
    
    table = Table(title="登录状态")
    table.add_column("项目", style="cyan")
    table.add_column("状态", style="green")
    
    if auth.is_authenticated:
        table.add_row("登录状态", "✓ 已登录")
        if auth.credentials and auth.credentials.user_info:
            table.add_row("公众号", auth.credentials.user_info.get("nickname", "未知"))
    else:
        table.add_row("登录状态", "✗ 未登录")
    
    # 缓存信息
    cache_stats = cache.get_stats()
    table.add_row("缓存状态", "启用" if cache_stats["enabled"] else "禁用")
    table.add_row("缓存公众号数", str(cache_stats["file_cache_count"]))
    table.add_row("缓存文章数", str(cache_stats["total_articles"]))
    
    console.print(table)


@batch_mp.command(name="cache")
@click.option("--clear", is_flag=True, help="清除所有缓存")
@click.option("--cleanup", is_flag=True, help="清理过期缓存")
@click.option("--list", "list_cache", is_flag=True, help="列出所有缓存")
def cache_cmd(clear: bool, cleanup: bool, list_cache: bool):
    """管理文章列表缓存
    
    示例:
        wechat-summarizer mp cache --list
        wechat-summarizer mp cache --cleanup
        wechat-summarizer mp cache --clear
    """
    components = _get_components()
    cache = components["cache"]
    
    if clear:
        if Confirm.ask("确定要清除所有缓存吗?"):
            cache.clear()
            console.print("[green]✓ 缓存已清除[/green]")
        return
    
    if cleanup:
        cleaned = cache.cleanup_expired()
        console.print(f"[green]✓ 已清理 {cleaned} 个过期缓存[/green]")
        return
    
    if list_cache:
        cached_accounts = cache.list_cached_accounts()
        
        if not cached_accounts:
            console.print("[yellow]缓存为空[/yellow]")
            return
        
        table = Table(title="缓存的公众号")
        table.add_column("公众号", style="cyan")
        table.add_column("文章数")
        table.add_column("缓存时间")
        table.add_column("状态")
        
        for acc in cached_accounts:
            status = "[red]已过期[/red]" if acc["is_expired"] else "[green]有效[/green]"
            table.add_row(
                acc["account_name"],
                f"{acc['article_count']}/{acc['total_count']}",
                acc["cached_at"][:19],
                status,
            )
        
        console.print(table)
        return
    
    # 默认显示缓存统计
    stats = cache.get_stats()
    
    table = Table(title="缓存统计")
    table.add_column("项目", style="cyan")
    table.add_column("值")
    
    table.add_row("缓存状态", "启用" if stats["enabled"] else "禁用")
    table.add_row("有效期", f"{stats['ttl_hours']} 小时")
    table.add_row("内存缓存数", str(stats["memory_cache_count"]))
    table.add_row("文件缓存数", str(stats["file_cache_count"]))
    table.add_row("总文章数", str(stats["total_articles"]))
    table.add_row("缓存大小", f"{stats['total_size_kb']} KB")
    table.add_row("缓存目录", stats["cache_dir"])
    
    console.print(table)
