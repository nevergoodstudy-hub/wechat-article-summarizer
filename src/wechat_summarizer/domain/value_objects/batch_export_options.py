"""批量导出选项值对象

定义批量导出文章链接的配置选项。
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ExportFormat(str, Enum):
    """导出格式"""

    TXT = "txt"  # 纯文本，每行一个链接
    CSV = "csv"  # CSV格式，包含标题等元数据
    JSON = "json"  # JSON格式，完整数据
    MARKDOWN = "markdown"  # Markdown格式，带标题链接


class LinkFormat(str, Enum):
    """链接格式"""

    RAW = "raw"  # 原始链接
    MARKDOWN = "markdown"  # [标题](链接) 格式
    HTML = "html"  # <a href="链接">标题</a> 格式
    ORG = "org"  # [[链接][标题]] Org-mode格式


@dataclass(frozen=True)
class BatchExportOptions:
    """
    批量导出选项值对象
    
    配置导出文章链接时的各种选项，包括格式、路径、去重等。
    
    Attributes:
        export_format: 导出文件格式
        link_format: 链接格式（用于TXT/MARKDOWN导出）
        output_path: 输出文件路径（None时使用默认路径）
        include_metadata: 是否包含元数据（标题、日期等）
        deduplicate: 是否去重
        group_by_account: 是否按公众号分组
        include_digest: 是否包含文章摘要
        timestamp_filename: 是否在文件名中添加时间戳
    """

    export_format: ExportFormat = ExportFormat.TXT
    link_format: LinkFormat = LinkFormat.RAW
    output_path: Path | None = None
    include_metadata: bool = True
    deduplicate: bool = True
    group_by_account: bool = False
    include_digest: bool = False
    timestamp_filename: bool = True

    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        extensions = {
            ExportFormat.TXT: ".txt",
            ExportFormat.CSV: ".csv",
            ExportFormat.JSON: ".json",
            ExportFormat.MARKDOWN: ".md",
        }
        return extensions.get(self.export_format, ".txt")

    def generate_filename(
        self,
        account_name: str | None = None,
        prefix: str = "wechat_articles",
    ) -> str:
        """生成导出文件名
        
        Args:
            account_name: 公众号名称（可选）
            prefix: 文件名前缀
            
        Returns:
            生成的文件名
        """
        from datetime import datetime

        parts = [prefix]
        
        if account_name:
            # 清理文件名中的非法字符
            safe_name = "".join(
                c for c in account_name if c.isalnum() or c in "._- "
            ).strip()
            if safe_name:
                parts.append(safe_name)

        if self.timestamp_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            parts.append(timestamp)

        filename = "_".join(parts) + self.get_file_extension()
        return filename

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "export_format": self.export_format.value,
            "link_format": self.link_format.value,
            "output_path": str(self.output_path) if self.output_path else None,
            "include_metadata": self.include_metadata,
            "deduplicate": self.deduplicate,
            "group_by_account": self.group_by_account,
            "include_digest": self.include_digest,
            "timestamp_filename": self.timestamp_filename,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BatchExportOptions":
        """从字典创建实例"""
        return cls(
            export_format=ExportFormat(data.get("export_format", "txt")),
            link_format=LinkFormat(data.get("link_format", "raw")),
            output_path=Path(data["output_path"]) if data.get("output_path") else None,
            include_metadata=data.get("include_metadata", True),
            deduplicate=data.get("deduplicate", True),
            group_by_account=data.get("group_by_account", False),
            include_digest=data.get("include_digest", False),
            timestamp_filename=data.get("timestamp_filename", True),
        )

    @classmethod
    def simple_txt(cls, output_path: Path | None = None) -> "BatchExportOptions":
        """创建简单TXT导出选项"""
        return cls(
            export_format=ExportFormat.TXT,
            link_format=LinkFormat.RAW,
            output_path=output_path,
            include_metadata=False,
        )

    @classmethod
    def markdown_with_titles(
        cls, output_path: Path | None = None
    ) -> "BatchExportOptions":
        """创建带标题的Markdown导出选项"""
        return cls(
            export_format=ExportFormat.MARKDOWN,
            link_format=LinkFormat.MARKDOWN,
            output_path=output_path,
            include_metadata=True,
            include_digest=True,
        )

    @classmethod
    def full_json(cls, output_path: Path | None = None) -> "BatchExportOptions":
        """创建完整JSON导出选项"""
        return cls(
            export_format=ExportFormat.JSON,
            output_path=output_path,
            include_metadata=True,
            include_digest=True,
        )

    @classmethod
    def csv_for_analysis(cls, output_path: Path | None = None) -> "BatchExportOptions":
        """创建用于数据分析的CSV导出选项"""
        return cls(
            export_format=ExportFormat.CSV,
            output_path=output_path,
            include_metadata=True,
            include_digest=True,
            group_by_account=True,
        )

    def __str__(self) -> str:
        return (
            f"BatchExportOptions(format={self.export_format.value}, "
            f"link={self.link_format.value})"
        )

    def __repr__(self) -> str:
        return (
            f"BatchExportOptions(export_format={self.export_format!r}, "
            f"link_format={self.link_format!r}, output_path={self.output_path!r})"
        )
