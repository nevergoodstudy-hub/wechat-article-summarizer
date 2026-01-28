"""链接导出器

导出文章链接到各种格式的文件。
支持 TXT、CSV、JSON、Markdown 格式。
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from ....application.ports.outbound.batch_export_port import BatchExportPort
from ....domain.entities.article_list import ArticleList, ArticleListItem
from ....domain.value_objects.batch_export_options import (
    BatchExportOptions,
    ExportFormat,
    LinkFormat,
)
from ....infrastructure.config.settings import get_settings


class LinkExporter:
    """
    链接导出器
    
    将文章列表导出到各种格式的文件。
    
    支持的导出格式：
    - TXT: 纯文本，每行一个链接
    - CSV: 表格格式，包含标题、链接、日期等
    - JSON: 完整数据的JSON格式
    - Markdown: 带链接的Markdown列表
    
    使用方法:
        exporter = LinkExporter()
        
        # 导出到TXT
        path = exporter.export_links(
            items,
            BatchExportOptions.simple_txt(),
            account_name="测试公众号"
        )
        print(f"已导出到: {path}")
    """

    def __init__(self, output_dir: str | Path | None = None) -> None:
        """初始化导出器
        
        Args:
            output_dir: 默认输出目录（可选）
        """
        settings = get_settings()
        
        if output_dir:
            self._output_dir = Path(output_dir)
        else:
            self._output_dir = Path(settings.export.default_output_dir)
        
        # 确保输出目录存在
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def export_links(
        self,
        items: list[ArticleListItem],
        options: BatchExportOptions,
        account_name: str | None = None,
    ) -> Path:
        """导出文章链接
        
        Args:
            items: 要导出的文章列表
            options: 导出选项
            account_name: 公众号名称（用于文件命名）
            
        Returns:
            导出文件的路径
        """
        # 去重
        if options.deduplicate:
            seen_links = set()
            unique_items = []
            for item in items:
                if item.link not in seen_links:
                    seen_links.add(item.link)
                    unique_items.append(item)
            items = unique_items
        
        # 确定输出路径
        output_path = self._resolve_output_path(options, account_name)
        
        # 根据格式导出
        if options.export_format == ExportFormat.TXT:
            self._export_txt(items, output_path, options)
        elif options.export_format == ExportFormat.CSV:
            self._export_csv(items, output_path, options, account_name)
        elif options.export_format == ExportFormat.JSON:
            self._export_json(items, output_path, options, account_name)
        elif options.export_format == ExportFormat.MARKDOWN:
            self._export_markdown(items, output_path, options, account_name)
        else:
            raise ValueError(f"不支持的导出格式: {options.export_format}")
        
        logger.info(f"已导出 {len(items)} 条链接到 {output_path}")
        return output_path

    def export_article_list(
        self,
        article_list: ArticleList,
        options: BatchExportOptions,
    ) -> Path:
        """导出文章列表聚合
        
        Args:
            article_list: 文章列表聚合
            options: 导出选项
            
        Returns:
            导出文件的路径
        """
        return self.export_links(
            article_list.items,
            options,
            account_name=article_list.account_name,
        )

    def export_multiple_accounts(
        self,
        article_lists: list[ArticleList],
        options: BatchExportOptions,
    ) -> Path:
        """导出多个公众号的文章
        
        Args:
            article_lists: 多个公众号的文章列表
            options: 导出选项
            
        Returns:
            导出文件的路径
        """
        if options.group_by_account:
            # 按公众号分组导出
            return self._export_grouped(article_lists, options)
        else:
            # 合并所有文章导出
            all_items = []
            for article_list in article_lists:
                all_items.extend(article_list.items)
            return self.export_links(all_items, options)

    def _export_grouped(
        self,
        article_lists: list[ArticleList],
        options: BatchExportOptions,
    ) -> Path:
        """按公众号分组导出"""
        output_path = self._resolve_output_path(options, None)
        
        if options.export_format == ExportFormat.JSON:
            # JSON格式分组
            data = {
                "exported_at": datetime.now().isoformat(),
                "total_accounts": len(article_lists),
                "total_articles": sum(al.count for al in article_lists),
                "accounts": [al.to_dict() for al in article_lists],
            }
            output_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            
        elif options.export_format == ExportFormat.MARKDOWN:
            # Markdown格式分组
            lines = [
                f"# 微信公众号文章导出",
                f"",
                f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"",
                f"共 {len(article_lists)} 个公众号, "
                f"{sum(al.count for al in article_lists)} 篇文章",
                f"",
            ]
            
            for article_list in article_lists:
                lines.append(f"## {article_list.account_name}")
                lines.append(f"")
                lines.append(f"共 {article_list.count} 篇文章")
                lines.append(f"")
                
                for item in article_list.items:
                    formatted = self.format_link(item, options)
                    lines.append(f"- {formatted}")
                
                lines.append(f"")
            
            output_path.write_text("\n".join(lines), encoding="utf-8")
            
        elif options.export_format == ExportFormat.CSV:
            # CSV格式分组（添加公众号列）
            with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                
                # 表头
                headers = ["公众号", "标题", "链接", "发布日期"]
                if options.include_digest:
                    headers.append("摘要")
                writer.writerow(headers)
                
                # 数据
                for article_list in article_lists:
                    for item in article_list.items:
                        row = [
                            article_list.account_name,
                            item.title,
                            item.link,
                            item.publish_date_str,
                        ]
                        if options.include_digest:
                            row.append(item.digest)
                        writer.writerow(row)
        else:
            # TXT格式分组
            lines = []
            for article_list in article_lists:
                lines.append(f"=== {article_list.account_name} ===")
                for item in article_list.items:
                    lines.append(self.format_link(item, options))
                lines.append("")
            
            output_path.write_text("\n".join(lines), encoding="utf-8")
        
        logger.info(f"已导出 {len(article_lists)} 个公众号到 {output_path}")
        return output_path

    def format_link(
        self,
        item: ArticleListItem,
        options: BatchExportOptions,
    ) -> str:
        """格式化单个链接
        
        Args:
            item: 文章列表项
            options: 导出选项
            
        Returns:
            格式化后的链接字符串
        """
        if options.link_format == LinkFormat.RAW:
            return item.link
        
        elif options.link_format == LinkFormat.MARKDOWN:
            return f"[{item.title}]({item.link})"
        
        elif options.link_format == LinkFormat.HTML:
            # 转义HTML特殊字符
            title = (
                item.title
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
            )
            return f'<a href="{item.link}">{title}</a>'
        
        elif options.link_format == LinkFormat.ORG:
            return f"[[{item.link}][{item.title}]]"
        
        else:
            return item.link

    def _resolve_output_path(
        self,
        options: BatchExportOptions,
        account_name: str | None,
    ) -> Path:
        """解析输出文件路径"""
        if options.output_path:
            return options.output_path
        
        filename = options.generate_filename(account_name)
        return self._output_dir / filename

    def _export_txt(
        self,
        items: list[ArticleListItem],
        output_path: Path,
        options: BatchExportOptions,
    ) -> None:
        """导出为TXT格式"""
        lines = []
        
        for item in items:
            formatted = self.format_link(item, options)
            
            if options.include_metadata and options.link_format == LinkFormat.RAW:
                # 添加标题注释
                lines.append(f"# {item.title} ({item.publish_date_str})")
            
            lines.append(formatted)
            
            if options.include_metadata and options.link_format == LinkFormat.RAW:
                lines.append("")  # 空行分隔
        
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def _export_csv(
        self,
        items: list[ArticleListItem],
        output_path: Path,
        options: BatchExportOptions,
        account_name: str | None,
    ) -> None:
        """导出为CSV格式"""
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            
            # 表头
            headers = ["标题", "链接", "发布日期"]
            if options.include_digest:
                headers.append("摘要")
            if options.include_metadata:
                headers.extend(["文章ID", "是否原创"])
            writer.writerow(headers)
            
            # 数据
            for item in items:
                row = [item.title, item.link, item.publish_date_str]
                if options.include_digest:
                    row.append(item.digest)
                if options.include_metadata:
                    row.extend([item.aid, "是" if item.is_original else "否"])
                writer.writerow(row)

    def _export_json(
        self,
        items: list[ArticleListItem],
        output_path: Path,
        options: BatchExportOptions,
        account_name: str | None,
    ) -> None:
        """导出为JSON格式"""
        data = {
            "exported_at": datetime.now().isoformat(),
            "account_name": account_name,
            "total_count": len(items),
            "articles": [item.to_dict() for item in items],
        }
        
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _export_markdown(
        self,
        items: list[ArticleListItem],
        output_path: Path,
        options: BatchExportOptions,
        account_name: str | None,
    ) -> None:
        """导出为Markdown格式"""
        lines = []
        
        # 标题
        if account_name:
            lines.append(f"# {account_name} 文章列表")
        else:
            lines.append("# 微信公众号文章列表")
        
        lines.append("")
        lines.append(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"共 {len(items)} 篇文章")
        lines.append("")
        
        # 文章列表
        current_date = ""
        
        for item in items:
            # 按日期分组
            if options.include_metadata and item.publish_date_str != current_date:
                current_date = item.publish_date_str
                lines.append(f"## {current_date}")
                lines.append("")
            
            # 文章条目
            formatted = self.format_link(item, options)
            lines.append(f"- {formatted}")
            
            if options.include_digest and item.digest:
                # 添加摘要作为子项
                lines.append(f"  > {item.digest[:100]}...")
        
        output_path.write_text("\n".join(lines), encoding="utf-8")
