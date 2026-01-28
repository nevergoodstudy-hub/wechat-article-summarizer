"""HTML导出器"""

import html
import re
from pathlib import Path

import bleach
from loguru import logger

from ....domain.entities import Article
from ....shared.exceptions import ExporterError
from .base import BaseExporter

# 安全 HTML 标签白名单
ALLOWED_TAGS = [
    "p", "div", "span", "br", "hr",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "a", "img",
    "ul", "ol", "li",
    "blockquote", "code", "pre",
    "strong", "em", "b", "i", "u",
    "table", "thead", "tbody", "tr", "th", "td",
    "figure", "figcaption",
    "section", "article",
]

# 安全属性白名单
ALLOWED_ATTRIBUTES = {
    "*": ["class", "id"],
    "a": ["href", "title", "target"],
    "img": ["src", "alt", "title", "width", "height"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan"],
}


class HtmlExporter(BaseExporter):
    """
    HTML导出器

    将文章导出为独立的HTML文件，包含样式。
    """

    def __init__(self, output_dir: str = "./output"):
        self._output_dir = Path(output_dir)

    @property
    def name(self) -> str:
        return "html"

    @property
    def target(self) -> str:
        return "html"

    def is_available(self) -> bool:
        """始终可用"""
        return True

    def export(
        self,
        article: Article,
        path: str | None = None,
        **options,
    ) -> str:
        """导出为HTML文件"""
        # 确定输出路径
        if path:
            output_path = Path(path)
            if output_path.is_dir():
                output_path = output_path / self._generate_filename(article)
        else:
            self._output_dir.mkdir(parents=True, exist_ok=True)
            output_path = self._output_dir / self._generate_filename(article)

        # 生成HTML内容
        html_content = self._generate_html(article, **options)

        # 写入文件
        try:
            output_path.write_text(html_content, encoding="utf-8")
            logger.info(f"HTML导出成功: {output_path}")
            return str(output_path)
        except Exception as e:
            raise ExporterError(f"HTML导出失败: {e}") from e

    def _generate_filename(self, article: Article) -> str:
        """生成文件名"""
        # 清理标题中的非法字符
        safe_title = re.sub(r'[\\/*?:"<>|]', "", article.title)
        safe_title = safe_title[:50]  # 限制长度
        return f"{safe_title}.html"

    def _sanitize_html(self, content: str) -> str:
        """清洗 HTML 内容，移除潜在的 XSS 攻击向量"""
        if not content:
            return ""
        return bleach.clean(
            content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True,
        )

    def _escape_text(self, text: str) -> str:
        """转义纯文本为安全的 HTML"""
        if not text:
            return ""
        return html.escape(text)

    def _generate_html(self, article: Article, **options) -> str:
        """生成HTML内容"""
        include_summary = options.get("include_summary", True)

        # 转义标题和元信息
        safe_title = self._escape_text(article.title)

        # 构建摘要部分
        summary_html = ""
        if include_summary and article.summary:
            key_points_html = ""
            if article.summary.key_points:
                # 转义每个关键点
                points = "\n".join(
                    f"<li>{self._escape_text(p)}</li>" for p in article.summary.key_points
                )
                key_points_html = f"""
                <div class="key-points">
                    <h3>📌 关键要点</h3>
                    <ul>{points}</ul>
                </div>
                """

            tags_html = ""
            if article.summary.tags:
                # 转义每个标签
                tags = " ".join(
                    f'<span class="tag">#{self._escape_text(t)}</span>'
                    for t in article.summary.tags
                )
                tags_html = f'<div class="tags">{tags}</div>'

            # 转义摘要内容
            safe_summary_content = self._escape_text(article.summary.content)
            summary_html = f"""
            <div class="summary-section">
                <h2>📝 文章摘要</h2>
                <div class="summary-content">{safe_summary_content}</div>
                {key_points_html}
                {tags_html}
            </div>
            <hr>
            """

        # 构建元信息（转义所有用户输入）
        meta_items = []
        if article.account_name:
            meta_items.append(f"公众号: {self._escape_text(article.account_name)}")
        if article.author:
            meta_items.append(f"作者: {self._escape_text(article.author)}")
        if article.publish_time:
            meta_items.append(f"发布时间: {article.publish_time_str}")
        meta_items.append(f"字数: {article.word_count}")

        meta_html = " | ".join(meta_items)

        # 清洗正文 HTML 内容
        safe_content_html = self._sanitize_html(article.content_html)

        # 转义 URL
        safe_url = self._escape_text(str(article.url))

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.8;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            font-size: 24px;
            margin-bottom: 10px;
            color: #1a1a1a;
        }}
        .meta {{
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }}
        .summary-section {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .summary-section h2 {{
            font-size: 18px;
            margin-bottom: 10px;
            color: #07C160;
        }}
        .summary-content {{
            margin-bottom: 15px;
        }}
        .key-points h3 {{
            font-size: 16px;
            margin-bottom: 10px;
        }}
        .key-points ul {{
            padding-left: 20px;
        }}
        .key-points li {{
            margin-bottom: 5px;
        }}
        .tags {{
            margin-top: 15px;
        }}
        .tag {{
            display: inline-block;
            background: #07C160;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 5px;
        }}
        hr {{
            border: none;
            border-top: 1px solid #eee;
            margin: 20px 0;
        }}
        .content {{
            font-size: 16px;
        }}
        .content img {{
            max-width: 100%;
            height: auto;
            margin: 10px 0;
        }}
        .content p {{
            margin-bottom: 1em;
        }}
        .content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 14px;
        }}
        .content table th,
        .content table td {{
            border: 1px solid #ddd;
            padding: 10px 12px;
            text-align: left;
        }}
        .content table th {{
            background-color: #f8f9fa;
            font-weight: bold;
            color: #333;
        }}
        .content table tr:nth-child(even) {{
            background-color: #fafafa;
        }}
        .content table tr:hover {{
            background-color: #f5f5f5;
        }}
        .source {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #999;
        }}
        .source a {{
            color: #07C160;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{safe_title}</h1>
        <div class="meta">{meta_html}</div>
        {summary_html}
        <div class="content">
            {safe_content_html}
        </div>
        <div class="source">
            原文链接: <a href="{safe_url}" target="_blank">{safe_url}</a>
        </div>
    </div>
</body>
</html>"""
