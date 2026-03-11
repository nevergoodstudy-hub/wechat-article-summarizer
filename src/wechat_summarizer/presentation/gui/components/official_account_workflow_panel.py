"""公众号搜索工作流面板。"""

from __future__ import annotations

import asyncio
import contextlib
import threading
import webbrowser
from tkinter import messagebox

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing
from ..utils.i18n import tr
from ..viewmodels.official_account_workflow_viewmodel import (
    OfficialAccountWorkflowState,
    OfficialAccountWorkflowViewModel,
)

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False


class OfficialAccountWorkflowPanel(ctk.CTkFrame):
    """公众号搜索、预览与导出工作流面板。"""

    def __init__(self, master, gui, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui
        self.viewmodel = OfficialAccountWorkflowViewModel(
            auth_manager=self.gui.container.wechat_auth_manager,
            search_use_case=self.gui.container.search_official_accounts_use_case,
            preview_use_case=self.gui.container.preview_related_account_articles_use_case,
            export_use_case=self.gui.container.export_related_account_articles_use_case,
        )
        self._poll_after_id = None
        self._search_query_var = ctk.StringVar(value="")
        self._keyword_var = ctk.StringVar(value="")
        self._recent_count_var = ctk.StringVar(value="50")
        export_methods = self._available_export_methods()
        self._export_method_var = ctk.StringVar(value=export_methods[0])
        self._build()
        self.viewmodel.refresh_authentication()
        self._refresh_from_viewmodel()

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text=tr("🔎 公众号搜索与相关文章导出"),
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(anchor="w", pady=(0, 16))

        self.workflow_status_label = ctk.CTkLabel(
            self,
            text="",
            anchor="w",
            justify="left",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.workflow_status_label.pack(fill="x", pady=(0, 10))

        self._build_auth_card()
        self._build_search_card()
        self._build_accounts_card()
        self._build_preview_card()
        self._build_export_card()

    def _build_auth_card(self) -> None:
        card = self._create_card()
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            card,
            text=tr("🔐 登录"),
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(16, 6))

        self.auth_state_label = ctk.CTkLabel(
            card,
            text="",
            anchor="w",
            justify="left",
            font=ctk.CTkFont(size=12),
        )
        self.auth_state_label.pack(fill="x", padx=20)

        self.qrcode_url_label = ctk.CTkLabel(
            card,
            text="",
            anchor="w",
            justify="left",
            wraplength=760,
            font=ctk.CTkFont(size=11),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        )
        self.qrcode_url_label.pack(fill="x", padx=20, pady=(6, 0))

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=(10, 16))

        self.login_btn = self.gui._create_modern_button(
            actions,
            text=tr("📱 获取二维码"),
            command=self._on_request_qrcode,
            variant="primary",
            size="small",
        )
        self.login_btn.pack(side="left", padx=(0, 8))

        self.open_qrcode_btn = self.gui._create_modern_button(
            actions,
            text=tr("🌐 打开二维码"),
            command=self._open_qrcode_in_browser,
            variant="ghost",
            size="small",
        )
        self.open_qrcode_btn.pack(side="left", padx=(0, 8))

        self.poll_btn = self.gui._create_modern_button(
            actions,
            text=tr("🔄 检查扫码状态"),
            command=self._on_poll_login,
            variant="ghost",
            size="small",
        )
        self.poll_btn.pack(side="left")

    def _build_search_card(self) -> None:
        card = self._create_card()
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            card,
            text=tr("🧭 搜索条件"),
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(16, 10))

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=(0, 10))
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(form, text=tr("公众号:")).grid(row=0, column=0, sticky="w")
        ctk.CTkEntry(form, textvariable=self._search_query_var).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(8, 16),
        )

        ctk.CTkLabel(form, text=tr("关键词:")).grid(row=0, column=2, sticky="w")
        ctk.CTkEntry(form, textvariable=self._keyword_var).grid(
            row=0,
            column=3,
            sticky="ew",
            padx=(8, 0),
        )

        ctk.CTkLabel(form, text=tr("最近文章数:")).grid(row=1, column=0, sticky="w", pady=(10, 0))
        ctk.CTkEntry(form, textvariable=self._recent_count_var, width=120).grid(
            row=1,
            column=1,
            sticky="w",
            padx=(8, 16),
            pady=(10, 0),
        )

        action_row = ctk.CTkFrame(card, fg_color="transparent")
        action_row.pack(fill="x", padx=20, pady=(0, 16))

        self.search_btn = self.gui._create_modern_button(
            action_row,
            text=tr("🔍 搜索公众号"),
            command=self._on_search_accounts,
            variant="primary",
            size="small",
        )
        self.search_btn.pack(side="left", padx=(0, 8))

        self.preview_btn = self.gui._create_modern_button(
            action_row,
            text=tr("📝 预览相关文章"),
            command=self._on_preview_articles,
            variant="ghost",
            size="small",
        )
        self.preview_btn.pack(side="left")

    def _build_accounts_card(self) -> None:
        card = self._create_card()
        card.pack(fill="both", expand=True, pady=(0, 12))

        ctk.CTkLabel(
            card,
            text=tr("📚 公众号候选"),
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(16, 10))

        self.accounts_frame = ctk.CTkScrollableFrame(card, height=150)
        self.accounts_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def _build_preview_card(self) -> None:
        card = self._create_card()
        card.pack(fill="both", expand=True, pady=(0, 12))

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))

        ctk.CTkLabel(
            header,
            text=tr("🗂️ 相关文章预览"),
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        self.preview_stats_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=12),
        )
        self.preview_stats_label.pack(side="right")

        self.preview_frame = ctk.CTkScrollableFrame(card, height=180)
        self.preview_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def _build_export_card(self) -> None:
        card = self._create_card()
        card.pack(fill="x")

        ctk.CTkLabel(
            card,
            text=tr("📤 导出"),
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(16, 10))

        controls = ctk.CTkFrame(card, fg_color="transparent")
        controls.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(controls, text=tr("摘要方法:")).pack(side="left")
        self.export_method_menu = ctk.CTkOptionMenu(
            controls,
            values=self._available_export_methods(),
            variable=self._export_method_var,
            width=140,
            height=32,
        )
        self.export_method_menu.pack(side="left", padx=(10, 20))

        self.export_btn = self.gui._create_modern_button(
            controls,
            text=tr("📦 导出链接与内容包"),
            command=self._on_export,
            variant="primary",
            size="small",
        )
        self.export_btn.pack(side="right")

    def _create_card(self):
        return ctk.CTkFrame(
            self,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
        )

    def on_page_shown(self) -> None:
        if self.viewmodel.workflow_state not in {
            OfficialAccountWorkflowState.WAITING_SCAN,
            OfficialAccountWorkflowState.SCAN_CONFIRMED,
        }:
            self.viewmodel.refresh_authentication()
        self._refresh_from_viewmodel()

    def _on_request_qrcode(self) -> None:
        self._cancel_poll()
        self._run_async(self.viewmodel.fetch_qrcode)

    def _on_poll_login(self) -> None:
        self._run_async(self.viewmodel.poll_login_status)

    def _on_search_accounts(self) -> None:
        self._run_async(
            lambda: self.viewmodel.search_accounts(
                self._search_query_var.get(),
                limit=10,
            )
        )

    def _on_select_account(self, account) -> None:
        self.viewmodel.select_account(account)
        self._refresh_from_viewmodel()
        if self._keyword_var.get().strip():
            self._on_preview_articles()

    def _on_preview_articles(self) -> None:
        self._run_async(
            lambda: self.viewmodel.preview_selected_account(
                keyword=self._keyword_var.get(),
                recent_count=self._parse_recent_count(),
            )
        )

    def _on_export(self) -> None:
        check_export_dir = getattr(self.gui, "_check_export_dir_configured", None)
        if callable(check_export_dir) and not check_export_dir():
            return
        self._run_sync(
            lambda: self.viewmodel.export_selected_articles(
                summarizer_method=self._export_method_var.get(),
            ),
            on_complete=self._handle_export_complete,
        )

    def _open_qrcode_in_browser(self) -> None:
        if self.viewmodel.qrcode_url:
            webbrowser.open(self.viewmodel.qrcode_url)

    def _run_async(self, coroutine_factory) -> None:
        def worker() -> None:
            asyncio.run(coroutine_factory())
            self.after(0, self._after_background_update)

        threading.Thread(target=worker, daemon=True).start()

    def _run_sync(self, func, on_complete=None) -> None:
        def worker() -> None:
            result = func()
            if on_complete is None:
                self.after(0, self._after_background_update)
            else:
                self.after(0, lambda: on_complete(result))

        threading.Thread(target=worker, daemon=True).start()

    def _after_background_update(self) -> None:
        self._refresh_from_viewmodel()
        if self.viewmodel.workflow_state in {
            OfficialAccountWorkflowState.WAITING_SCAN,
            OfficialAccountWorkflowState.SCAN_CONFIRMED,
        }:
            self._schedule_poll()
        elif self.viewmodel.workflow_state in {
            OfficialAccountWorkflowState.AUTHENTICATED,
            OfficialAccountWorkflowState.FAILED,
            OfficialAccountWorkflowState.COMPLETED,
        }:
            self._cancel_poll()

    def _handle_export_complete(self, result) -> None:
        self._refresh_from_viewmodel()
        if result is not None:
            messagebox.showinfo(
                "导出完成",
                f"已导出 {result.exported_count}/{result.matched_count} 篇相关文章\n输出目录: {result.output_dir}",
            )

    def _schedule_poll(self) -> None:
        if self._poll_after_id is not None:
            return

        def poll_again() -> None:
            self._poll_after_id = None
            self._on_poll_login()

        self._poll_after_id = self.after(2000, poll_again)

    def _cancel_poll(self) -> None:
        if self._poll_after_id is None:
            return
        with contextlib.suppress(Exception):
            self.after_cancel(self._poll_after_id)
        self._poll_after_id = None

    def _refresh_from_viewmodel(self) -> None:
        state = self.viewmodel.workflow_state
        status_map = {
            OfficialAccountWorkflowState.UNAUTHENTICATED: tr("请先登录微信公众平台"),
            OfficialAccountWorkflowState.FETCHING_QRCODE: tr("正在获取登录二维码…"),
            OfficialAccountWorkflowState.WAITING_SCAN: tr("请使用微信扫码"),
            OfficialAccountWorkflowState.SCAN_CONFIRMED: tr("已扫码，请在手机上确认"),
            OfficialAccountWorkflowState.AUTHENTICATED: tr("已登录，可以搜索公众号"),
            OfficialAccountWorkflowState.SEARCHING_ACCOUNTS: tr("正在搜索公众号候选…"),
            OfficialAccountWorkflowState.ACCOUNT_SELECTED: tr("公众号已选择，可以预览相关文章"),
            OfficialAccountWorkflowState.PREVIEWING_ARTICLES: tr("正在拉取近期文章并按关键词过滤…"),
            OfficialAccountWorkflowState.READY_TO_EXPORT: tr("预览已就绪，可以导出"),
            OfficialAccountWorkflowState.EXPORTING: tr("正在导出链接清单与内容包…"),
            OfficialAccountWorkflowState.COMPLETED: tr("导出完成"),
            OfficialAccountWorkflowState.FAILED: self.viewmodel.error_message or tr("工作流执行失败"),
        }
        status_text = status_map[state]
        status_color = (
            ModernColors.ERROR
            if state == OfficialAccountWorkflowState.FAILED
            else ModernColors.INFO
        )
        self.workflow_status_label.configure(text=status_text, text_color=status_color)

        if hasattr(self.gui, "_set_status"):
            self.gui._set_status(
                status_text,
                status_color,
                pulse=state
                in {
                    OfficialAccountWorkflowState.FETCHING_QRCODE,
                    OfficialAccountWorkflowState.SEARCHING_ACCOUNTS,
                    OfficialAccountWorkflowState.PREVIEWING_ARTICLES,
                    OfficialAccountWorkflowState.EXPORTING,
                },
            )

        authenticated = state in {
            OfficialAccountWorkflowState.AUTHENTICATED,
            OfficialAccountWorkflowState.SEARCHING_ACCOUNTS,
            OfficialAccountWorkflowState.ACCOUNT_SELECTED,
            OfficialAccountWorkflowState.PREVIEWING_ARTICLES,
            OfficialAccountWorkflowState.READY_TO_EXPORT,
            OfficialAccountWorkflowState.EXPORTING,
            OfficialAccountWorkflowState.COMPLETED,
        }
        self.auth_state_label.configure(
            text=tr("已登录") if authenticated else tr("未登录"),
        )
        self.qrcode_url_label.configure(
            text=self.viewmodel.qrcode_url or tr("二维码获取后会显示在这里"),
        )
        self.login_btn.configure(state="disabled" if authenticated else "normal")
        self.open_qrcode_btn.configure(
            state="normal" if self.viewmodel.qrcode_url else "disabled",
        )
        self.poll_btn.configure(
            state="normal" if self.viewmodel.qrcode_uuid else "disabled",
        )
        self.search_btn.configure(
            state="normal" if authenticated and not self.viewmodel.is_busy else "disabled",
        )
        self.preview_btn.configure(
            state="normal"
            if self.viewmodel.selected_account is not None and not self.viewmodel.is_busy
            else "disabled",
        )
        self.export_btn.configure(
            state="normal"
            if self.viewmodel.preview_result
            and self.viewmodel.preview_result.matched_count > 0
            and not self.viewmodel.is_busy
            else "disabled",
        )

        self._render_accounts()
        self._render_preview()

    def _render_accounts(self) -> None:
        for child in self.accounts_frame.winfo_children():
            child.destroy()

        if not self.viewmodel.accounts:
            ctk.CTkLabel(
                self.accounts_frame,
                text=tr("暂无候选公众号"),
                font=ctk.CTkFont(size=12),
            ).pack(anchor="w", padx=4, pady=4)
            return

        for account in self.viewmodel.accounts:
            is_selected = self.viewmodel.selected_account == account
            button = ctk.CTkButton(
                self.accounts_frame,
                text=account.display_name,
                anchor="w",
                fg_color=ModernColors.INFO if is_selected else ModernColors.NEUTRAL_BTN,
                hover_color=ModernColors.INFO if is_selected else ModernColors.NEUTRAL_BTN_DISABLED,
                command=lambda selected=account: self._on_select_account(selected),
            )
            button.pack(fill="x", pady=(0, 4))
            if account.signature:
                ctk.CTkLabel(
                    self.accounts_frame,
                    text=account.signature,
                    wraplength=720,
                    justify="left",
                    font=ctk.CTkFont(size=11),
                    text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
                ).pack(anchor="w", padx=8, pady=(0, 6))

    def _render_preview(self) -> None:
        for child in self.preview_frame.winfo_children():
            child.destroy()

        preview = self.viewmodel.preview_result
        if preview is None:
            self.preview_stats_label.configure(text=tr("尚未生成预览"))
            ctk.CTkLabel(
                self.preview_frame,
                text=tr("选择公众号后将在这里展示关键词命中的相关文章"),
                font=ctk.CTkFont(size=12),
            ).pack(anchor="w", padx=4, pady=4)
            return

        self.preview_stats_label.configure(
            text=tr(f"扫描 {preview.total_articles} 篇 / 命中 {preview.matched_count} 篇"),
        )

        if preview.matched_count == 0:
            ctk.CTkLabel(
                self.preview_frame,
                text=tr("最近文章中没有命中当前关键词"),
                font=ctk.CTkFont(size=12),
            ).pack(anchor="w", padx=4, pady=4)
            return

        for item in preview.matched_articles:
            wrapper = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
            wrapper.pack(fill="x", pady=4)
            ctk.CTkLabel(
                wrapper,
                text=f"• {item.title}",
                anchor="w",
                justify="left",
                wraplength=720,
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(anchor="w")
            if item.digest:
                ctk.CTkLabel(
                    wrapper,
                    text=item.digest,
                    anchor="w",
                    justify="left",
                    wraplength=720,
                    font=ctk.CTkFont(size=11),
                    text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
                ).pack(anchor="w", padx=12, pady=(2, 0))

    def _available_export_methods(self) -> list[str]:
        methods = [
            name
            for name, info in getattr(self.gui, "_summarizer_info", {}).items()
            if getattr(info, "available", False)
        ]
        if methods:
            return methods
        return ["simple"]

    def _parse_recent_count(self) -> int:
        try:
            value = int(self._recent_count_var.get().strip() or "50")
        except ValueError:
            value = 50
            self._recent_count_var.set("50")
        return max(value, 1)
