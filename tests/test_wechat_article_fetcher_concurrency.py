"""Wechat article fetcher concurrency tests."""

from __future__ import annotations

import asyncio

import pytest

from wechat_summarizer.domain.entities.article_list import ArticleList
from wechat_summarizer.domain.entities.official_account import OfficialAccount
from wechat_summarizer.infrastructure.adapters.wechat_batch.article_fetcher import (
    WechatArticleFetcher,
)


class _AuthDouble:
    """Minimal auth double for fetcher construction."""

    is_authenticated = True
    credentials = None
    token = "token"


class _TrackingFetcher(WechatArticleFetcher):
    """Fetcher double that records concurrent account work."""

    def __init__(self) -> None:
        super().__init__(auth_manager=_AuthDouble())  # type: ignore[arg-type]
        self.running = 0
        self.max_seen = 0
        self._lock = asyncio.Lock()

    async def get_all_articles(
        self,
        account: OfficialAccount,
        max_count: int | None = None,
        use_cache: bool = True,
    ) -> ArticleList:
        async with self._lock:
            self.running += 1
            self.max_seen = max(self.max_seen, self.running)

        await asyncio.sleep(0.01)

        async with self._lock:
            self.running -= 1

        return ArticleList(fakeid=account.fakeid, account_name=account.nickname)


@pytest.mark.unit
async def test_fetch_multiple_accounts_respects_max_concurrency() -> None:
    """Multiple-account fetching should use the configured concurrency cap."""
    fetcher = _TrackingFetcher()
    accounts = [
        OfficialAccount(fakeid=f"fakeid-{index}", nickname=f"account-{index}") for index in range(6)
    ]

    result = await fetcher.fetch_multiple_accounts(accounts, max_concurrency=2)

    assert set(result) == {account.fakeid for account in accounts}
    assert fetcher.max_seen <= 2
