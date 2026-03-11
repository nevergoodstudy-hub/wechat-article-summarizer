"""公众号搜索用例。"""

from __future__ import annotations

from dataclasses import dataclass

from ...domain.entities.official_account import OfficialAccount
from ...shared.exceptions import ValidationError
from ..ports.outbound.official_account_search_port import OfficialAccountSearchPort


@dataclass(frozen=True)
class SearchOfficialAccountsResult:
    """公众号搜索结果。"""

    query: str
    accounts: list[OfficialAccount]

    @property
    def total_count(self) -> int:
        return len(self.accounts)


class SearchOfficialAccountsUseCase:
    """执行公众号候选搜索。"""

    def __init__(self, search_port: OfficialAccountSearchPort) -> None:
        self._search_port = search_port

    async def execute(
        self,
        query: str,
        limit: int = 10,
    ) -> SearchOfficialAccountsResult:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValidationError("搜索关键词不能为空")
        if limit <= 0:
            raise ValidationError("搜索结果数量必须大于0")

        accounts = await self._search_port.search_official_accounts(
            normalized_query,
            limit=limit,
        )
        return SearchOfficialAccountsResult(query=normalized_query, accounts=accounts)
