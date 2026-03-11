"""Markdown 内容包导出器测试。"""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pytest

from wechat_summarizer.domain.entities.article import Article
from wechat_summarizer.domain.entities.summary import Summary, SummaryMethod, SummaryStyle
from wechat_summarizer.domain.value_objects.content import ArticleContent
from wechat_summarizer.domain.value_objects.url import ArticleURL
from wechat_summarizer.infrastructure.adapters.wechat_batch.article_package_exporter import (
    MarkdownArticlePackageExporter,
)


def _build_article(url: str, title: str) -> Article:
    article = Article(
        url=ArticleURL.from_string(url),
        title=title,
        account_name="测试公众号",
        publish_time=datetime(2024, 1, 15, 10, 30, 0),
        content=ArticleContent.from_text(f"{title} 正文"),
    )
    article.attach_summary(
        Summary(
            content=f"{title} 摘要",
            key_points=("要点",),
            tags=("tag",),
            method=SummaryMethod.SIMPLE,
            style=SummaryStyle.CONCISE,
        )
    )
    return article


@dataclass
class _FakeMarkdownExporter:
    calls: list[tuple[str, Path]]

    def export(self, article: Article, path: str | None = None, **options) -> str:
        output_dir = Path(path or ".")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{article.title}.md"
        output_path.write_text(f"# {article.title}\n\n{article.summary.content}", encoding="utf-8")
        self.calls.append((article.title, output_path))
        return str(output_path)


@pytest.mark.unit
def test_markdown_article_package_exporter_writes_markdown_files_and_manifest(
    tmp_path: Path,
) -> None:
    markdown_exporter = _FakeMarkdownExporter(calls=[])
    exporter = MarkdownArticlePackageExporter(markdown_exporter=markdown_exporter)
    output_path = tmp_path / "articles.zip"
    articles = [
        _build_article("https://mp.weixin.qq.com/s/python-1", "Python 实战"),
        _build_article("https://mp.weixin.qq.com/s/db-1", "数据库优化"),
    ]
    manifest = {
        "account": {"nickname": "Python之禅"},
        "articles": [{"title": article.title, "link": str(article.url)} for article in articles],
        "failures": [],
    }

    result = exporter.export(articles=articles, output_path=output_path, manifest=manifest)

    assert result == output_path
    assert output_path.exists()
    assert [title for title, _ in markdown_exporter.calls] == ["Python 实战", "数据库优化"]

    with zipfile.ZipFile(output_path) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert "Python 实战.md" in names
        assert "数据库优化.md" in names

        manifest_data = json.loads(archive.read("manifest.json").decode("utf-8"))
        assert manifest_data["account"]["nickname"] == "Python之禅"
        assert len(manifest_data["articles"]) == 2


@pytest.mark.unit
def test_markdown_article_package_exporter_supports_manifest_only_archive(tmp_path: Path) -> None:
    exporter = MarkdownArticlePackageExporter(markdown_exporter=_FakeMarkdownExporter(calls=[]))
    output_path = tmp_path / "empty.zip"

    exporter.export(articles=[], output_path=output_path, manifest={"articles": [], "failures": []})

    with zipfile.ZipFile(output_path) as archive:
        assert set(archive.namelist()) == {"manifest.json"}
