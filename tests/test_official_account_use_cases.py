"""公众号搜索/预览/导出用例测试。"""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pytest

from wechat_summarizer.application.use_cases.export_related_account_articles_use_case import (
    ExportRelatedAccountArticlesUseCase,
)
from wechat_summarizer.application.use_cases.preview_related_account_articles_use_case import (
    PreviewRelatedAccountArticlesUseCase,
)
from wechat_summarizer.application.use_cases.search_official_accounts_use_case import (
    SearchOfficialAccountsUseCase,
)
from wechat_summarizer.domain.entities.article import Article
from wechat_summarizer.domain.entities.article_list import ArticleList, ArticleListItem
from wechat_summarizer.domain.entities.official_account import OfficialAccount
from wechat_summarizer.domain.entities.summary import Summary, SummaryMethod, SummaryStyle
from wechat_summarizer.domain.value_objects.content import ArticleContent
from wechat_summarizer.domain.value_objects.url import ArticleURL
from wechat_summarizer.shared.exceptions import ValidationError


class _FakeOfficialAccountSearchPort:
    def __init__(self, accounts: list[OfficialAccount]) -> None:
        self.accounts = accounts
        self.calls: list[tuple[str, int]] = []

    async def search_official_accounts(
        self,
        query: str,
        limit: int = 10,
    ) -> list[OfficialAccount]:
        self.calls.append((query, limit))
        return self.accounts[:limit]


class _FakeArticleListPort:
    def __init__(self, article_list: ArticleList) -> None:
        self.article_list = article_list
        self.calls: list[tuple[OfficialAccount, int | None]] = []

    async def get_all_articles(
        self,
        account: OfficialAccount,
        max_count: int | None = None,
    ) -> ArticleList:
        self.calls.append((account, max_count))
        return self.article_list


class _FakeFetchArticleUseCase:
    def __init__(self, articles: dict[str, Article]) -> None:
        self.articles = articles
        self.calls: list[str] = []

    def execute(self, url: str) -> Article:
        self.calls.append(url)
        if url not in self.articles:
            raise RuntimeError(f"missing article for {url}")
        return self.articles[url]


class _FakeSummarizeArticleUseCase:
    def __init__(self, summary: Summary) -> None:
        self.summary = summary
        self.calls: list[tuple[str, str]] = []

    def execute(self, article: Article, method: str = "simple") -> Summary:
        self.calls.append((article.title, method))
        return self.summary


