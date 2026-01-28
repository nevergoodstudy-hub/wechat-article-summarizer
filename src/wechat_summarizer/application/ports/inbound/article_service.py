"""文章服务入站端口 - 定义应用层对外提供的服务接口"""

from typing import Protocol

from ....domain.entities import Article, Summary


class ArticleServicePort(Protocol):
    """
    文章服务端口

    定义应用层对外提供的文章相关服务接口。
    展示层（GUI/CLI）通过此接口与应用层交互。
    """

    def fetch_article(self, url: str) -> Article:
        """
        抓取文章

        Args:
            url: 文章URL

        Returns:
            抓取到的文章实体
        """
        ...

    def summarize_article(
        self,
        article: Article,
        method: str = "simple",
        style: str = "concise",
    ) -> Summary:
        """
        生成文章摘要

        Args:
            article: 文章实体
            method: 摘要方法 (simple, ollama, openai, anthropic, zhipu)
            style: 摘要风格 (concise, detailed, bullet)

        Returns:
            生成的摘要
        """
        ...

    def process_article(
        self,
        url: str,
        summarize: bool = True,
        method: str = "simple",
    ) -> Article:
        """
        完整处理文章（抓取+摘要）

        Args:
            url: 文章URL
            summarize: 是否生成摘要
            method: 摘要方法

        Returns:
            处理完成的文章（带摘要）
        """
        ...

    def export_article(
        self,
        article: Article,
        target: str,
        path: str | None = None,
    ) -> str:
        """
        导出文章

        Args:
            article: 文章实体
            target: 导出目标 (html, markdown, onenote, notion, obsidian)
            path: 导出路径（文件导出时使用）

        Returns:
            导出结果（文件路径或成功消息）
        """
        ...
