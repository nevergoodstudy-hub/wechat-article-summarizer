"""Markdown导出器"""

import re
from pathlib import Path

from loguru import logger

from ....domain.entities import Article
from ....shared.exceptions import ExporterError
from .base import BaseExporter


def _escape_yaml_value(value: str) -> str:
    """转义 YAML 值中的特殊字符

    处理的字符：
    - 双引号 -> 转义
    - 换行符 -> 空格
    - 反斜杠 -> 双反斜杠
    """
    if not value:
        return ""
    # 先处理反斜杠，再处理其他
    value = value.replace("\\", "\\\\")
    value = value.replace('"', '\\"')
    value = value.replace("\n", " ")
    value = value.replace("\r", " ")
    return value

# 延迟导入markdownify
_markdownify_available = True
try:
    from markdownify import markdownify as md
except ImportError:
    _markdownify_available = False


class MarkdownExporter(BaseExporter):
    """
    Markdown导出器

    将文章导出为Markdown格式，适合在笔记软件中使用。
    """

    def __init__(self, output_dir: str = "./output"):
        self._output_dir = Path(output_dir)

    @property
    def name(self) -> str:
        return "markdown"

    @property
    def target(self) -> str:
        return "markdown"

    def is_available(self) -> bool:
        """检查markdownify是否可用"""
        return _markdownify_available

    def export(
        self,
        article: Article,
        path: str | None = None,
        **options,
    ) -> str:
        """导出为Markdown文件"""
        if not self.is_available():
            raise ExporterError("markdownify未安装，请运行: pip install markdownify")

        # 确定输出路径
        if path:
            output_path = Path(path)
            if output_path.is_dir():
                output_path = output_path / self._generate_filename(article)
        else:
            self._output_dir.mkdir(parents=True, exist_ok=True)
            output_path = self._output_dir / self._generate_filename(article)

        # 生成Markdown内容
        md_content = self._generate_markdown(article, **options)

        # 写入文件
        try:
            output_path.write_text(md_content, encoding="utf-8")
            logger.info(f"Markdown导出成功: {output_path}")
            return str(output_path)
        except Exception as e:
            raise ExporterError(f"Markdown导出失败: {e}") from e

    def _generate_filename(self, article: Article) -> str:
        """生成文件名"""
        safe_title = re.sub(r'[\\/*?:"<>|]', "", article.title)
        safe_title = safe_title[:50]
        return f"{safe_title}.md"

    def _generate_markdown(self, article: Article, **options) -> str:
        """生成Markdown内容"""
        include_summary = options.get("include_summary", True)
        include_frontmatter = options.get("include_frontmatter", True)

        parts = []

        # YAML Front Matter（转义所有用户输入）
        if include_frontmatter:
            frontmatter_lines = [
                "---",
                f'title: "{_escape_yaml_value(article.title)}"',
            ]
            if article.account_name:
                frontmatter_lines.append(f'source: "{_escape_yaml_value(article.account_name)}"')
            if article.author:
                frontmatter_lines.append(f'author: "{_escape_yaml_value(article.author)}"')
            if article.publish_time:
                frontmatter_lines.append(f"date: {article.publish_time_str}")
            frontmatter_lines.append(f'url: "{str(article.url)}"')
            frontmatter_lines.append(f"word_count: {article.word_count}")

            if article.summary and article.summary.tags:
                # 转义每个标签
                tags = ", ".join(f'"{_escape_yaml_value(t)}"' for t in article.summary.tags)
                frontmatter_lines.append(f"tags: [{tags}]")

            frontmatter_lines.append("---")
            frontmatter_lines.append("")
            parts.append("\n".join(frontmatter_lines))

        # 标题
        parts.append(f"# {article.title}\n")

        # 元信息
        meta_items = []
        if article.account_name:
            meta_items.append(f"**公众号**: {article.account_name}")
        if article.author:
            meta_items.append(f"**作者**: {article.author}")
        if article.publish_time:
            meta_items.append(f"**发布时间**: {article.publish_time_str}")
        meta_items.append(f"**字数**: {article.word_count}")

        parts.append(" | ".join(meta_items))
        parts.append("")

        # 摘要部分
        if include_summary and article.summary:
            parts.append("---")
            parts.append("")
            parts.append("## 📝 文章摘要")
            parts.append("")
            parts.append(article.summary.content)
            parts.append("")

            if article.summary.key_points:
                parts.append("### 📌 关键要点")
                parts.append("")
                for point in article.summary.key_points:
                    parts.append(f"- {point}")
                parts.append("")

            if article.summary.tags:
                tags = " ".join(f"`#{t}`" for t in article.summary.tags)
                parts.append(f"**标签**: {tags}")
                parts.append("")

        parts.append("---")
        parts.append("")

        # 正文内容
        parts.append("## 原文内容")
        parts.append("")

        # 将HTML转换为Markdown
        if article.content_html:
            content_md = md(article.content_html, heading_style="ATX")
            # 清理多余空行
            content_md = re.sub(r"\n{3,}", "\n\n", content_md)
            parts.append(content_md)
        else:
            parts.append(article.content_text)

        parts.append("")
        parts.append("---")
        parts.append("")
        parts.append(f"[原文链接]({article.url})")

        return "\n".join(parts)