class _FakeLinkExporter:
    def __init__(self) -> None:
        self.calls: list[tuple[list[ArticleListItem], object, str | None]] = []

    def export_links(
        self,
        items: list[ArticleListItem],
        options,
        account_name: str | None = None,
    ) -> Path:
        output_path = Path(options.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(f"{options.export_format.value}:{len(items)}", encoding="utf-8")
        self.calls.append((items, options, account_name))
        return output_path


@dataclass
class _FakePackageCall:
    articles: list[Article]
    output_path: Path
    manifest: dict


class _FakeArticlePackageExporter:
    def __init__(self) -> None:
        self.calls: list[_FakePackageCall] = []

    def export(self, articles: list[Article], output_path: str | Path, manifest: dict) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            for index, article in enumerate(articles, start=1):
                archive.writestr(f"{index:03d}_{article.title}.md", f"# {article.title}")
        self.calls.append(_FakePackageCall(articles=list(articles), output_path=path, manifest=manifest))
        return path


def _build_article(
    *,
    url: str,
    title: str,
    account_name: str = "测试号",
) -> Article:
    return Article(
        url=ArticleURL.from_string(url),
        title=title,
        account_name=account_name,
        publish_time=datetime(2024, 1, 15, 10, 30, 0),
        content=ArticleContent.from_text(f"{title} 正文内容"),
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_official_accounts_use_case_strips_query_and_returns_accounts() -> None:
    accounts = [
        OfficialAccount(fakeid="1", nickname="Python之禅", alias="python"),
        OfficialAccount(fakeid="2", nickname="测试号", alias="test"),
    ]
    port = _FakeOfficialAccountSearchPort(accounts)
    use_case = SearchOfficialAccountsUseCase(port)

    result = await use_case.execute("  Python  ", limit=1)

    assert result.query == "Python"
    assert result.accounts == accounts[:1]
    assert port.calls == [("Python", 1)]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_official_accounts_use_case_rejects_blank_query() -> None:
    use_case = SearchOfficialAccountsUseCase(_FakeOfficialAccountSearchPort([]))

    with pytest.raises(ValidationError, match="搜索关键词不能为空"):
        await use_case.execute("   ")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_preview_related_account_articles_use_case_filters_recent_articles_by_keyword() -> None:
    account = OfficialAccount(fakeid="MzI1", nickname="Python之禅", alias="python")
    article_list = ArticleList(
        fakeid=account.fakeid,
        account_name=account.nickname,
        items=[
            ArticleListItem(
                aid="1",
                title="Python 实战",
                link="https://mp.weixin.qq.com/s/python-1",
                digest="含项目案例",
                update_time=300,
            ),
            ArticleListItem(
                aid="2",
                title="数据库优化",
                link="https://mp.weixin.qq.com/s/db-1",
                digest="包含 Python 脚本",
                update_time=200,
            ),
            ArticleListItem(
                aid="3",
                title="前端工程化",
                link="https://mp.weixin.qq.com/s/front-1",
                digest="与本次关键词无关",
                update_time=100,
            ),
        ],
        total_count=88,
    )
    port = _FakeArticleListPort(article_list)
    use_case = PreviewRelatedAccountArticlesUseCase(port)

    result = await use_case.execute(account=account, keyword="Python", recent_count=50)

    assert result.account == account
    assert result.keyword == "Python"
    assert result.total_articles == 3
    assert result.available_total == 88
    assert result.matched_count == 2
    assert [item.title for item in result.matched_articles] == [
        "Python 实战",
        "数据库优化",
    ]
    assert port.calls == [(account, 50)]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_preview_related_account_articles_use_case_rejects_blank_keyword() -> None:
    account = OfficialAccount(fakeid="MzI1", nickname="Python之禅")
    port = _FakeArticleListPort(ArticleList(fakeid=account.fakeid, account_name=account.nickname))
    use_case = PreviewRelatedAccountArticlesUseCase(port)

    with pytest.raises(ValidationError, match="关键词不能为空"):
        await use_case.execute(account=account, keyword="  ")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_export_related_account_articles_use_case_writes_outputs_and_records_partial_failures(
    tmp_path: Path,
) -> None:
    account = OfficialAccount(fakeid="MzI1", nickname="Python之禅", alias="python")
    matched_articles = [
        ArticleListItem(
            aid="1",
            title="Python 实战",
            link="https://mp.weixin.qq.com/s/python-1",
            digest="含项目案例",
            update_time=300,
        ),
        ArticleListItem(
            aid="2",
            title="数据库优化",
            link="https://mp.weixin.qq.com/s/db-1",
            digest="包含 Python 脚本",
            update_time=200,
        ),
    ]
    preview_use_case = PreviewRelatedAccountArticlesUseCase(
        _FakeArticleListPort(
            ArticleList(
                fakeid=account.fakeid,
                account_name=account.nickname,
                items=matched_articles,
                total_count=88,
            )
        )
    )
    preview = await preview_use_case.execute(account=account, keyword="Python", recent_count=50)
    fetch_use_case = _FakeFetchArticleUseCase(
        {
            matched_articles[0].link: _build_article(
                url=matched_articles[0].link,
                title=matched_articles[0].title,
            )
        }
    )
    summarize_use_case = _FakeSummarizeArticleUseCase(
        Summary(
            content="测试摘要",
            key_points=("要点1",),
            tags=("Python",),
            method=SummaryMethod.SIMPLE,
            style=SummaryStyle.CONCISE,
        )
    )
    link_exporter = _FakeLinkExporter()
    package_exporter = _FakeArticlePackageExporter()
    use_case = ExportRelatedAccountArticlesUseCase(
        fetch_use_case=fetch_use_case,
        summarize_use_case=summarize_use_case,
        link_exporter=link_exporter,
        package_exporter=package_exporter,
        output_root=tmp_path,
    )

    result = use_case.execute(preview=preview, summarizer_method="simple")

    assert result.output_dir.exists()
    assert result.matched_count == 2
    assert result.exported_count == 1
    assert result.failed_count == 1
    assert result.link_exports["csv"].exists()
    assert result.link_exports["markdown"].exists()
    assert result.search_result_path.exists()
    assert result.export_report_path.exists()
    assert result.package_path.exists()
    assert result.failures[0].stage == "fetch"
    assert result.failures[0].link == matched_articles[1].link
    assert len(package_exporter.calls) == 1
    assert [article.title for article in package_exporter.calls[0].articles] == ["Python 实战"]

    search_result = json.loads(result.search_result_path.read_text(encoding="utf-8"))
    export_report = json.loads(result.export_report_path.read_text(encoding="utf-8"))
    assert search_result["matched_count"] == 2
    assert export_report["exported_count"] == 1
    assert export_report["failed_count"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_export_related_account_articles_use_case_rejects_empty_preview(tmp_path: Path) -> None:
    account = OfficialAccount(fakeid="MzI1", nickname="Python之禅", alias="python")
    preview_use_case = PreviewRelatedAccountArticlesUseCase(
        _FakeArticleListPort(ArticleList(fakeid=account.fakeid, account_name=account.nickname))
    )
    preview = await preview_use_case.execute(account=account, keyword="Python", recent_count=50)
    use_case = ExportRelatedAccountArticlesUseCase(
        fetch_use_case=_FakeFetchArticleUseCase({}),
        summarize_use_case=_FakeSummarizeArticleUseCase(
            Summary(content="摘要", method=SummaryMethod.SIMPLE, style=SummaryStyle.CONCISE)
        ),
        link_exporter=_FakeLinkExporter(),
        package_exporter=_FakeArticlePackageExporter(),
        output_root=tmp_path,
    )

    with pytest.raises(ValidationError, match="没有可导出的相关文章"):
        use_case.execute(preview=preview, summarizer_method="simple")
