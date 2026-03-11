"""公众号工作流 ViewModel 测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from wechat_summarizer.application.ports.outbound.auth_port import AuthCredentials, QRCodeData
from wechat_summarizer.application.use_cases.export_related_account_articles_use_case import (
    RelatedAccountArticlesExportResult,
)
from wechat_summarizer.application.use_cases.preview_related_account_articles_use_case import (
    RelatedAccountArticlesPreview,
)
from wechat_summarizer.application.use_cases.search_official_accounts_use_case import (
    SearchOfficialAccountsResult,
)
from wechat_summarizer.domain.entities.article_list import ArticleListItem
from wechat_summarizer.domain.entities.official_account import OfficialAccount
from wechat_summarizer.presentation.gui.viewmodels.official_account_workflow_viewmodel import (
    OfficialAccountWorkflowState,
    OfficialAccountWorkflowViewModel,
)


def _build_preview(account: OfficialAccount, matched_count: int) -> RelatedAccountArticlesPreview:
    matched_articles = [
        ArticleListItem(
            aid=f"{index}",
            title=f"Python 文章 {index}",
            link=f"https://mp.weixin.qq.com/s/python-{index}",
            digest="Python 相关文章",
            update_time=100 - index,
        )
        for index in range(matched_count)
    ]
    return RelatedAccountArticlesPreview(
        account=account,
        keyword="Python",
        recent_count=50,
        total_articles=max(matched_count, 3),
        available_total=20,
        matched_articles=matched_articles,
    )


class _FakeAuthManager:
    def __init__(
        self,
        *,
        authenticated: bool = False,
        poll_responses: list[tuple[int, AuthCredentials | None]] | None = None,
    ) -> None:
        self._authenticated = authenticated
        self._poll_responses = list(poll_responses or [])

    @property
    def is_authenticated(self) -> bool:
        return self._authenticated

    async def get_qrcode(self) -> QRCodeData:
        return QRCodeData(
            qrcode_url="https://mp.weixin.qq.com/cgi-bin/loginqrcode?action=getqrcode",
            uuid="uuid-123",
            expires_in=300,
        )

    async def poll_scan_status(self, uuid: str) -> tuple[int, AuthCredentials | None]:
        assert uuid == "uuid-123"
        status, credentials = self._poll_responses.pop(0)
        if status == 2:
            self._authenticated = True
        return status, credentials


class _FakeSearchUseCase:
    def __init__(self, accounts: list[OfficialAccount]) -> None:
        self.accounts = accounts
        self.calls: list[tuple[str, int]] = []

    async def execute(self, query: str, limit: int = 10) -> SearchOfficialAccountsResult:
        self.calls.append((query, limit))
        return SearchOfficialAccountsResult(query=query, accounts=self.accounts[:limit])


class _FakePreviewUseCase:
    def __init__(self, preview: RelatedAccountArticlesPreview) -> None:
        self.preview = preview
        self.calls: list[tuple[OfficialAccount, str, int]] = []

    async def execute(
        self,
        *,
        account: OfficialAccount,
        keyword: str,
        recent_count: int = 50,
    ) -> RelatedAccountArticlesPreview:
        self.calls.append((account, keyword, recent_count))
        return self.preview


class _FakeExportUseCase:
    def __init__(self, result: RelatedAccountArticlesExportResult) -> None:
        self.result = result
        self.calls: list[tuple[RelatedAccountArticlesPreview, str | None]] = []

    def execute(
        self,
        *,
        preview: RelatedAccountArticlesPreview,
        summarizer_method: str | None = None,
    ) -> RelatedAccountArticlesExportResult:
        self.calls.append((preview, summarizer_method))
        return self.result


@pytest.mark.unit
def test_refresh_authentication_sets_authenticated_state() -> None:
    account = OfficialAccount(fakeid="MzA1", nickname="Python之禅", alias="python")
    viewmodel = OfficialAccountWorkflowViewModel(
        auth_manager=_FakeAuthManager(authenticated=True),
        search_use_case=_FakeSearchUseCase([account]),
        preview_use_case=_FakePreviewUseCase(_build_preview(account, matched_count=1)),
        export_use_case=_FakeExportUseCase(
            RelatedAccountArticlesExportResult(
                output_dir=Path("output"),
                matched_count=1,
                exported_count=1,
                link_exports={},
                search_result_path=Path("search_result.json"),
                export_report_path=Path("export_report.json"),
                package_path=Path("articles.zip"),
                failures=[],
            )
        ),
    )

    viewmodel.refresh_authentication()

    assert viewmodel.workflow_state == OfficialAccountWorkflowState.AUTHENTICATED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_qrcode_stores_qrcode_and_moves_to_waiting_scan() -> None:
    account = OfficialAccount(fakeid="MzA1", nickname="Python之禅", alias="python")
    viewmodel = OfficialAccountWorkflowViewModel(
        auth_manager=_FakeAuthManager(),
        search_use_case=_FakeSearchUseCase([account]),
        preview_use_case=_FakePreviewUseCase(_build_preview(account, matched_count=1)),
        export_use_case=_FakeExportUseCase(
            RelatedAccountArticlesExportResult(
                output_dir=Path("output"),
                matched_count=1,
                exported_count=1,
                link_exports={},
                search_result_path=Path("search_result.json"),
                export_report_path=Path("export_report.json"),
                package_path=Path("articles.zip"),
                failures=[],
            )
        ),
    )

    await viewmodel.fetch_qrcode()

    assert viewmodel.workflow_state == OfficialAccountWorkflowState.WAITING_SCAN
    assert viewmodel.qrcode_url.endswith("action=getqrcode")
    assert viewmodel.qrcode_uuid == "uuid-123"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_poll_login_status_transitions_scan_confirmed_then_authenticated() -> None:
    account = OfficialAccount(fakeid="MzA1", nickname="Python之禅", alias="python")
    auth = _FakeAuthManager(
        poll_responses=[
            (1, None),
            (
                2,
                AuthCredentials(token="123", cookies={"pass_ticket": "ticket"}),
            ),
        ]
    )
    viewmodel = OfficialAccountWorkflowViewModel(
        auth_manager=auth,
        search_use_case=_FakeSearchUseCase([account]),
        preview_use_case=_FakePreviewUseCase(_build_preview(account, matched_count=1)),
        export_use_case=_FakeExportUseCase(
            RelatedAccountArticlesExportResult(
                output_dir=Path("output"),
                matched_count=1,
                exported_count=1,
                link_exports={},
                search_result_path=Path("search_result.json"),
                export_report_path=Path("export_report.json"),
                package_path=Path("articles.zip"),
                failures=[],
            )
        ),
    )
    await viewmodel.fetch_qrcode()

    await viewmodel.poll_login_status()
    assert viewmodel.workflow_state == OfficialAccountWorkflowState.SCAN_CONFIRMED

    await viewmodel.poll_login_status()
    assert viewmodel.workflow_state == OfficialAccountWorkflowState.AUTHENTICATED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_preview_and_export_flow_reaches_completed_state() -> None:
    account = OfficialAccount(fakeid="MzA1", nickname="Python之禅", alias="python")
    preview = _build_preview(account, matched_count=1)
    export_result = RelatedAccountArticlesExportResult(
        output_dir=Path("output"),
        matched_count=1,
        exported_count=1,
        link_exports={"csv": Path("matched_links.csv")},
        search_result_path=Path("search_result.json"),
        export_report_path=Path("export_report.json"),
        package_path=Path("articles.zip"),
        failures=[],
    )
    search_use_case = _FakeSearchUseCase([account])
    preview_use_case = _FakePreviewUseCase(preview)
    export_use_case = _FakeExportUseCase(export_result)
    viewmodel = OfficialAccountWorkflowViewModel(
        auth_manager=_FakeAuthManager(authenticated=True),
        search_use_case=search_use_case,
        preview_use_case=preview_use_case,
        export_use_case=export_use_case,
    )

    viewmodel.refresh_authentication()
    await viewmodel.search_accounts("Python", limit=5)
    viewmodel.select_account(account)
    await viewmodel.preview_selected_account(keyword="Python", recent_count=50)
    result = viewmodel.export_selected_articles(summarizer_method="simple")

    assert search_use_case.calls == [("Python", 5)]
    assert preview_use_case.calls == [(account, "Python", 50)]
    assert export_use_case.calls == [(preview, "simple")]
    assert result == export_result
    assert viewmodel.workflow_state == OfficialAccountWorkflowState.COMPLETED
    assert viewmodel.accounts == [account]
    assert viewmodel.selected_account == account
    assert viewmodel.preview_result == preview
    assert viewmodel.last_export_result == export_result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_preview_with_zero_matches_keeps_account_selected_state() -> None:
    account = OfficialAccount(fakeid="MzA1", nickname="Python之禅", alias="python")
    viewmodel = OfficialAccountWorkflowViewModel(
        auth_manager=_FakeAuthManager(authenticated=True),
        search_use_case=_FakeSearchUseCase([account]),
        preview_use_case=_FakePreviewUseCase(_build_preview(account, matched_count=0)),
        export_use_case=_FakeExportUseCase(
            RelatedAccountArticlesExportResult(
                output_dir=Path("output"),
                matched_count=0,
                exported_count=0,
                link_exports={},
                search_result_path=Path("search_result.json"),
                export_report_path=Path("export_report.json"),
                package_path=Path("articles.zip"),
                failures=[],
            )
        ),
    )

    viewmodel.refresh_authentication()
    viewmodel.select_account(account)
    await viewmodel.preview_selected_account(keyword="Python", recent_count=50)

    assert viewmodel.workflow_state == OfficialAccountWorkflowState.ACCOUNT_SELECTED
    assert viewmodel.preview_result is not None
    assert viewmodel.preview_result.matched_count == 0
