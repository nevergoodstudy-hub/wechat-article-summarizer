import json
from pathlib import Path

from wechat_summarizer.domain.entities import Article, Summary
from wechat_summarizer.domain.value_objects import ArticleContent, ArticleURL
from wechat_summarizer.infrastructure.adapters.exporters.onenote import OneNoteExporter


def test_onenote_exporter_is_available_requires_cached_refresh_token(tmp_path: Path) -> None:
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


def test_onenote_exporter_builds_html_payload(tmp_path: Path) -> None:
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
