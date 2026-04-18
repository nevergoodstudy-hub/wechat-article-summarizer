import json
from pathlib import Path
from types import SimpleNamespace

from wechat_summarizer.domain.entities import Article, Summary
from wechat_summarizer.domain.value_objects import ArticleContent, ArticleURL
from wechat_summarizer.infrastructure.adapters.exporters.onenote import OneNoteExporter
from wechat_summarizer.shared import system_keyring as system_keyring_module


class _FakeKeyring:
    def __init__(self) -> None:
        self._backend = SimpleNamespace(priority=5)
        self._store: dict[tuple[str, str], str] = {}

    def get_keyring(self) -> SimpleNamespace:
        return self._backend

    def get_password(self, service_name: str, entry_name: str) -> str | None:
        return self._store.get((service_name, entry_name))

    def set_password(self, service_name: str, entry_name: str, value: str) -> None:
        self._store[(service_name, entry_name)] = value

    def delete_password(self, service_name: str, entry_name: str) -> None:
        self._store.pop((service_name, entry_name), None)


def _patch_fake_keyring(monkeypatch) -> None:
    fake = _FakeKeyring()
    monkeypatch.setattr(system_keyring_module, "_keyring", fake)
    monkeypatch.setattr(system_keyring_module, "_is_recommended_backend", lambda backend: True)


def test_onenote_exporter_is_available_requires_cached_refresh_token(
    monkeypatch, tmp_path: Path
) -> None:
    _patch_fake_keyring(monkeypatch)
    token_path = tmp_path / "onenote_token.json"

    exporter = OneNoteExporter(
        client_id="client-id",
        tenant="common",
        notebook="Notebook",
        section="Section",
        token_cache_path=str(token_path),
    )
    assert exporter.is_available() is False

    token_path.write_text(
        json.dumps(
            {"refresh_token": "rt", "access_token": "at", "expires_in": 3600, "obtained_at": 1}
        ),
        encoding="utf-8",
    )

    assert exporter.is_available() is True


def test_onenote_exporter_builds_html_payload(monkeypatch, tmp_path: Path) -> None:
    _patch_fake_keyring(monkeypatch)
    exporter = OneNoteExporter(
        client_id="client-id",
        tenant="common",
        notebook="Notebook",
        section="Section",
        token_cache_path=str(tmp_path / "onenote_token.json"),
    )

    article = Article(
        url=ArticleURL.from_string("https://mp.weixin.qq.com/s/xxx"),
        title="Test Title",
        content=ArticleContent.from_text("hello world"),
    )
    article.attach_summary(Summary(content="sum", key_points=("kp1",), tags=("t1",)))

    html = exporter._build_page_html(article, include_content=True, max_content_chars=5)
    assert "<title>Test Title</title>" in html
    assert "<h2>摘要</h2>" in html
    assert "kp1" in html
    assert "t1" in html
    assert "hello" in html
