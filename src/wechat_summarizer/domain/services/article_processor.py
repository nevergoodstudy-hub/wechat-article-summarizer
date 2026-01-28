"""文章处理领域服务"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities import Article, Summary
    from ..value_objects import ArticleContent


class ArticleProcessorService:
    """
    文章处理领域服务

    领域服务包含不属于任何特定实体的业务逻辑，
    但又是领域逻辑的一部分。
    """

    def process_article(
        self,
        article: Article,
        summary: Summary | None = None,
    ) -> Article:
        """
        处理文章

        将摘要附加到文章，执行必要的领域验证。
        """
        if summary:
            article.attach_summary(summary)

        return article

    def validate_content(self, content: ArticleContent) -> bool:
        """
        验证文章内容是否有效

        - 内容不能为空
        - 字数至少100字
        """
        if not content.text:
            return False

        if content.word_count < 100:
            return False

        return True

    def estimate_tokens(self, content: ArticleContent) -> int:
        """
        估算Token数量

        简单估算：中文约1.5字符/token，英文约4字符/token
        """
        text = content.text

        # 简单区分中英文
        chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        other_chars = len(text) - chinese_chars

        # 估算Token
        chinese_tokens = chinese_chars / 1.5
        other_tokens = other_chars / 4

        return int(chinese_tokens + other_tokens)

    def should_chunk(self, content: ArticleContent, max_tokens: int = 4000) -> bool:
        """
        判断是否需要分块处理
        """
        estimated = self.estimate_tokens(content)
        return estimated > max_tokens
