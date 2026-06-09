"""批量处理页面

从 WechatSummarizerGUI 提取的批量文章处理页面。
采用 CustomTkinter CTkFrame 子类化 + controller 模式。
"""

from __future__ import annotations

from ..frames.batch_processing import BatchInputFrame, BatchResultsFrame
from ..utils.i18n import tr

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False


class BatchPage(ctk.CTkFrame):
    """批量文章处理页面

    Args:
        master: 父容器
        gui: WechatSummarizerGUI 控制器引用
    """

    def __init__(self, master, gui, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui

        self.batch_url_text = None
        self.batch_url_status_label = None
        self.batch_method_var = None
        self.concurrency_var = None
        self.batch_start_btn = None
        self.batch_stop_btn = None
        self.batch_result_frame = None
        self.batch_progress = None
        self.batch_status_label = None
        self.batch_elapsed_label = None
        self.batch_eta_label = None
        self.batch_rate_label = None
        self.batch_count_label = None
        self.batch_export_word_btn = None
        self.batch_export_md_btn = None
        self.batch_export_btn = None
        self.batch_export_html_btn = None
        self._unsubscribe_navigate = None
        if hasattr(self.gui, "event_bus"):
            self._unsubscribe_navigate = self.gui.event_bus.subscribe(
                "navigate", self._on_navigate_event
            )

        self._build()

    def _build(self) -> None:
        """构建批量处理页面"""
        ctk.CTkLabel(
            self, text=tr("📚 批量文章处理"), font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w", pady=(0, 20))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self.input_frame = BatchInputFrame(content, gui=self.gui, stop_command=self._on_stop_batch)
        self.input_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        self.results_frame = BatchResultsFrame(content, gui=self.gui)
        self.results_frame.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        self.batch_url_text = self.input_frame.batch_url_text
        self.batch_url_status_label = self.input_frame.batch_url_status_label
        self.batch_method_var = self.input_frame.batch_method_var
        self.concurrency_var = self.input_frame.concurrency_var
        self.batch_start_btn = self.input_frame.batch_start_btn
        self.batch_stop_btn = self.input_frame.batch_stop_btn
        self.batch_result_frame = self.results_frame.batch_result_frame
        self.batch_progress = self.results_frame.batch_progress
        self.batch_status_label = self.results_frame.batch_status_label
        self.batch_elapsed_label = self.results_frame.batch_elapsed_label
        self.batch_eta_label = self.results_frame.batch_eta_label
        self.batch_rate_label = self.results_frame.batch_rate_label
        self.batch_count_label = self.results_frame.batch_count_label
        self.batch_export_word_btn = self.results_frame.batch_export_word_btn
        self.batch_export_md_btn = self.results_frame.batch_export_md_btn
        self.batch_export_btn = self.results_frame.batch_export_btn
        self.batch_export_html_btn = self.results_frame.batch_export_html_btn

    def _on_navigate_event(self, *, from_page: str, to_page: str) -> None:
        """响应导航事件（保留扩展点）。"""
        _ = from_page
        if to_page == self.gui.PAGE_BATCH:
            return None

    def _on_stop_batch(self) -> None:
        """停止批量处理"""
        if hasattr(self.gui, "_batch_cancel_requested"):
            self.gui._batch_cancel_requested = True
        self.batch_stop_btn.configure(state="disabled")
        self.batch_status_label.configure(text=tr("正在停止…"))

    def set_processing_state(self, processing: bool) -> None:
        """切换开始/停止按钮状态"""
        if processing:
            self.batch_start_btn.configure(state="disabled")
            self.batch_stop_btn.configure(state="normal")
        else:
            self.batch_start_btn.configure(state="normal")
            self.batch_stop_btn.configure(state="disabled")
