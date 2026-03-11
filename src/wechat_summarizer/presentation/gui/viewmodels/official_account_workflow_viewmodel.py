"""公众号工作流 ViewModel。"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from ....application.use_cases.export_related_account_articles_use_case import (
    RelatedAccountArticlesExportResult,
)
from ....application.use_cases.preview_related_account_articles_use_case import (
    RelatedAccountArticlesPreview,
)
from ....application.use_cases.search_official_accounts_use_case import (
    SearchOfficialAccountsResult,
)
from ....domain.entities.official_account import OfficialAccount
from .base import BaseViewModel, Observable

if TYPE_CHECKING:
    from ....application.use_cases.export_related_account_articles_use_case import (
        ExportRelatedAccountArticlesUseCase,
    )
    from ....application.use_cases.preview_related_account_articles_use_case import (
        PreviewRelatedAccountArticlesUseCase,
    )
    from ....application.use_cases.search_official_accounts_use_case import (
        SearchOfficialAccountsUseCase,
    )


class OfficialAccountWorkflowState(Enum):
    """公众号工作流状态。"""

    UNAUTHENTICATED = "unauthenticated"
    FETCHING_QRCODE = "fetching_qrcode"
    WAITING_SCAN = "waiting_scan"
    SCAN_CONFIRMED = "scan_confirmed"
    AUTHENTICATED = "authenticated"
    SEARCHING_ACCOUNTS = "searching_accounts"
    ACCOUNT_SELECTED = "account_selected"
    PREVIEWING_ARTICLES = "previewing_articles"
    READY_TO_EXPORT = "ready_to_export"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"


class OfficialAccountWorkflowViewModel(BaseViewModel):
    """管理公众号搜索、预览和导出状态。"""

    def __init__(
        self,
        *,
        auth_manager,
        search_use_case: SearchOfficialAccountsUseCase,
        preview_use_case: PreviewRelatedAccountArticlesUseCase,
        export_use_case: ExportRelatedAccountArticlesUseCase,
    ) -> None:
        super().__init__()
        self._auth_manager = auth_manager
        self._search_use_case = search_use_case
        self._preview_use_case = preview_use_case
        self._export_use_case = export_use_case

        self._workflow_state = Observable(OfficialAccountWorkflowState.UNAUTHENTICATED)
        self._accounts = Observable[list[OfficialAccount]]([])
        self._selected_account = Observable[OfficialAccount | None](None)
        self._preview_result = Observable[RelatedAccountArticlesPreview | None](None)
        self._last_export_result = Observable[RelatedAccountArticlesExportResult | None](None)
        self._qrcode_url = Observable("")
        self._qrcode_uuid = Observable("")

    @property
    def workflow_state(self) -> OfficialAccountWorkflowState:
        return self._workflow_state.value

    @property
    def qrcode_url(self) -> str:
        return self._qrcode_url.value

    @property
    def qrcode_uuid(self) -> str:
        return self._qrcode_uuid.value

    @property
    def accounts(self) -> list[OfficialAccount]:
        return self._accounts.value

    @property
    def selected_account(self) -> OfficialAccount | None:
        return self._selected_account.value

    @property
    def preview_result(self) -> RelatedAccountArticlesPreview | None:
        return self._preview_result.value

    @property
    def last_export_result(self) -> RelatedAccountArticlesExportResult | None:
        return self._last_export_result.value

    def refresh_authentication(self) -> None:
        self.error_message = ""
        if getattr(self._auth_manager, "is_authenticated", False):
            self._workflow_state.value = OfficialAccountWorkflowState.AUTHENTICATED
        else:
            self._workflow_state.value = OfficialAccountWorkflowState.UNAUTHENTICATED

    async def fetch_qrcode(self) -> None:
        self.set_loading()
        self._workflow_state.value = OfficialAccountWorkflowState.FETCHING_QRCODE
        try:
            qrcode = await self._auth_manager.get_qrcode()
        except Exception as exc:
            self._set_failed(str(exc))
            return

        self._qrcode_url.value = qrcode.qrcode_url
        self._qrcode_uuid.value = qrcode.uuid
        self.error_message = ""
        self.is_busy = False
        self._workflow_state.value = OfficialAccountWorkflowState.WAITING_SCAN

    async def poll_login_status(self) -> None:
        if not self.qrcode_uuid:
            self._set_failed("二维码尚未生成")
            return

        self.set_loading()
        try:
            status, _credentials = await self._auth_manager.poll_scan_status(self.qrcode_uuid)
        except Exception as exc:
            self._set_failed(str(exc))
            return

        self.error_message = ""
        self.is_busy = False
        if status == 0:
            self._workflow_state.value = OfficialAccountWorkflowState.WAITING_SCAN
        elif status == 1:
            self._workflow_state.value = OfficialAccountWorkflowState.SCAN_CONFIRMED
        elif status == 2:
            self._workflow_state.value = OfficialAccountWorkflowState.AUTHENTICATED
        else:
            self._set_failed("二维码已过期或登录失败")

    async def search_accounts(self, query: str, limit: int = 10) -> SearchOfficialAccountsResult | None:
        self.set_loading()
        self._workflow_state.value = OfficialAccountWorkflowState.SEARCHING_ACCOUNTS
        try:
            result = await self._search_use_case.execute(query, limit=limit)
        except Exception as exc:
            self._set_failed(str(exc))
            return None

        self._accounts.value = result.accounts
        self._selected_account.value = None
        self._preview_result.value = None
        self._last_export_result.value = None
        self.error_message = ""
        self.is_busy = False
        self._workflow_state.value = OfficialAccountWorkflowState.AUTHENTICATED
        return result

    def select_account(self, account: OfficialAccount) -> None:
        self._selected_account.value = account
        self._preview_result.value = None
        self._last_export_result.value = None
        self.error_message = ""
        self._workflow_state.value = OfficialAccountWorkflowState.ACCOUNT_SELECTED

    async def preview_selected_account(
        self,
        *,
        keyword: str,
        recent_count: int = 50,
    ) -> RelatedAccountArticlesPreview | None:
        if self.selected_account is None:
            self._set_failed("请先选择公众号")
            return None

        self.set_loading()
        self._workflow_state.value = OfficialAccountWorkflowState.PREVIEWING_ARTICLES
        try:
            preview = await self._preview_use_case.execute(
                account=self.selected_account,
                keyword=keyword,
                recent_count=recent_count,
            )
        except Exception as exc:
            self._set_failed(str(exc))
            return None

        self._preview_result.value = preview
        self.error_message = ""
        self.is_busy = False
        if preview.matched_count > 0:
            self._workflow_state.value = OfficialAccountWorkflowState.READY_TO_EXPORT
        else:
            self._workflow_state.value = OfficialAccountWorkflowState.ACCOUNT_SELECTED
        return preview

    def export_selected_articles(
        self,
        *,
        summarizer_method: str | None = None,
    ) -> RelatedAccountArticlesExportResult | None:
        if self.preview_result is None:
            self._set_failed("请先预览相关文章")
            return None

        self.set_loading()
        self._workflow_state.value = OfficialAccountWorkflowState.EXPORTING
        try:
            result = self._export_use_case.execute(
                preview=self.preview_result,
                summarizer_method=summarizer_method,
            )
        except Exception as exc:
            self._set_failed(str(exc))
            return None

        self._last_export_result.value = result
        self.error_message = ""
        self.is_busy = False
        self._workflow_state.value = OfficialAccountWorkflowState.COMPLETED
        return result

    def _set_failed(self, message: str) -> None:
        self.set_error(message)
        self._workflow_state.value = OfficialAccountWorkflowState.FAILED
