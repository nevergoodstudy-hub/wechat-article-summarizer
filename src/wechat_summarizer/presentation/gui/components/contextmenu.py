"""
上下文菜单组件 (Context Menu)
符合2026年设计趋势的现代右键菜单

功能特性:
- 右键菜单支持
- 智能位置调整(避免超出屏幕)
- 键盘导航(上/下/Enter/Escape)
- 子菜单支持
- 分隔线和禁用项
- 快捷键显示

安全措施:
- 菜单项数量限制
- 输入清洗
- 回调异常捕获
- 自动关闭机制
"""

import tkinter as tk
from typing import Optional, Callable, List, Dict, Any, Literal
from dataclasses import dataclass, field
import html
import logging

logger = logging.getLogger(__name__)


@dataclass
class MenuItem:
    """菜单项定义"""
    id: str
    label: str
    icon: str = ""
    shortcut: str = ""
    disabled: bool = False
    separator: bool = False
    children: List["MenuItem"] = field(default_factory=list)
    on_click: Optional[Callable[[], None]] = None


class ContextMenu:
    """上下文菜单"""
    
    # 安全限制
    MAX_ITEMS = 50
    MAX_LABEL_LENGTH = 100
    
    def __init__(
        self,
        parent: tk.Widget,
        items: List[MenuItem],
        min_width: int = 180,
        **kwargs
    ):
        self.parent = parent
        self.items = items[:self.MAX_ITEMS]
        self.min_width = min_width
        
        self._window: Optional[tk.Toplevel] = None
        self._item_frames: List[Dict[str, Any]] = []
        self._selected_index = -1
        self._is_open = False
        self._submenu: Optional["ContextMenu"] = None
        
        # 样式
        self.colors = {
            "bg": "#252525",
            "item_bg": "#252525",
            "item_hover": "#3a3a3a",
            "item_active": "#3b82f6",
            "text": "#e5e5e5",
            "text_disabled": "#666666",
            "shortcut": "#808080",
            "separator": "#404040",
            "border": "#404040"
        }
    
    def show(self, x: int, y: int):
        """在指定位置显示菜单"""
        if self._is_open:
            self.close()
        
        self._is_open = True
        
        # 创建顶层窗口
        self._window = tk.Toplevel(self.parent)
        self._window.wm_overrideredirect(True)
        self._window.configure(bg=self.colors["border"])
        
        # 主容器
        container = tk.Frame(
            self._window,
            bg=self.colors["bg"],
            padx=1,
            pady=1
        )
        container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # 渲染菜单项
        self._render_items(container)
        
        # 更新窗口以获取实际大小
        self._window.update_idletasks()
        
        # 智能位置调整
        x, y = self._adjust_position(x, y)
        self._window.geometry(f"+{x}+{y}")
        
        # 绑定事件
        self._window.bind("<Escape>", lambda e: self.close())
        self._window.bind("<Up>", self._on_key_up)
        self._window.bind("<Down>", self._on_key_down)
        self._window.bind("<Return>", self._on_key_enter)
        self._window.bind("<FocusOut>", self._on_focus_out)
        
        # 全局点击关闭
        self.parent.bind("<Button-1>", self._on_global_click, add="+")
        
        # 获取焦点
        self._window.focus_set()
    
    def _render_items(self, container: tk.Frame):
        """渲染菜单项"""
        self._item_frames.clear()
        
        for idx, item in enumerate(self.items):
            if item.separator:
                # 分隔线
                sep = tk.Frame(
                    container,
                    bg=self.colors["separator"],
                    height=1
                )
                sep.pack(fill=tk.X, padx=8, pady=4)
                continue
            
            # 菜单项框架
            frame = tk.Frame(
                container,
                bg=self.colors["item_bg"],
                padx=10,
                pady=6,
                cursor="hand2" if not item.disabled else ""
            )
            frame.pack(fill=tk.X)
            
            # 图标
            if item.icon:
                icon_label = tk.Label(
                    frame,
                    text=item.icon,
                    bg=frame.cget("bg"),
                    fg=self.colors["text"] if not item.disabled else self.colors["text_disabled"],
                    font=("Segoe UI", 12),
                    width=2
                )
                icon_label.pack(side=tk.LEFT, padx=(0, 8))
            
            # 标签
            label_text = html.escape(item.label[:self.MAX_LABEL_LENGTH])
            label = tk.Label(
                frame,
                text=label_text,
                bg=frame.cget("bg"),
                fg=self.colors["text"] if not item.disabled else self.colors["text_disabled"],
                font=("Segoe UI", 11),
                anchor="w"
            )
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # 子菜单箭头或快捷键
            if item.children:
                arrow = tk.Label(
                    frame,
                    text="▶",
                    bg=frame.cget("bg"),
                    fg=self.colors["shortcut"],
                    font=("Segoe UI", 8)
                )
                arrow.pack(side=tk.RIGHT, padx=(10, 0))
            elif item.shortcut:
                shortcut_label = tk.Label(
                    frame,
                    text=item.shortcut,
                    bg=frame.cget("bg"),
                    fg=self.colors["shortcut"],
                    font=("Segoe UI", 10)
                )
                shortcut_label.pack(side=tk.RIGHT, padx=(10, 0))
            
            # 保存引用
            self._item_frames.append({
                "frame": frame,
                "item": item,
                "index": idx
            })
            
            # 事件绑定
            if not item.disabled:
                self._bind_item_events(frame, item, idx)
    
    def _bind_item_events(self, frame: tk.Frame, item: MenuItem, idx: int):
        """绑定菜单项事件"""
        def on_enter(e):
            self._highlight_item(idx)
            
            # 如果有子菜单，显示它
            if item.children:
                self._show_submenu(frame, item)
        
        def on_leave(e):
            if not item.children:
                self._unhighlight_item(idx)
        
        def on_click(e):
            if item.children:
                return
            
            self._execute_item(item)
        
        for widget in [frame] + frame.winfo_children():
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)
    
    def _highlight_item(self, idx: int):
        """高亮菜单项"""
        # 取消之前的高亮
        if self._selected_index >= 0:
            self._unhighlight_item(self._selected_index)
        
        self._selected_index = idx
        
        for item_data in self._item_frames:
            if item_data["index"] == idx:
                frame = item_data["frame"]
                frame.configure(bg=self.colors["item_hover"])
                for child in frame.winfo_children():
                    try:
                        child.configure(bg=self.colors["item_hover"])
                    except tk.TclError:
                        pass
                break
    
    def _unhighlight_item(self, idx: int):
        """取消高亮"""
        for item_data in self._item_frames:
            if item_data["index"] == idx:
                frame = item_data["frame"]
                frame.configure(bg=self.colors["item_bg"])
                for child in frame.winfo_children():
                    try:
                        child.configure(bg=self.colors["item_bg"])
                    except tk.TclError:
                        pass
                break
    
    def _execute_item(self, item: MenuItem):
        """执行菜单项"""
        self.close()
        
        if item.on_click:
            try:
                item.on_click()
            except Exception as e:
                logger.error(f"菜单项执行失败: {e}")
    
    def _show_submenu(self, parent_frame: tk.Frame, item: MenuItem):
        """显示子菜单"""
        if self._submenu:
            self._submenu.close()
        
        if not item.children:
            return
        
        # 计算子菜单位置
        frame_x = parent_frame.winfo_rootx() + parent_frame.winfo_width()
        frame_y = parent_frame.winfo_rooty()
        
        self._submenu = ContextMenu(
            self.parent,
            item.children,
            min_width=self.min_width
        )
        self._submenu.colors = self.colors
        self._submenu.show(frame_x, frame_y)
    
    def _adjust_position(self, x: int, y: int) -> tuple:
        """调整位置避免超出屏幕"""
        screen_width = self._window.winfo_screenwidth()
        screen_height = self._window.winfo_screenheight()
        
        menu_width = self._window.winfo_reqwidth()
        menu_height = self._window.winfo_reqheight()
        
        # 右边超出
        if x + menu_width > screen_width:
            x = screen_width - menu_width - 10
        
        # 下边超出
        if y + menu_height > screen_height:
            y = screen_height - menu_height - 10
        
        # 确保不小于0
        x = max(0, x)
        y = max(0, y)
        
        return x, y
    
    def _on_key_up(self, event):
        """向上导航"""
        if not self._item_frames:
            return
        
        # 找下一个非禁用项
        new_idx = self._selected_index - 1
        while new_idx >= 0:
            for item_data in self._item_frames:
                if item_data["index"] == new_idx and not item_data["item"].disabled:
                    self._highlight_item(new_idx)
                    return
            new_idx -= 1
    
    def _on_key_down(self, event):
        """向下导航"""
        if not self._item_frames:
            return
        
        new_idx = self._selected_index + 1
        max_idx = max(d["index"] for d in self._item_frames)
        
        while new_idx <= max_idx:
            for item_data in self._item_frames:
                if item_data["index"] == new_idx and not item_data["item"].disabled:
                    self._highlight_item(new_idx)
                    return
            new_idx += 1
    
    def _on_key_enter(self, event):
        """回车确认"""
        if self._selected_index < 0:
            return
        
        for item_data in self._item_frames:
            if item_data["index"] == self._selected_index:
                item = item_data["item"]
                if item.children:
                    self._show_submenu(item_data["frame"], item)
                else:
                    self._execute_item(item)
                break
    
    def _on_focus_out(self, event):
        """失去焦点"""
        # 延迟关闭，允许子菜单获取焦点
        self.parent.after(100, self._check_close)
    
    def _check_close(self):
        """检查是否需要关闭"""
        if self._window and self._window.winfo_exists():
            try:
                focus = self._window.focus_get()
                if focus is None or focus.winfo_toplevel() != self._window:
                    if not (self._submenu and self._submenu._is_open):
                        self.close()
            except tk.TclError:
                self.close()
    
    def _on_global_click(self, event):
        """全局点击"""
        if self._window and self._window.winfo_exists():
            # 检查点击是否在菜单内
            try:
                click_x = event.x_root
                click_y = event.y_root
                
                menu_x = self._window.winfo_x()
                menu_y = self._window.winfo_y()
                menu_w = self._window.winfo_width()
                menu_h = self._window.winfo_height()
                
                if not (menu_x <= click_x <= menu_x + menu_w and
                        menu_y <= click_y <= menu_y + menu_h):
                    self.close()
            except tk.TclError:
                self.close()
    
    def close(self):
        """关闭菜单"""
        if self._submenu:
            self._submenu.close()
            self._submenu = None
        
        if self._window:
            try:
                self._window.destroy()
            except tk.TclError:
                pass
            self._window = None
        
        self._is_open = False
        self._selected_index = -1
        self._item_frames.clear()
        
        # 解绑全局点击
        try:
            self.parent.unbind("<Button-1>")
        except tk.TclError:
            pass
    
    def is_open(self) -> bool:
        """是否打开状态"""
        return self._is_open


