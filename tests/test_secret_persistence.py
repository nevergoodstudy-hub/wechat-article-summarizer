from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from wechat_summarizer.application.ports.outbound.auth_port import AuthCredentials
from wechat_summarizer.infrastructure.adapters.exporters.onenote import _TokenCache
from wechat_summarizer.infrastructure.adapters.wechat_batch.auth_manager import (
    FileCredentialStorage,
    WechatAuthManager,
)
from wechat_summarizer.shared import system_keyring as system_keyring_module
from wechat_summarizer.shared.system_keyring import JsonSecretStore


class _FakeKeyring:
    def __init__(self, priority: int = 5) -> None:
        self._backend = SimpleNamespace(priority=priority)
        self._store: dict[tuple[str, str], str] = {}

    def get_keyring(self) -> SimpleNamespace:
        return self._backend

    def get_password(self, service_name: str, entry_name: str) -> str | None:
        return self._store.get((service_name, entry_name))

    def set_password(self, service_name: str, entry_name: str, value: str) -> None:
        self._store[(service_name, entry_name)] = value

    def delete_password(self, service_name: str, entry_name: str) -> None:
        self._store.pop((service_name, entry_name), None)


def _install_fake_keyring(
    monkeypatch: pytest.MonkeyPatch, *, priority: int = 5
) -> _FakeKeyring:
    fake = _FakeKeyring(priority=priority)
    monkeypatch.setattr(system_keyring_module, "_keyring", fake)
    monkeypatch.setattr(
        system_keyring_module,
        "_is_recommended_backend",
        lambda backend: getattr(backend, "priority", 0) >= 1,
    )
    return fake


@pytest.mark.unit
def test_json_secret_store_migrates_legacy_file_into_keyring(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_keyring = _install_fake_keyring(monkeypatch)
    legacy_path = tmp_path / "legacy.json"
    legacy_path.write_text(json.dumps({"token": "abc"}), encoding="utf-8")

    store = JsonSecretStore(
        service_name="wechat-summarizer.test",
        entry_name="entry",
        legacy_path=legacy_path,
        label="test secret",
    )

    assert store.load() == {"token": "abc"}
    assert legacy_path.exists() is False
    assert fake_keyring.get_password("wechat-summarizer.test", "entry") == '{"token": "abc"}'


@pytest.mark.unit
def test_json_secret_store_keeps_only_in_memory_when_keyring_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_keyring(monkeypatch, priority=0)
    store = JsonSecretStore(
        service_name="wechat-summarizer.test",
        entry_name="entry",
        label="test secret",
    )

    store.save({"refresh_token": "rt"})

    assert store.load() == {"refresh_token": "rt"}

    new_store = JsonSecretStore(
        service_name="wechat-summarizer.test",
        entry_name="entry",
        label="test secret",
    )
    assert new_store.load() is None


@pytest.mark.unit
def test_file_credential_storage_uses_secure_store_without_creating_plaintext_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_keyring = _install_fake_keyring(monkeypatch)
    credential_path = tmp_path / "wechat_credentials.json"
    storage = FileCredentialStorage(credential_path)
    credentials = AuthCredentials(
        token="token-123",
        cookies={"session": "cookie"},
        user_info={"nickname": "公众号"},
    )

    storage.save(credentials)

    assert credential_path.exists() is False
    loaded = storage.load()
    assert loaded is not None
    assert loaded.token == "token-123"
    assert loaded.cookies == {"session": "cookie"}
    assert loaded.user_info == {"nickname": "公众号"}
    assert fake_keyring.get_password(
        "wechat-summarizer.wechat-batch",
        str(credential_path.resolve()),
    ) is not None


@pytest.mark.unit
def test_file_credential_storage_migrates_existing_plaintext_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_keyring = _install_fake_keyring(monkeypatch)
    credential_path = tmp_path / "wechat_credentials.json"
    credential_path.write_text(
        json.dumps(
            {
                "token": "legacy-token",
                "cookies": {"session": "cookie"},
                "fingerprint": "",
                "expires_at": None,
                "user_info": {"nickname": "公众号"},
            }
        ),
        encoding="utf-8",
    )

    storage = FileCredentialStorage(credential_path)

    loaded = storage.load()

    assert loaded is not None
    assert loaded.token == "legacy-token"
    assert credential_path.exists() is False
    assert fake_keyring.get_password(
        "wechat-summarizer.wechat-batch",
        str(credential_path.resolve()),
    ) is not None


@pytest.mark.unit
def test_onenote_token_cache_uses_secure_store_without_plaintext_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_keyring = _install_fake_keyring(monkeypatch)
    token_path = tmp_path / "onenote_token.json"
    cache = _TokenCache(token_path)

    cache.save({"refresh_token": "rt", "access_token": "at"})

    assert token_path.exists() is False
    assert cache.load() == {"refresh_token": "rt", "access_token": "at"}
    assert fake_keyring.get_password(
        "wechat-summarizer.onenote",
        str(token_path.resolve()),
    ) is not None


@pytest.mark.unit
def test_onenote_token_cache_migrates_legacy_plaintext_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_fake_keyring(monkeypatch)
    token_path = tmp_path / "onenote_token.json"
    token_path.write_text(
        json.dumps({"refresh_token": "rt", "access_token": "at"}),
        encoding="utf-8",
    )

    cache = _TokenCache(token_path)

    assert cache.load() == {"refresh_token": "rt", "access_token": "at"}
    assert token_path.exists() is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wechat_auth_manager_sets_local_expiry_when_login_completes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_fake_keyring(monkeypatch)
    storage = FileCredentialStorage(tmp_path / "wechat_credentials.json")
    manager = WechatAuthManager(storage=storage, auto_load=False)

    fake_client = SimpleNamespace(
        cookies=SimpleNamespace(jar=[SimpleNamespace(name="sid", value="cookie")])
    )

    async def fake_get_client() -> SimpleNamespace:
        return fake_client

    async def fake_get(url: str, follow_redirects: bool = True) -> SimpleNamespace:
        return SimpleNamespace(url="https://mp.weixin.qq.com/cgi-bin/home?token=123456")

    async def fake_get_user_info(_token: str) -> dict[str, str]:
        return {"nickname": "公众号"}

    fake_client.get = fake_get
    monkeypatch.setattr(manager, "_get_client", fake_get_client)
    monkeypatch.setattr(manager, "_get_user_info", fake_get_user_info)

    credentials = await manager._complete_login({"redirect_url": "/cgi-bin/home?token=123456"})

    assert credentials.token == "123456"
    assert credentials.cookies == {"sid": "cookie"}
    assert credentials.user_info == {"nickname": "公众号"}
    assert credentials.expires_at is not None
    assert credentials.expires_at > datetime.now()
