"""
可折叠侧边栏组件 (CollapsibleSidebar)
符合2026年设计趋势的现代侧边栏

功能特性:
- 展开/收起动画(300ms ease-out)
- 图标模式(60px)与完整模式(240px)切换
- 活动状态指示器(左侧彩色条)
- Tooltip提示(收起状态)
- 徽章通知(未读消息数)
- 子菜单手风琴展开
- 状态持久化

安全措施:
- 徽章数字验证(0-9999)
- 状态文件路径验证
- 输入清洗
- 事件解绑防内存泄漏
"""

import contextlib
import json
import logging
import os
import time
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, cast

logger = logging.getLogger(__name__)


@dataclass
class NavItem:
    """导航项定义"""

    id: str
    label: str
    icon: str = "📄"
    badge: int = 0
    children: list[NavItem] = field(default_factory=list)
    on_click: Callable[[], None] | None = None
    disabled: bool = False


class Tooltip:
    """Tooltip提示组件"""

    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip_window: tk.Toplevel | None = None

        self.widget.bind("<Enter>", self._show)
        self.widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        if self.tooltip_window:
            return

        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 5
        y = self.widget.winfo_rooty()

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            bg="#333333",
            fg="#ffffff",
            font=("Segoe UI", 10),
            padx=8,
            pady=4,
        )
        label.pack()

    def _hide(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def update_text(self, text: str):
        self.text = text

    def destroy(self):
        self._hide()
        self.widget.unbind("<Enter>")
        self.widget.unbind("<Leave>")


class CollapsibleSidebar(tk.Frame):
    """可折叠侧边栏组件"""

    # 常量
    EXPANDED_WIDTH = 240
    COLLAPSED_WIDTH = 60
    ANIMATION_DURATION = 300  # ms
    ANIMATION_STEPS = 15
    MAX_BADGE = 9999

    def __init__(
        self,
        parent: tk.Widget,
        items: list[NavItem],
        on_select: Callable[[str], None] | None = None,
        persist_state: bool = True,
        state_file: str | None = None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self.items = items
        self.on_select = on_select
        self.persist_state = persist_state

        # 状态文件路径验证
        if state_file:
            # 安全检查：防止路径遍历
            base_dir = os.path.dirname(os.path.abspath(__file__))
            abs_path = os.path.abspath(state_file)
            if not abs_path.startswith(base_dir) and not state_file.startswith(
                os.path.expanduser("~")
            ):
                logger.warning(f"不安全的状态文件路径: {state_file}")
                state_file = None

        self.state_file = state_file or os.path.join(
            os.path.expanduser("~"), ".wechat_summarizer", "sidebar_state.json"
        )

        # 状态
        self._expanded = True
        self._current_width = self.EXPANDED_WIDTH
        self._animating = False
        self._active_item: str | None = None
        self._expanded_submenus: set = set()

        # 样式
        self.colors = {
            "bg": "#1a1a1a",
            "item_bg": "#1a1a1a",
            "item_hover": "#2a2a2a",
            "item_active": "#1e3a5f",
            "text": "#e5e5e5",
            "text_secondary": "#808080",
            "accent": "#3b82f6",
            "indicator": "#3b82f6",
            "badge_bg": "#ef4444",
            "badge_text": "#ffffff",
            "border": "#333333",
        }

        self.configure(bg=self.colors["bg"], width=self._current_width)

        # UI元素引用
        self._item_widgets: dict[str, dict[str, Any]] = {}
        self._tooltips: list[Tooltip] = []

        # 加载保存的状态
        self._load_state()

        # 构建UI
        self._setup_ui()

    def _setup_ui(self):
        """构建UI"""
        # Logo/品牌区
        self.header = tk.Frame(self, bg=self.colors["bg"], height=60)
        self.header.pack(fill=tk.X)
        self.header.pack_propagate(False)

        self.logo_label = tk.Label(
            self.header,
            text="📱" if not self._expanded else "📱 WeChat",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=("Segoe UI", 14, "bold"),
        )
        self.logo_label.pack(pady=15)

        # 分隔线
        tk.Frame(self, bg=self.colors["border"], height=1).pack(fill=tk.X)

        # 导航项容器（可滚动）
        self.nav_container = tk.Frame(self, bg=self.colors["bg"])
        self.nav_container.pack(fill=tk.BOTH, expand=True, pady=10)

        # 渲染导航项
        self._render_nav_items()

        # 底部分隔线
        tk.Frame(self, bg=self.colors["border"], height=1).pack(fill=tk.X)

        # 底部工具栏
        self.footer = tk.Frame(self, bg=self.colors["bg"], height=50)
        self.footer.pack(fill=tk.X)
        self.footer.pack_propagate(False)

        # 折叠/展开按钮
        self.toggle_btn = tk.Label(
            self.footer,
            text="◀" if self._expanded else "▶",
            bg=self.colors["bg"],
            fg=self.colors["text_secondary"],
            font=("Segoe UI", 12),
            cursor="hand2",
        )
        self.toggle_btn.pack(pady=12)
        self.toggle_btn.bind("<Button-1>", lambda e: self.toggle())
        self.toggle_btn.bind("<Enter>", lambda e: self.toggle_btn.config(fg=self.colors["text"]))
        self.toggle_btn.bind(
            "<Leave>", lambda e: self.toggle_btn.config(fg=self.colors["text_secondary"])
        )

    def _render_nav_items(self):
        """渲染导航项"""
        # 清理现有项
        for widget in self.nav_container.winfo_children():
            widget.destroy()

        self._item_widgets.clear()
        for tooltip in self._tooltips:
            tooltip.destroy()
        self._tooltips.clear()

        for item in self.items:
            self._create_nav_item(item, self.nav_container, level=0)

    def _create_nav_item(self, item: NavItem, parent: tk.Widget, level: int = 0):
        """创建单个导航项"""
        # 验证徽章数字
        badge = max(0, min(item.badge, self.MAX_BADGE))

        is_active = self._active_item == item.id
        has_children = bool(item.children)
        is_submenu_expanded = item.id in self._expanded_submenus

        # 容器
        item_frame = tk.Frame(parent, bg=self.colors["bg"])
        item_frame.pack(fill=tk.X, padx=5, pady=1)

        # 主行
        row = tk.Frame(
            item_frame,
            bg=self.colors["item_active"] if is_active else self.colors["item_bg"],
            height=44,
        )
        row.pack(fill=tk.X)
        row.pack_propagate(False)

        # 活动指示器（左侧彩色条）
        indicator = tk.Frame(
            row, bg=self.colors["indicator"] if is_active else self.colors["bg"], width=4
        )
        indicator.pack(side=tk.LEFT, fill=tk.Y)

        # 缩进（子菜单）
        if level > 0:
            tk.Frame(row, bg=row.cget("bg"), width=level * 20).pack(side=tk.LEFT)

        # 图标
        icon_label = tk.Label(
            row,
            text=item.icon,
            bg=row.cget("bg"),
            fg=self.colors["text"],
            font=("Segoe UI", 14),
            width=3,
        )
        icon_label.pack(side=tk.LEFT, padx=(10, 5))

        # 标签（展开状态才显示）
        label = tk.Label(
            row,
            text=item.label,
            bg=row.cget("bg"),
            fg=self.colors["text"] if not item.disabled else self.colors["text_secondary"],
            font=("Segoe UI", 11),
            anchor="w",
        )
        if self._expanded:
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 徽章
        badge_label = None
        if badge > 0:
            badge_text = str(badge) if badge < 100 else "99+"
            badge_label = tk.Label(
                row,
                text=badge_text,
                bg=self.colors["badge_bg"],
                fg=self.colors["badge_text"],
                font=("Segoe UI", 9, "bold"),
                padx=5,
                pady=1,
            )
            if self._expanded:
                badge_label.pack(side=tk.RIGHT, padx=10)

        # 子菜单箭头
        arrow_label = None
        if has_children and self._expanded:
            arrow_label = tk.Label(
                row,
                text="▼" if is_submenu_expanded else "▶",
                bg=row.cget("bg"),
                fg=self.colors["text_secondary"],
                font=("Segoe UI", 8),
            )
            arrow_label.pack(side=tk.RIGHT, padx=10)

        # 保存引用
        self._item_widgets[item.id] = {
            "frame": item_frame,
            "row": row,
            "indicator": indicator,
            "icon": icon_label,
            "label": label,
            "badge": badge_label,
            "arrow": arrow_label,
            "item": item,
        }

        # Tooltip（收起状态）
        if not self._expanded:
            tooltip_text = item.label
            if badge > 0:
                tooltip_text += f" ({badge})"
            tooltip = Tooltip(row, tooltip_text)
            self._tooltips.append(tooltip)

        # 事件绑定
        if not item.disabled:

            def on_enter(e, r=row, act=is_active):
                if not act:
                    r.config(bg=self.colors["item_hover"])
                    for child in r.winfo_children():
                        with contextlib.suppress(tk.TclError):
                            child.config(bg=self.colors["item_hover"])

            def on_leave(e, r=row, act=is_active):
                if not act:
                    r.config(bg=self.colors["item_bg"])
                    for child in r.winfo_children():
                        with contextlib.suppress(tk.TclError):
                            child.config(bg=self.colors["item_bg"])

            def on_click(e, i=item):
                self._on_item_click(i)

            for widget in [row, icon_label, label]:
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)
                widget.bind("<Button-1>", on_click)
                cast(Any, widget).configure(cursor="hand2")

        # 子菜单
        if has_children and is_submenu_expanded and self._expanded:
            submenu_frame = tk.Frame(item_frame, bg=self.colors["bg"])
            submenu_frame.pack(fill=tk.X)

            for child in item.children:
                self._create_nav_item(child, submenu_frame, level + 1)

    def _on_item_click(self, item: NavItem):
        """处理项点击"""
        if item.children:
            # 切换子菜单展开状态
            if item.id in self._expanded_submenus:
                self._expanded_submenus.discard(item.id)
            else:
                self._expanded_submenus.add(item.id)
            self._render_nav_items()
        else:
            # 设置活动项
            self._active_item = item.id
            self._render_nav_items()

            # 回调
            if item.on_click:
                item.on_click()
            if self.on_select:
                self.on_select(item.id)

        # 保存状态
        self._save_state()

    def toggle(self):
        """切换展开/收起状态"""
        if self._animating:
            return

        self._expanded = not self._expanded
        self._animate_toggle()
        self._save_state()

    def _animate_toggle(self):
        """执行展开/收起动画"""
        self._animating = True

        start_width = self._current_width
        end_width = self.EXPANDED_WIDTH if self._expanded else self.COLLAPSED_WIDTH
        delta = end_width - start_width

        step_delay = self.ANIMATION_DURATION // self.ANIMATION_STEPS

        def ease_out(t):
            """ease-out缓动函数"""
            return 1 - (1 - t) ** 3

        def animate_step(step):
            if step > self.ANIMATION_STEPS:
                self._animating = False
                self._current_width = end_width
                self.configure(width=end_width)
                self._on_animation_complete()
                return

            progress = ease_out(step / self.ANIMATION_STEPS)
            new_width = int(start_width + delta * progress)
            self._current_width = new_width
            self.configure(width=new_width)

            self.after(step_delay, lambda: animate_step(step + 1))

        animate_step(1)

    def _on_animation_complete(self):
        """动画完成后更新UI"""
        # 更新logo
        self.logo_label.config(text="📱" if not self._expanded else "📱 WeChat")

        # 更新切换按钮
        self.toggle_btn.config(text="◀" if self._expanded else "▶")

        # 重新渲染导航项
        self._render_nav_items()

    def _load_state(self):
        """加载保存的状态"""
        if not self.persist_state:
            return

        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, encoding="utf-8") as f:
                    state = json.load(f)

                self._expanded = state.get("expanded", True)
                self._current_width = (
                    self.EXPANDED_WIDTH if self._expanded else self.COLLAPSED_WIDTH
                )
                self._active_item = state.get("active_item")
                self._expanded_submenus = set(state.get("expanded_submenus", []))

                logger.info(f"侧边栏状态已加载: expanded={self._expanded}")
        except Exception as e:
            logger.warning(f"加载侧边栏状态失败: {e}")

    def _save_state(self):
        """保存状态"""
        if not self.persist_state:
            return

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

            state = {
                "expanded": self._expanded,
                "active_item": self._active_item,
                "expanded_submenus": list(self._expanded_submenus),
                "timestamp": time.time(),
            }

            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            logger.warning(f"保存侧边栏状态失败: {e}")

    # ===== 公共API =====

    def expand(self):
        """展开侧边栏"""
        if not self._expanded:
            self.toggle()

    def collapse(self):
        """收起侧边栏"""
        if self._expanded:
            self.toggle()

    def set_active(self, item_id: str):
        """设置活动项"""
        self._active_item = item_id
        self._render_nav_items()
        self._save_state()

    def get_active(self) -> str | None:
        """获取当前活动项ID"""
        return self._active_item

    def set_badge(self, item_id: str, count: int):
        """设置徽章数量"""
        count = max(0, min(count, self.MAX_BADGE))

        for item in self.items:
            if item.id == item_id:
                item.badge = count
                break
            for child in item.children:
                if child.id == item_id:
                    child.badge = count
                    break

        self._render_nav_items()

    def update_items(self, items: list[NavItem]):
        """更新导航项"""
        self.items = items
        self._render_nav_items()

    def is_expanded(self) -> bool:
        """是否展开状态"""
        return self._expanded

    def destroy(self):
        """清理资源"""
        for tooltip in self._tooltips:
            tooltip.destroy()
        self._tooltips.clear()
        self._item_widgets.clear()
        super().destroy()


