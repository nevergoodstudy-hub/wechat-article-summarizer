"""公众号搜索适配器测试。"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from wechat_summarizer.application.ports.outbound.auth_port import AuthCredentials
from wechat_summarizer.infrastructure.adapters.wechat_batch.account_searcher import (
    WechatOfficialAccountSearcher,
)


class _FakeCookies:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def set(self, name: str, value: str) -> None:
        self.values[name] = value


@dataclass
class _FakeResponse:
    status_code: int
    payload: dict

    def json(self) -> dict:
        return self.payload


class _FakeAsyncClient:
    def __init__(self, response: _FakeResponse) -> None:
        self.response = response
        self.cookies = _FakeCookies()
        self.calls: list[tuple[str, dict]] = []

    async def get(self, url: str, params: dict | None = None):
        self.calls.append((url, params or {}))
        return self.response


class _FakeAuthManager:
    def __init__(self, *, token: str = "123456") -> None:
        self._credentials = AuthCredentials(
            token=token,
            cookies={"pass_ticket": "ticket", "bizuin": "123"},
        )

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def credentials(self) -> AuthCredentials:
        return self._credentials

    @property
    def token(self) -> str:
        return self._credentials.token


@pytest.mark.unit
@pytest.mark.asyncio
async def test_searcher_parses_search_results_and_strips_highlight_markup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _FakeAsyncClient(
        _FakeResponse(
            status_code=200,
            payload={
                "base_resp": {"ret": 0, "err_msg": "ok"},
                "list": [
                    {
                        "fakeid": "MzA1",
                        "nickname": '<em class="highlight">Python</em>之禅',
                        "alias": "python_vtalk",
                        "round_head_img": "https://example.com/avatar.jpg",
                        "service_type": 0,
                        "signature": "分享 Python 技术",
                    }
                ],
            },
        )
    )
    searcher = WechatOfficialAccountSearcher(_FakeAuthManager())

    async def _fake_get_client():
        return client

    monkeypatch.setattr(searcher, "_get_client", _fake_get_client)

    result = await searcher.search_official_accounts("Python", limit=5)

    assert len(result) == 1
    assert result[0].fakeid == "MzA1"
    assert result[0].nickname == "Python之禅"
    assert result[0].alias == "python_vtalk"
    assert client.cookies.values["pass_ticket"] == "ticket"
    assert client.calls[0][1]["action"] == "search_biz"
    assert client.calls[0][1]["query"] == "Python"
    assert client.calls[0][1]["count"] == 5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_searcher_raises_when_login_expired(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _FakeAsyncClient(
        _FakeResponse(
            status_code=200,
            payload={"base_resp": {"ret": 200040, "err_msg": "invalid session"}},
        )
    )
    searcher = WechatOfficialAccountSearcher(_FakeAuthManager())

    async def _fake_get_client():
        return client

    monkeypatch.setattr(searcher, "_get_client", _fake_get_client)

    with pytest.raises(ValueError, match="登录状态已失效"):
        await searcher.search_official_accounts("Python")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_searcher_rejects_blank_query() -> None:
    searcher = WechatOfficialAccountSearcher(_FakeAuthManager())

    with pytest.raises(ValueError, match="搜索关键词不能为空"):
        await searcher.search_official_accounts("  ")
