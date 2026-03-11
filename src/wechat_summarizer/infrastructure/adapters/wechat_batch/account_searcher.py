"""公众号搜索适配器。"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, cast

import httpx

from ....domain.entities.official_account import OfficialAccount
from ..http_client_pool import get_http_pool

if TYPE_CHECKING:
    from .auth_manager import WechatAuthManager

SEARCH_BIZ_URL = "https://mp.weixin.qq.com/cgi-bin/searchbiz"


class WechatOfficialAccountSearcher:
    """基于微信公众平台后台接口搜索公众号候选项。"""

    def __init__(self, auth_manager: WechatAuthManager) -> None:
        self._auth = auth_manager
        self._client: httpx.AsyncClient | None = None

    @property
    def is_authenticated(self) -> bool:
        return self._auth.is_authenticated

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            pool = get_http_pool()
            self._client = await pool.get_client("mp.weixin.qq.com")
        return self._client

    def _prepare_cookies(self, client: httpx.AsyncClient) -> None:
        if not self._auth.credentials:
            raise ValueError("未登录，请先完成认证")
        for name, value in self._auth.credentials.cookies.items():
            client.cookies.set(name, value)

    async def search_official_accounts(
        self,
        query: str,
        limit: int = 10,
    ) -> list[OfficialAccount]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("搜索关键词不能为空")
        if limit <= 0:
            raise ValueError("搜索结果数量必须大于0")
        if not self.is_authenticated:
            raise ValueError("未登录，请先完成认证")

        client = await self._get_client()
        self._prepare_cookies(client)

        token = self._auth.token
        if not token:
            raise ValueError("Token无效")

        response = await client.get(
            SEARCH_BIZ_URL,
            params={
                "action": "search_biz",
                "begin": 0,
                "count": limit,
                "query": normalized_query,
                "token": token,
                "lang": "zh_CN",
                "f": "json",
                "ajax": "1",
            },
        )
        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}")

        data = cast(dict[str, Any], response.json())
        base_resp = data.get("base_resp", {})
        ret = base_resp.get("ret", -1)
        if ret != 0:
            if ret in {200040, 200003}:
                raise ValueError("登录状态已失效，请重新登录")
            err_msg = base_resp.get("err_msg", "未知错误")
            raise RuntimeError(f"公众号搜索失败 ({ret}): {err_msg}")

        return self._parse_accounts(data)

    def _parse_accounts(self, response: dict[str, Any]) -> list[OfficialAccount]:
        raw_accounts = response.get("list") or response.get("biz_list") or response.get("items") or []
        accounts: list[OfficialAccount] = []
        for item in raw_accounts:
            if not isinstance(item, dict):
                continue
            normalized = dict(item)
            normalized["nickname"] = self._strip_highlight_markup(str(item.get("nickname", "")))
            normalized["alias"] = self._strip_highlight_markup(str(item.get("alias", "")))
            normalized["signature"] = self._strip_highlight_markup(str(item.get("signature", "")))
            if normalized.get("service_type") not in {0, 1}:
                normalized["service_type"] = 0
            try:
                accounts.append(OfficialAccount.from_api_response(normalized))
            except Exception:
                continue
        return accounts

    @staticmethod
    def _strip_highlight_markup(value: str) -> str:
        return re.sub(r"<[^>]+>", "", value).strip()
