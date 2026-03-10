"""LogPanel 日志面板组件

从 WechatSummarizerGUI 提取的可折叠日志面板。
采用 CustomTkinter CTkFrame 子类化模式，内部管理折叠/展开动画。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing
from .animation_helper import AnimationHelper

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False


class LogPanel(ctk.CTkFrame):
    """可折叠日志面板组件

    包含：
    - 日志标题栏（切换/清空/复制按钮）
    - 日志文本区域（带动画折叠/展开）

    Args:
        master: 父容器
        get_font: 字体工厂函数 (size, weight='normal') -> CTkFont
        root: Tk 根窗口（用于动画定时器）
        on_status_change: 状态变更回调 (text, color) -> None
    """

    def __init__(
        self,
        master,
        *,
        get_font: Callable,
        root,
        on_status_change: Callable[[str, str], None] | None = None,
        **kwargs,
    ):
        super().__init__(
            master,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            **kwargs,
        )

        self._get_font = get_font
        self._tk_root = root  # NOTE: must NOT use self._root — it shadows tkinter.Misc._root()
        self._on_status_change = on_status_change
        self._is_expanded = True

        # 公开属性
        self.log_text: ctk.CTkTextbox | None = None
        self.log_toggle_btn: ctk.CTkButton | None = None

        self._build()

    @property
    def is_expanded(self) -> bool:
        """日志面板是否处于展开状态"""
        return self._is_expanded

    def _build(self):
        """构建日志面板"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(10, 5))

        self.log_toggle_btn = ctk.CTkButton(
            header,
            text="📋 日志 ▼",
            font=self._get_font(12),
            width=80,
            height=25,
            fg_color="transparent",
            hover_color=(ModernColors.LIGHT_HOVER_SUBTLE, ModernColors.DARK_HOVER_SUBTLE),
            text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
            command=self.toggle_animated,
        )
        self.log_toggle_btn.pack(side="left")

        # 级别过滤下拉
        self._level_var = ctk.StringVar(value="ALL")
        ctk.CTkOptionMenu(
            header,
            values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR"],
            variable=self._level_var,
            width=90,
            height=25,
            font=self._get_font(10),
            command=self._on_level_filter,
        ).pack(side="left", padx=(8, 4))

        # 搜索框
        self._search_var = ctk.StringVar()
        self._search_entry = ctk.CTkEntry(
            header,
            textvariable=self._search_var,
            placeholder_text="🔍 搜索日志…",
            width=140,
            height=25,
            font=self._get_font(10),
            corner_radius=Spacing.RADIUS_SM,
        )
        self._search_entry.pack(side="left", padx=4)
        self._search_entry.bind("<KeyRelease>", self._on_search)

        ctk.CTkButton(
            header,
            text="清空",
            font=self._get_font(11),
            width=50,
            height=25,
            fg_color="transparent",
            hover_color=(ModernColors.LIGHT_HOVER_SUBTLE, ModernColors.DARK_HOVER_SUBTLE),
            command=self.clear,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            header,
            text="复制",
            font=self._get_font(11),
            width=50,
            height=25,
            fg_color="transparent",
            hover_color=(ModernColors.LIGHT_HOVER_SUBTLE, ModernColors.DARK_HOVER_SUBTLE),
            command=self.copy,
        ).pack(side="left")

        self.log_text = ctk.CTkTextbox(
            self,
            height=120,
            corner_radius=Spacing.RADIUS_MD,
            font=("Consolas", 11),
            state="disabled",
        )
        self.log_text.pack(fill="x", padx=15, pady=(0, 10))
        self._is_expanded = True

        # 配置日志级别颜色标签
        self._setup_log_tags()

    def toggle(self):
        """切换日志面板（无动画）"""
        if self._is_expanded:
            self.log_text.pack_forget()
            self.log_toggle_btn.configure(text="📋 日志 ▶")
            self._is_expanded = False
        else:
            self.log_text.pack(fill="x", padx=15, pady=(0, 10))
            self.log_toggle_btn.configure(text="📋 日志 ▼")
            self._is_expanded = True

    def toggle_animated(self):
        """带动画的日志面板切换"""
        if self._is_expanded:
            self._animate_collapse()
        else:
            self._animate_expand()

    def _animate_expand(self):
        """日志面板展开动画"""
        self.log_text.configure(height=1)
        self.log_text.pack(fill="x", padx=15, pady=(0, 10))
        self.log_toggle_btn.configure(text="📋 日志 ▼")
        self._is_expanded = True

        def update_height(h):
            try:
                self.log_text.configure(height=int(h))
            except Exception:
                return None

        AnimationHelper.animate_value(
            self._tk_root,
            1,
            120,
            200,
            update_height,
            easing=AnimationHelper.ease_out_cubic,
        )

    def _animate_collapse(self):
        """日志面板收起动画"""

        def update_height(h):
            try:
                self.log_text.configure(height=int(h))
            except Exception:
                return None

        def on_complete():
            self.log_text.pack_forget()
            self.log_toggle_btn.configure(text="📋 日志 ▶")
            self._is_expanded = False

        AnimationHelper.animate_value(
            self._tk_root,
            120,
            1,
            200,
            update_height,
            easing=AnimationHelper.ease_out_cubic,
            on_complete=on_complete,
        )

    def _get_internal_textbox(self) -> Any | None:
        """获取 CTkTextbox 底层 tk.Text 控件。"""
        log_text = self.log_text
        if log_text is None:
            return None
        return getattr(log_text, "_textbox", None)

    def _setup_log_tags(self):
        """配置日志级别颜色标签"""
        import contextlib

        tw = self._get_internal_textbox()
        if tw is None:
            return
        with contextlib.suppress(Exception):
            tw.tag_configure("ERROR", foreground=ModernColors.ERROR)
            tw.tag_configure("WARNING", foreground=ModernColors.WARNING)
            tw.tag_configure("SUCCESS", foreground=ModernColors.SUCCESS)
            tw.tag_configure("INFO", foreground=ModernColors.INFO)
            tw.tag_configure("DEBUG", foreground="#888888")
            tw.tag_configure("SEARCH_HIT", background="#facc15", foreground="#000000")
            # 确保 SEARCH_HIT 优先级最高
            tw.tag_raise("SEARCH_HIT")

    def _on_level_filter(self, _value: str = ""):
        """级别过滤 - 显示/隐藏匹配行"""
        import contextlib

        level = self._level_var.get()
        tw = self._get_internal_textbox()
        if tw is None:
            return
        with contextlib.suppress(Exception):
            tw.configure(state="normal")
            tw.tag_remove("hidden", "1.0", "end")
            if level != "ALL":
                # 简单实现：通过前景色调暗非匹配行
                tw.tag_configure("dim", foreground="#555555")
                tw.tag_remove("dim", "1.0", "end")
                line_count = int(tw.index("end-1c").split(".")[0])
                for i in range(1, line_count + 1):
                    line = tw.get(f"{i}.0", f"{i}.end")
                    if level not in line.upper():
                        tw.tag_add("dim", f"{i}.0", f"{i}.end")
            tw.configure(state="disabled")

    def _on_search(self, _event=None):
        """搜索高亮"""
        import contextlib

        query = self._search_var.get().strip()
        tw = self._get_internal_textbox()
        if tw is None:
            return
        with contextlib.suppress(Exception):
            tw.tag_remove("SEARCH_HIT", "1.0", "end")
            if not query:
                return
            start = "1.0"
            while True:
                pos = tw.search(query, start, stopindex="end", nocase=True)
                if not pos:
                    break
                end = f"{pos}+{len(query)}c"
                tw.tag_add("SEARCH_HIT", pos, end)
                start = end

    def clear(self):
        """清空日志"""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def copy(self):
        """复制日志内容到剪贴板"""
        content = self.log_text.get("1.0", "end").strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)
            if self._on_status_change:
                self._on_status_change("已复制到剪贴板", ModernColors.SUCCESS)
