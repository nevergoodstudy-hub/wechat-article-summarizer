"""ZIP 批量导出器

支持将多篇文章打包为 ZIP 文件，包含 HTML 和可选的图片资源。
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

import httpx
from loguru import logger

from ....shared.exceptions import ExporterError
from .base import BaseExporter
from .html import HtmlExporter

if TYPE_CHECKING:
    from ....domain.entities import Article


class ZipExporter(BaseExporter):
    """
    ZIP 批量导出器

    将文章打包为 ZIP 文件，包含：
    - HTML 文件
    - 可选：下载并包含图片资源
    """

    def __init__(
        self,
        output_dir: str = "./output",
        download_images: bool = False,
        image_timeout: int = 30,
    ):
        """
        Args:
            output_dir: 输出目录
            download_images: 是否下载并包含图片
            image_timeout: 图片下载超时时间
        """
        self._output_dir = Path(output_dir)
        self._download_images = download_images
        self._image_timeout = image_timeout
        self._html_exporter = HtmlExporter(output_dir)

    @property
    def name(self) -> str:
        return "zip"

    @property
    def target(self) -> str:
        return "zip"

    def is_available(self) -> bool:
        """始终可用"""
        return True

    def export(
        self,
        article: "Article",
        path: str | None = None,
        **options,
    ) -> str:
        """导出单篇文章为 ZIP"""
        return self.export_batch([article], path, **options)

    def export_batch(
        self,
        articles: list["Article"],
        path: str | None = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        **options,
    ) -> str:
        """
        批量导出文章为 ZIP 文件

        Args:
            articles: 文章列表
            path: 输出路径（可选）
            progress_callback: 进度回调函数，接受 (current, total, item_name) 参数
            **options: 额外选项
                - download_images: 是否下载图片（覆盖初始化设置）

        Returns:
            ZIP 文件路径
        """
        download_images = options.get("download_images", self._download_images)
        total = len(articles)

        # 确定输出路径
        if path:
            output_path = Path(path)
            if output_path.is_dir():
                output_path = output_path / self._generate_zip_name(articles)
        else:
            self._output_dir.mkdir(parents=True, exist_ok=True)
            output_path = self._output_dir / self._generate_zip_name(articles)

        # 确保扩展名
        if not str(output_path).endswith(".zip"):
            output_path = Path(str(output_path) + ".zip")
        
        logger.info(f"📦 开始打包 {total} 篇文章为 ZIP...")

        try:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, article in enumerate(articles):
                    # 调用进度回调
                    if progress_callback:
                        try:
                            progress_callback(i, total, article.title[:30])
                        except Exception:
                            pass
                    
                    # 生成 HTML 内容
                    html_content = self._html_exporter._generate_html(article, **options)
                    safe_title = self._safe_filename(article.title)
                    html_filename = f"{i + 1:03d}_{safe_title}.html"

                    # 如果需要下载图片，处理图片链接
                    if download_images and article.content and article.content.images:
                        html_content, image_files = self._process_images(
                            html_content,
                            article.content.images,
                            f"{i + 1:03d}_{safe_title}",
                        )
                        # 添加图片到 ZIP
                        for img_name, img_data in image_files.items():
                            zf.writestr(f"images/{img_name}", img_data)

                    # 添加 HTML 到 ZIP
                    zf.writestr(html_filename, html_content.encode("utf-8"))
                    
                    # 记录进度日志
                    logger.debug(f"已打包 {i + 1}/{total}: {article.title[:30]}")
                
                # 最后一次进度回调
                if progress_callback:
                    try:
                        progress_callback(total, total, "生成索引文件")
                    except Exception:
                        pass

                # 添加索引文件
                index_content = self._generate_index(articles)
                zf.writestr("index.html", index_content.encode("utf-8"))

            logger.success(f"✅ ZIP 导出成功: {output_path} ({len(articles)} 篇文章)")
            return str(output_path)

        except Exception as e:
            raise ExporterError(f"ZIP 导出失败: {e}") from e

    def _generate_zip_name(self, articles: list["Article"]) -> str:
        """生成 ZIP 文件名"""
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        count = len(articles)
        return f"articles_{count}篇_{timestamp}.zip"

    def _safe_filename(self, title: str) -> str:
        """生成安全的文件名"""
        safe = re.sub(r'[\\/*?:"<>|]', "", title)
        safe = safe.strip()[:50]
        return safe or "untitled"

    def _process_images(
        self,
        html_content: str,
        images: tuple[str, ...],
        prefix: str,
    ) -> tuple[str, dict[str, bytes]]:
        """
        下载图片并替换 HTML 中的链接

        Returns:
            (修改后的 HTML, {图片文件名: 图片数据})
        """
        image_files: dict[str, bytes] = {}
        modified_html = html_content

        for i, img_url in enumerate(images):
            if not img_url:
                continue

            try:
                # 下载图片
                with httpx.Client(timeout=self._image_timeout) as client:
                    response = client.get(img_url)
                    response.raise_for_status()
                    img_data = response.content

                # 确定图片扩展名
                content_type = response.headers.get("content-type", "")
                ext = self._get_image_ext(content_type, img_url)

                # 生成文件名
                img_filename = f"{prefix}_img_{i + 1}{ext}"
                image_files[img_filename] = img_data

                # 替换 HTML 中的链接
                modified_html = modified_html.replace(
                    img_url,
                    f"images/{img_filename}",
                )

            except Exception as e:
                logger.warning(f"下载图片失败 {img_url}: {e}")
                continue

        return modified_html, image_files

    def _get_image_ext(self, content_type: str, url: str) -> str:
        """获取图片扩展名"""
        # 从 Content-Type 推断
        type_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/svg+xml": ".svg",
        }
        for mime, ext in type_map.items():
            if mime in content_type:
                return ext

        # 从 URL 推断
        url_lower = url.lower()
        for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]:
            if ext in url_lower:
                return ext if ext != ".jpeg" else ".jpg"

        return ".jpg"  # 默认

    def _generate_index(self, articles: list["Article"]) -> str:
        """生成索引页 HTML"""
        items = []
        for i, article in enumerate(articles):
            safe_title = self._safe_filename(article.title)
            html_filename = f"{i + 1:03d}_{safe_title}.html"
            items.append(f'<li><a href="{html_filename}">{article.title}</a></li>')

        items_html = "\n".join(items)

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文章索引</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{ color: #333; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 10px 0; }}
        a {{ color: #07C160; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>📚 文章索引</h1>
    <p>共 {len(articles)} 篇文章</p>
    <ul>
        {items_html}
    </ul>
</body>
</html>"""