# 使用示例
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Sidebar 测试")
    root.geometry("1000x600")
    root.configure(bg="#121212")

    # 定义导航项
    nav_items = [
        NavItem(id="home", label="首页", icon="🏠"),
        NavItem(
            id="chat",
            label="聊天记录",
            icon="💬",
            badge=5,
            children=[
                NavItem(id="chat_recent", label="最近", icon="🕐"),
                NavItem(id="chat_starred", label="已标记", icon="⭐"),
                NavItem(id="chat_archived", label="已归档", icon="📦"),
            ],
        ),
        NavItem(id="summary", label="摘要", icon="📝", badge=2),
        NavItem(id="export", label="导出", icon="📤"),
        NavItem(id="settings", label="设置", icon="⚙️"),
    ]

    def on_select(item_id):
        print(f"选择了: {item_id}")

    # 主布局
    main_frame = tk.Frame(root, bg="#121212")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # 侧边栏
    sidebar = CollapsibleSidebar(
        main_frame, items=nav_items, on_select=on_select, persist_state=True
    )
    sidebar.pack(side=tk.LEFT, fill=tk.Y)

    # 内容区
    content = tk.Frame(main_frame, bg="#1e1e1e")
    content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    tk.Label(content, text="内容区域", bg="#1e1e1e", fg="#e5e5e5", font=("Segoe UI", 16)).pack(
        pady=50
    )

    root.mainloop()