class ContextMenuManager:
    """上下文菜单管理器"""
    
    _menus: Dict[int, ContextMenu] = {}
    
    @classmethod
    def bind(
        cls,
        widget: tk.Widget,
        items: List[MenuItem],
        button: Literal[1, 2, 3] = 3
    ) -> ContextMenu:
        """
        为widget绑定上下文菜单
        button: 1=左键, 2=中键, 3=右键
        """
        menu = ContextMenu(widget, items)
        
        def show_menu(event):
            menu.show(event.x_root, event.y_root)
        
        widget.bind(f"<Button-{button}>", show_menu)
        
        cls._menus[id(widget)] = menu
        return menu
    
    @classmethod
    def unbind(cls, widget: tk.Widget):
        """解绑上下文菜单"""
        widget_id = id(widget)
        if widget_id in cls._menus:
            cls._menus[widget_id].close()
            del cls._menus[widget_id]
        
        try:
            widget.unbind("<Button-3>")
        except tk.TclError:
            pass
    
    @classmethod
    def close_all(cls):
        """关闭所有菜单"""
        for menu in cls._menus.values():
            menu.close()


# 使用示例
if __name__ == "__main__":
    root = tk.Tk()
    root.title("上下文菜单测试")
    root.geometry("600x400")
    root.configure(bg="#121212")
    
    # 定义菜单项
    menu_items = [
        MenuItem(
            id="cut",
            label="剪切",
            icon="✂️",
            shortcut="Ctrl+X",
            on_click=lambda: print("剪切")
        ),
        MenuItem(
            id="copy",
            label="复制",
            icon="📋",
            shortcut="Ctrl+C",
            on_click=lambda: print("复制")
        ),
        MenuItem(
            id="paste",
            label="粘贴",
            icon="📄",
            shortcut="Ctrl+V",
            on_click=lambda: print("粘贴")
        ),
        MenuItem(id="sep1", label="", separator=True),
        MenuItem(
            id="select_all",
            label="全选",
            shortcut="Ctrl+A",
            on_click=lambda: print("全选")
        ),
        MenuItem(id="sep2", label="", separator=True),
        MenuItem(
            id="more",
            label="更多选项",
            icon="⚙️",
            children=[
                MenuItem(
                    id="settings",
                    label="设置",
                    icon="⚙️",
                    on_click=lambda: print("设置")
                ),
                MenuItem(
                    id="help",
                    label="帮助",
                    icon="❓",
                    on_click=lambda: print("帮助")
                )
            ]
        ),
        MenuItem(
            id="disabled",
            label="禁用项",
            disabled=True
        )
    ]
    
    # 标签
    label = tk.Label(
        root,
        text="右键点击此处查看上下文菜单",
        bg="#2a2a2a",
        fg="#e5e5e5",
        font=("Segoe UI", 14),
        padx=40,
        pady=80
    )
    label.pack(expand=True)
    
    # 绑定上下文菜单
    ContextMenuManager.bind(label, menu_items)
    
    root.mainloop()
