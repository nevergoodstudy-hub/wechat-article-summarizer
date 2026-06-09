"""单篇处理页面

从 WechatSummarizerGUI 提取的单篇文章处理页面。
采用 CustomTkinter CTkFrame 子类化 + controller 模式。

2026 UI 增强:
- 剪贴板智能检测（自动识别微信链接）
- 摘要/要点复制按钮
- 处理中 skeleton 状态
"""

from __future__ import annotations

import contextlib
import re

from ..frames.single_article import SingleArticleInputFrame, SingleArticleResultFrame
from ..frames.single_clipboard import SingleClipboardBannerFrame
from ..utils.i18n import tr

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False

_WECHAT_URL_RE = re.compile(r"https?://mp\.weixin\.qq\.com/s[/?]")


class SinglePage(ctk.CTkFrame):
    """单篇文章处理页面

    Args:
        master: 父容器
        gui: WechatSummarizerGUI 控制器引用
    """

    def __init__(self, master, gui, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui

        # 公开属性 - 供外部通过别名访问
        self.url_entry = None
        self.url_status_label = None
        self.method_var = None
        self.method_menu = None
        self.summarize_var = None
        self.fetch_btn = None
        self.export_btn = None
        self.preview_text = None
        self.title_label = None
        self.author_label = None
        self.word_count_label = None
        self.summary_text = None
        self.points_text = None

        self._clipboard_banner: ctk.CTkFrame | None = None
        self._unsubscribe_navigate = None
        if hasattr(self.gui, "event_bus"):
            self._unsubscribe_navigate = self.gui.event_bus.subscribe(
                "navigate", self._on_navigate_event
            )
        self._build()

    # ==================================================================
    # 剪贴板智能检测
    # ==================================================================

    def on_page_shown(self) -> None:
        """页面显示时调用 - 检测剪贴板中的微信链接"""
        with contextlib.suppress(Exception):
            clip = self.clipboard_get().strip()
            if clip and _WECHAT_URL_RE.match(clip):
                current = self.url_entry.get().strip() if self.url_entry else ""
                if clip != current:
                    self._show_clipboard_banner(clip)

    def _on_navigate_event(self, *, from_page: str, to_page: str) -> None:
        """响应导航事件。"""
        _ = from_page
        if to_page == self.gui.PAGE_SINGLE:
            self.on_page_shown()

    def _show_clipboard_banner(self, url: str) -> None:
        """显示剪贴板智能提示横幅"""
        self._dismiss_clipboard_banner()
        banner = SingleClipboardBannerFrame(
            self,
            url=url,
            on_apply=self._apply_clipboard,
            on_dismiss=self._dismiss_clipboard_banner,
        )
        # 插入到最顶部
        banner.pack(fill="x", pady=(0, 8), before=self.winfo_children()[0])
        self._clipboard_banner = banner

    def _apply_clipboard(self, url: str) -> None:
        """应用剪贴板链接"""
        if self.url_entry:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url)
            with contextlib.suppress(Exception):
                self.gui._on_url_input_change()
        self._dismiss_clipboard_banner()

    def _dismiss_clipboard_banner(self) -> None:
        """关闭剪贴板横幅"""
        if self._clipboard_banner:
            with contextlib.suppress(Exception):
                self._clipboard_banner.destroy()
            self._clipboard_banner = None

    # ==================================================================
    # 复制辅助
    # ==================================================================

    def _copy_textbox(self, textbox: ctk.CTkTextbox, label: str = "内容") -> None:
        """复制 textbox 内容到剪贴板"""
        text = textbox.get("1.0", "end").strip()
        if not text:
            return
        with contextlib.suppress(Exception):
            self.clipboard_clear()
            self.clipboard_append(text)
        # toast 提示
        if hasattr(self.gui, "_toast_manager") and self.gui._toast_manager:
            self.gui._toast_manager.success(f"已复制{label}")

    def _build(self):
        """构建单篇处理页面"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(
            header, text=tr("📄 单篇文章处理"), font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self.input_frame = SingleArticleInputFrame(content, gui=self.gui)
        self.input_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        self.result_frame = SingleArticleResultFrame(
            content,
            gui=self.gui,
            copy_textbox=self._copy_textbox,
        )
        self.result_frame.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        self.url_entry = self.input_frame.url_entry
        self.url_status_label = self.input_frame.url_status_label
        self.method_var = self.input_frame.method_var
        self.method_menu = self.input_frame.method_menu
        self.summarize_var = self.input_frame.summarize_var
        self.fetch_btn = self.input_frame.fetch_btn
        self.export_btn = self.input_frame.export_btn
        self.preview_text = self.input_frame.preview_text
        self.title_label = self.result_frame.title_label
        self.author_label = self.result_frame.author_label
        self.word_count_label = self.result_frame.word_count_label
        self.summary_text = self.result_frame.summary_text
        self.points_text = self.result_frame.points_text
