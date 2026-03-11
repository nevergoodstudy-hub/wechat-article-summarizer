"""公众号相关文章预览用例。"""

from __future__ import annotations

from dataclasses import dataclass

from ...domain.entities.article_list import ArticleList, ArticleListItem
from ...domain.entities.official_account import OfficialAccount
from ...domain.value_objects.article_filter import ArticleFilter
from ...shared.exceptions import ValidationError
from ..ports.outbound.article_list_port import ArticleListPort


@dataclass(frozen=True)
class RelatedAccountArticlesPreview:
    """公众号相关文章预览结果。"""

    account: OfficialAccount
    keyword: str
    recent_count: int
    total_articles: int
    available_total: int
    matched_articles: list[ArticleListItem]

    @property
    def matched_count(self) -> int:
        return len(self.matched_articles)

    def to_dict(self) -> dict:
        return {
            "account": self.account.to_dict(),
            "keyword": self.keyword,
            "recent_count": self.recent_count,
            "total_articles": self.total_articles,
            "available_total": self.available_total,
            "matched_count": self.matched_count,
            "matched_articles": [item.to_dict() for item in self.matched_articles],
        }


class PreviewRelatedAccountArticlesUseCase:
    """拉取公众号近期文章并按关键词预览相关文章。"""

    def __init__(self, article_list_port: ArticleListPort) -> None:
        self._article_list_port = article_list_port

    async def execute(
        self,
        *,
        account: OfficialAccount,
        keyword: str,
        recent_count: int = 50,
    ) -> RelatedAccountArticlesPreview:
        normalized_keyword = keyword.strip()
        if not normalized_keyword:
            raise ValidationError("关键词不能为空")
        if recent_count <= 0:
            raise ValidationError("最近文章数量必须大于0")

        article_list = await self._article_list_port.get_all_articles(
            account,
            max_count=recent_count,
        )
        recent_articles = article_list.sort_by_time()[:recent_count]
        article_filter = ArticleFilter.by_keyword(normalized_keyword)
        matched_articles = article_filter.apply(recent_articles)
        return self._build_result(
            account=account,
            keyword=normalized_keyword,
            recent_count=recent_count,
            article_list=article_list,
            matched_articles=matched_articles,
        )

    @staticmethod
    def _build_result(
        *,
        account: OfficialAccount,
        keyword: str,
        recent_count: int,
        article_list: ArticleList,
        matched_articles: list[ArticleListItem],
    ) -> RelatedAccountArticlesPreview:
        total_articles = min(article_list.count, recent_count) if recent_count > 0 else article_list.count
        return RelatedAccountArticlesPreview(
            account=account,
            keyword=keyword,
            recent_count=recent_count,
            total_articles=total_articles,
            available_total=article_list.total_count,
            matched_articles=matched_articles,
        )
