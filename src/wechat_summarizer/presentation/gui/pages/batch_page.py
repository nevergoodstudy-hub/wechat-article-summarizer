"""批量处理页面壳层。"""

from __future__ import annotations

from ..components.official_account_workflow_panel import OfficialAccountWorkflowPanel
from ..components.url_batch_panel import UrlBatchPanel
from ..styles.colors import ModernColors
from ..styles.spacing import Spacing
from ..utils.i18n import tr

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False


class BatchPage(ctk.CTkFrame):
    """在 URL 批处理与公众号工作流之间切换的壳层页面。"""

    MODE_URL_BATCH = "url_batch"
    MODE_OFFICIAL_ACCOUNT = "official_account"

    def __init__(self, master, gui, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui
        self._mode_var = ctk.StringVar(value=self.MODE_URL_BATCH)
        self._build()
        self._expose_url_batch_aliases()
        self._show_active_panel()

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text=tr("📚 批量工作流"),
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(anchor="w", pady=(0, 20))

        switch_card = ctk.CTkFrame(
            self,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
        )
        switch_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            switch_card,
            text=tr("选择工作模式"),
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=20, pady=12)

        ctk.CTkSegmentedButton(
            switch_card,
            values=[self.MODE_URL_BATCH, self.MODE_OFFICIAL_ACCOUNT],
            variable=self._mode_var,
            command=lambda _value: self._show_active_panel(),
            width=320,
        ).pack(side="right", padx=20, pady=12)

        self._panel_container = ctk.CTkFrame(self, fg_color="transparent")
        self._panel_container.pack(fill="both", expand=True)

        self.url_batch_panel = UrlBatchPanel(self._panel_container, gui=self.gui)
        self.official_account_workflow_panel = OfficialAccountWorkflowPanel(
            self._panel_container,
            gui=self.gui,
        )

    def _expose_url_batch_aliases(self) -> None:
        self.batch_url_text = self.url_batch_panel.batch_url_text
        self.batch_url_status_label = self.url_batch_panel.batch_url_status_label
        self.batch_method_var = self.url_batch_panel.batch_method_var
        self.concurrency_var = self.url_batch_panel.concurrency_var
        self.batch_start_btn = self.url_batch_panel.batch_start_btn
        self.batch_result_frame = self.url_batch_panel.batch_result_frame
        self.batch_progress = self.url_batch_panel.batch_progress
        self.batch_status_label = self.url_batch_panel.batch_status_label
        self.batch_elapsed_label = self.url_batch_panel.batch_elapsed_label
        self.batch_eta_label = self.url_batch_panel.batch_eta_label
        self.batch_rate_label = self.url_batch_panel.batch_rate_label
        self.batch_count_label = self.url_batch_panel.batch_count_label
        self.batch_export_word_btn = self.url_batch_panel.batch_export_word_btn
        self.batch_export_md_btn = self.url_batch_panel.batch_export_md_btn
        self.batch_export_btn = self.url_batch_panel.batch_export_btn
        self.batch_export_html_btn = self.url_batch_panel.batch_export_html_btn

    def _get_active_panel(self):
        if self._mode_var.get() == self.MODE_OFFICIAL_ACCOUNT:
            return self.official_account_workflow_panel
        return self.url_batch_panel

    def _show_active_panel(self) -> None:
        self.url_batch_panel.pack_forget()
        self.official_account_workflow_panel.pack_forget()
        self._get_active_panel().pack(fill="both", expand=True)

    def on_page_shown(self) -> None:
        active_panel = self._get_active_panel()
        if hasattr(active_panel, "on_page_shown"):
            active_panel.on_page_shown()

    def set_processing_state(self, processing: bool) -> None:
        self.url_batch_panel.set_processing_state(processing)
