"""公众号搜索端口。"""

from __future__ import annotations

from abc import abstractmethod
from typing import Protocol

from ....domain.entities.official_account import OfficialAccount


class OfficialAccountSearchPort(Protocol):
    """公众号搜索端口协议。"""

    @abstractmethod
    async def search_official_accounts(
        self,
        query: str,
        limit: int = 10,
    ) -> list[OfficialAccount]:
        """按关键词搜索公众号候选项。"""
        ...
