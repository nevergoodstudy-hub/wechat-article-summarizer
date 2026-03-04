"""多格式压缩导出器

支持将多篇文章打包为多种压缩格式：
- ZIP: Python 标准库 zipfile（始终可用）
- 7z: 使用 py7zr 库（需安装）
- RAR: 需要外部 WinRAR/rar 命令行工具（因 RAR 格式专有）
"""

from __future__ import annotations

import contextlib
import io
import re
import subprocess
import tempfile
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from ....shared.exceptions import ExporterError
from .base import BaseExporter
from .html import HtmlExporter

if TYPE_CHECKING:
    from ....domain.entities import Article


class ArchiveFormat(Enum):
    """支持的压缩格式"""

    ZIP = "zip"
    SEVENZIP = "7z"
    RAR = "rar"


@dataclass
class ArchiveFormatInfo:
    """压缩格式信息"""

    format: ArchiveFormat
    name: str
    extension: str
    available: bool
    reason: str = ""

    @property
    def display_name(self) -> str:
        status = "✓" if self.available else "✗"
        return f"{status} {self.name} ({self.extension})"


class MultiFormatArchiveExporter(BaseExporter):
    """
    多格式压缩导出器

    支持将文章打包为 ZIP、7z 或 RAR 格式，包含：
    - HTML 文件
    - 可选：下载并包含图片资源
    - 索引文件
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

        # 缓存格式可用性检查结果
        self._format_availability_cache: dict[ArchiveFormat, ArchiveFormatInfo] = {}

    @property
    def name(self) -> str:
        return "archive"

    @property
    def target(self) -> str:
        return "archive"

    def is_available(self) -> bool:
        """始终可用（至少 ZIP 格式可用）"""
        return True

    def get_available_formats(self) -> list[ArchiveFormatInfo]:
        """获取所有支持的压缩格式及其可用性

        Returns:
            格式信息列表
        """
        formats = []

        # ZIP - 始终可用（Python 标准库）
        formats.append(
            ArchiveFormatInfo(
                format=ArchiveFormat.ZIP,
                name="ZIP",
                extension=".zip",
                available=True,
                reason="Python 标准库支持",
            )
        )

        # 7z - 需要 py7zr 库
        py7zr_available = self._check_py7zr_available()
        formats.append(
            ArchiveFormatInfo(
                format=ArchiveFormat.SEVENZIP,
                name="7-Zip",
                extension=".7z",
                available=py7zr_available,
                reason="py7zr 库支持" if py7zr_available else "需要安装 py7zr 库",
            )
        )

        # RAR - 需要外部工具
        rar_available, rar_reason = self._check_rar_available()
        formats.append(
            ArchiveFormatInfo(
                format=ArchiveFormat.RAR,
                name="RAR",
                extension=".rar",
                available=rar_available,
                reason=rar_reason,
            )
        )

        return formats

    def _check_py7zr_available(self) -> bool:
        """检查 py7zr 库是否可用"""
        try:
            import py7zr  # noqa: F401

            return True
        except ImportError:
            return False

    def _check_rar_available(self) -> tuple[bool, str]:
        """检查 RAR 创建工具是否可用

        Returns:
            (是否可用, 原因说明)
        """
        # 检查 WinRAR (Windows)
        rar_paths = [
            r"C:\Program Files\WinRAR\Rar.exe",
            r"C:\Program Files (x86)\WinRAR\Rar.exe",
            "rar",  # 在 PATH 中
        ]

        for rar_path in rar_paths:
            try:
                result = subprocess.run(
                    [rar_path, "-?"], capture_output=True, stdin=subprocess.DEVNULL, timeout=5
                )
                if result.returncode == 0:
                    return True, f"使用 {rar_path}"
            except subprocess.SubprocessError, FileNotFoundError, OSError:
                continue

        return False, "需要安装 WinRAR 并添加到 PATH"

    def _find_rar_executable(self) -> str | None:
        """查找可用的 RAR 可执行文件"""
        rar_paths = [
            r"C:\Program Files\WinRAR\Rar.exe",
            r"C:\Program Files (x86)\WinRAR\Rar.exe",
            "rar",
        ]

        for rar_path in rar_paths:
            try:
                result = subprocess.run(
                    [rar_path, "-?"], capture_output=True, stdin=subprocess.DEVNULL, timeout=5
                )
                if result.returncode == 0:
                    return rar_path
            except subprocess.SubprocessError, FileNotFoundError, OSError:
                continue

        return None

    def export(
        self,
        article: Article,
        path: str | None = None,
        **options,
    ) -> str:
        """导出单篇文章"""
        return self.export_batch([article], path, **options)

    def export_batch(
        self,
        articles: list[Article],
        path: str | None = None,
        archive_format: ArchiveFormat | str = ArchiveFormat.ZIP,
        progress_callback: Callable[[int, int, str], None] | None = None,
        **options,
    ) -> str:
        """
        批量导出文章为压缩文件

        Args:
            articles: 文章列表
            path: 输出路径（可选）
            archive_format: 压缩格式（'zip', '7z', 'rar' 或 ArchiveFormat 枚举）
            progress_callback: 进度回调函数，接受 (current, total, item_name) 参数
            **options: 额外选项
                - download_images: 是否下载图片（覆盖初始化设置）

        Returns:
            压缩文件路径
        """
        # 统一格式类型
        if isinstance(archive_format, str):
            format_map = {
                "zip": ArchiveFormat.ZIP,
                "7z": ArchiveFormat.SEVENZIP,
                "rar": ArchiveFormat.RAR,
            }
            archive_format = format_map.get(archive_format.lower(), ArchiveFormat.ZIP)

        # 检查格式是否可用
        formats = self.get_available_formats()
        format_info = next((f for f in formats if f.format == archive_format), None)

        if not format_info or not format_info.available:
            raise ExporterError(
                f"压缩格式 {archive_format.value} 不可用: {format_info.reason if format_info else '未知格式'}"
            )

        # 调用对应的导出方法
        if archive_format == ArchiveFormat.ZIP:
            return self._export_zip(articles, path, progress_callback, **options)
        elif archive_format == ArchiveFormat.SEVENZIP:
            return self._export_7z(articles, path, progress_callback, **options)
        elif archive_format == ArchiveFormat.RAR:
            return self._export_rar(articles, path, progress_callback, **options)
        else:
            raise ExporterError(f"不支持的压缩格式: {archive_format}")

    def _export_zip(
        self,
        articles: list[Article],
        path: str | None,
        progress_callback: Callable[[int, int, str], None] | None,
        **options,
    ) -> str:
        """导出为 ZIP 格式"""
        download_images = options.get("download_images", self._download_images)
        total = len(articles)

        output_path = self._determine_output_path(path, articles, ".zip")

        logger.info(f"📦 开始打包 {total} 篇文章为 ZIP...")

        try:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                self._write_articles_to_temp_and_add(
                    zf,
                    articles,
                    download_images,
                    progress_callback,
                    add_func=lambda zf, name, data: zf.writestr(name, data),
                )

                # 添加索引文件
                index_content = self._generate_index(articles)
                zf.writestr("index.html", index_content.encode("utf-8"))

            logger.success(f"✅ ZIP 导出成功: {output_path} ({len(articles)} 篇文章)")
            return str(output_path)

        except Exception as e:
            raise ExporterError(f"ZIP 导出失败: {e}") from e

    def _export_7z(
        self,
        articles: list[Article],
        path: str | None,
        progress_callback: Callable[[int, int, str], None] | None,
        **options,
    ) -> str:
        """导出为 7z 格式"""
        try:
            import py7zr
        except ImportError as err:
            raise ExporterError("7z 格式需要安装 py7zr 库: pip install py7zr") from err

        options.get("download_images", self._download_images)
        total = len(articles)

        output_path = self._determine_output_path(path, articles, ".7z")

        logger.info(f"📦 开始打包 {total} 篇文章为 7z...")

        try:
            with py7zr.SevenZipFile(output_path, "w") as archive:
                for i, article in enumerate(articles):
                    if progress_callback:
                        with contextlib.suppress(Exception):
                            progress_callback(i, total, article.title[:30])

                    # 生成 HTML 内容
                    html_content = self._html_exporter._generate_html(article, **options)
                    safe_title = self._safe_filename(article.title)
                    html_filename = f"{i + 1:03d}_{safe_title}.html"

                    # 使用 writestr 写入内存数据
                    html_bytes = html_content.encode("utf-8")
                    archive.writestr({html_filename: io.BytesIO(html_bytes)})

                    logger.debug(f"已打包 {i + 1}/{total}: {article.title[:30]}")

                # 最后一次进度回调
                if progress_callback:
                    with contextlib.suppress(Exception):
                        progress_callback(total, total, "生成索引文件")

                # 添加索引文件
                index_content = self._generate_index(articles)
                archive.writestr({"index.html": io.BytesIO(index_content.encode("utf-8"))})

            logger.success(f"✅ 7z 导出成功: {output_path} ({len(articles)} 篇文章)")
            return str(output_path)

        except Exception as e:
            raise ExporterError(f"7z 导出失败: {e}") from e

    def _export_rar(
        self,
        articles: list[Article],
        path: str | None,
        progress_callback: Callable[[int, int, str], None] | None,
        **options,
    ) -> str:
        """导出为 RAR 格式（使用外部 WinRAR 工具）"""
        rar_exe = self._find_rar_executable()
        if not rar_exe:
            raise ExporterError("RAR 格式需要安装 WinRAR 并添加到 PATH")

        options.get("download_images", self._download_images)
        total = len(articles)

        output_path = self._determine_output_path(path, articles, ".rar")

        logger.info(f"📦 开始打包 {total} 篇文章为 RAR...")

        # 创建临时目录存放文件
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            try:
                for i, article in enumerate(articles):
                    if progress_callback:
                        with contextlib.suppress(Exception):
                            progress_callback(i, total, article.title[:30])

                    # 生成 HTML 内容
                    html_content = self._html_exporter._generate_html(article, **options)
                    safe_title = self._safe_filename(article.title)
                    html_filename = f"{i + 1:03d}_{safe_title}.html"

                    # 写入临时文件
                    html_path = temp_path / html_filename
                    html_path.write_text(html_content, encoding="utf-8")

                    logger.debug(f"已准备 {i + 1}/{total}: {article.title[:30]}")

                # 最后一次进度回调
                if progress_callback:
                    with contextlib.suppress(Exception):
                        progress_callback(total, total, "生成索引文件")

                # 添加索引文件
                index_content = self._generate_index(articles)
                (temp_path / "index.html").write_text(index_content, encoding="utf-8")

                # 使用 WinRAR 创建压缩包
                # rar a -ep1 <archive> <files>
                # -ep1: 从路径中排除基目录
                result = subprocess.run(
                    [rar_exe, "a", "-ep1", "-r", str(output_path), str(temp_path / "*")],
                    capture_output=True,
                    text=True,
                    stdin=subprocess.DEVNULL,
                    timeout=300,  # 5分钟超时
                )

                if result.returncode != 0:
                    raise ExporterError(f"RAR 创建失败: {result.stderr}")

                logger.success(f"✅ RAR 导出成功: {output_path} ({len(articles)} 篇文章)")
                return str(output_path)

            except subprocess.TimeoutExpired as err:
                raise ExporterError("RAR 创建超时") from err
            except Exception as e:
                raise ExporterError(f"RAR 导出失败: {e}") from e

    def _determine_output_path(
        self, path: str | None, articles: list[Article], extension: str
    ) -> Path:
        """确定输出文件路径"""
        if path:
            output_path = Path(path)
            if output_path.is_dir():
                output_path = output_path / self._generate_archive_name(articles, extension)
        else:
            self._output_dir.mkdir(parents=True, exist_ok=True)
            output_path = self._output_dir / self._generate_archive_name(articles, extension)

        # 确保扩展名正确
        if not str(output_path).endswith(extension):
            output_path = Path(str(output_path) + extension)

        return output_path

    def _generate_archive_name(self, articles: list[Article], extension: str) -> str:
        """生成压缩文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        count = len(articles)
        return f"articles_{count}篇_{timestamp}{extension}"

    def _safe_filename(self, title: str) -> str:
        """生成安全的文件名"""
        safe = re.sub(r'[\\/*?:"<>|]', "", title)
        safe = safe.strip()[:50]
        return safe or "untitled"

    def _write_articles_to_temp_and_add(
        self,
        archive,
        articles: list[Article],
        download_images: bool,
        progress_callback: Callable[[int, int, str], None] | None,
        add_func: Callable,
        **options,
    ):
        """写入文章到压缩文件的通用方法"""
        total = len(articles)

        for i, article in enumerate(articles):
            if progress_callback:
                with contextlib.suppress(Exception):
                    progress_callback(i, total, article.title[:30])

            # 生成 HTML 内容
            html_content = self._html_exporter._generate_html(article, **options)
            safe_title = self._safe_filename(article.title)
            html_filename = f"{i + 1:03d}_{safe_title}.html"

            # 添加到压缩文件
            add_func(archive, html_filename, html_content.encode("utf-8"))

            logger.debug(f"已打包 {i + 1}/{total}: {article.title[:30]}")

        # 最后一次进度回调
        if progress_callback:
            with contextlib.suppress(Exception):
                progress_callback(total, total, "生成索引文件")

    def _generate_index(self, articles: list[Article]) -> str:
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
