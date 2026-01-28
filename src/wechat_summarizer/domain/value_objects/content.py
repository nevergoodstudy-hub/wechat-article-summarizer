"""内容值对象"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class ArticleContent:
    """
    文章内容值对象

    封装文章的HTML和纯文本内容，提供内容处理方法。
    """

    html: str = ""
    text: str = ""
    images: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        # 如果只有HTML，自动提取纯文本
        if self.html and not self.text:
            object.__setattr__(self, "text", self._extract_text(self.html))

        # 如果只有纯文本，简单包装为HTML
        if self.text and not self.html:
            object.__setattr__(self, "html", f"<p>{self.text}</p>")

    @staticmethod
    def _extract_text(html: str) -> str:
        """从HTML提取纯文本"""
        soup = BeautifulSoup(html, "html.parser")

        # 移除脚本和样式
        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        # 清理多余空白
        lines = (line.strip() for line in text.splitlines())
        text = "\n".join(line for line in lines if line)
        return text

    @classmethod
    def from_html(cls, html: str, clean: bool = True) -> ArticleContent:
        """从HTML创建内容对象"""
        if clean:
            html = cls._clean_html(html)

        images = cls._extract_images(html)
        text = cls._extract_text(html)

        return cls(html=html, text=text, images=tuple(images))

    @classmethod
    def from_text(cls, text: str) -> ArticleContent:
        """从纯文本创建内容对象"""
        # 简单将文本转为段落
        paragraphs = text.split("\n\n")
        html = "\n".join(f"<p>{p}</p>" for p in paragraphs if p.strip())
        return cls(html=html, text=text, images=())

    @staticmethod
    def _clean_html(html: str) -> str:
        """清理HTML内容"""
        soup = BeautifulSoup(html, "html.parser")

        # 移除隐藏元素的样式 (微信特殊处理)
        for tag in soup.find_all(style=True):
            raw_style = tag.get("style")
            # BeautifulSoup 的属性类型在类型层面可能是 list[str] / str / None
            style = " ".join(raw_style) if isinstance(raw_style, list) else str(raw_style or "")

            # 移除 visibility:hidden 和 opacity:0
            style = re.sub(r"visibility\s*:\s*hidden\s*;?", "", style, flags=re.I)
            style = re.sub(r"opacity\s*:\s*0\s*;?", "", style, flags=re.I)

            if style.strip():
                tag["style"] = style
            else:
                del tag["style"]

        # 处理懒加载图片
        for img in soup.find_all("img"):
            data_src = img.get("data-src")
            if data_src and not img.get("src"):
                img["src"] = data_src

        return str(soup)

    @staticmethod
    def _extract_images(html: str) -> list[str]:
        """提取图片URL列表"""
        soup = BeautifulSoup(html, "html.parser")
        images: list[str] = []

        for img in soup.find_all("img"):
            src_val = img.get("data-src") or img.get("src")
            if not src_val:
                continue

            # BeautifulSoup 类型层面可能返回 list[str]；这里统一转成 str
            if isinstance(src_val, list):
                src_val = src_val[0] if src_val else ""

            src = str(src_val)
            if src.startswith(("http://", "https://")):
                images.append(src)

        return images

    @property
    def word_count(self) -> int:
        """字数统计"""
        return len(self.text)

    @property
    def image_count(self) -> int:
        """图片数量"""
        return len(self.images)

    @property
    def preview(self) -> str:
        """内容预览 (前500字)"""
        if len(self.text) <= 500:
            return self.text
        return self.text[:500] + "..."

    def truncate(self, max_length: int = 10000) -> ArticleContent:
        """截断内容"""
        if len(self.text) <= max_length:
            return self

        return ArticleContent(
            html=self.html[: max_length * 2],  # HTML可能更长
            text=self.text[:max_length],
            images=self.images,
        )
