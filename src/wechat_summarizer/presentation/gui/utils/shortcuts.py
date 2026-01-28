"""
快捷键系统 (Keyboard Shortcuts)
符合2026年设计趋势的现代快捷键管理

功能特性:
- 全局快捷键注册
- 快捷键提示面板(Ctrl+?)
- 可自定义绑定
- 快捷键分组
- 冲突检测

安全措施:
- 快捷键数量限制
- 冲突防护
- 输入验证
- 回调异常捕获
"""

import tkinter as tk
from typing import Optional, Callable, Dict, List, Tuple
from dataclasses import dataclass, field
import json
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class Shortcut:
    """快捷键定义"""
    id: str
    name: str
    keys: str  # 如 "Ctrl+S", "Ctrl+Shift+N"
    callback: Optional[Callable[[], None]] = None
    group: str = "通用"
    description: str = ""
    enabled: bool = True


class KeyboardShortcutManager:
    """快捷键管理器"""
    
    # 安全限制
    MAX_SHORTCUTS = 100
    
    # 修饰键映射
    MODIFIER_MAP = {
        "Ctrl": "Control",
        "Alt": "Alt",
        "Shift": "Shift",
        "Meta": "Meta",
        "Cmd": "Meta"  # macOS
    }
    
    _instance: Optional["KeyboardShortcutManager"] = None
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self._shortcuts: Dict[str, Shortcut] = {}
        self._bindings: Dict[str, str] = {}  # key combo -> shortcut id
        self._enabled = True
        
        # 配置文件路径
        self._config_file = os.path.join(
            os.path.expanduser("~"),
            ".wechat_summarizer",
            "shortcuts.json"
        )
        
        # 加载自定义绑定
        self._load_custom_bindings()
        
        # 注册默认快捷键
        self._register_defaults()
        
        # 绑定帮助面板
        self.register(Shortcut(
            id="show_help",
            name="显示快捷键帮助",
            keys="Ctrl+?",
            callback=self.show_help_panel,
            group="帮助"
        ))
    
    @classmethod
    def get_instance(cls, root: Optional[tk.Tk] = None) -> "KeyboardShortcutManager":
        """获取单例实例"""
        if cls._instance is None:
            if root is None:
                raise ValueError("首次调用需要提供root参数")
            cls._instance = cls(root)
        return cls._instance
    
    def _register_defaults(self):
        """注册默认快捷键"""
        defaults = [
            Shortcut(
                id="save",
                name="保存",
                keys="Ctrl+S",
                group="文件",
                description="保存当前文件"
            ),
            Shortcut(
                id="open",
                name="打开",
                keys="Ctrl+O",
                group="文件",
                description="打开文件"
            ),
            Shortcut(
                id="new",
                name="新建",
                keys="Ctrl+N",
                group="文件",
                description="新建文件"
            ),
            Shortcut(
                id="undo",
                name="撤销",
                keys="Ctrl+Z",
                group="编辑",
                description="撤销上一步操作"
            ),
            Shortcut(
                id="redo",
                name="重做",
                keys="Ctrl+Y",
                group="编辑",
                description="重做上一步操作"
            ),
            Shortcut(
                id="copy",
                name="复制",
                keys="Ctrl+C",
                group="编辑",
                description="复制选中内容"
            ),
            Shortcut(
                id="paste",
                name="粘贴",
                keys="Ctrl+V",
                group="编辑",
                description="粘贴剪贴板内容"
            ),
            Shortcut(
                id="cut",
                name="剪切",
                keys="Ctrl+X",
                group="编辑",
                description="剪切选中内容"
            ),
            Shortcut(
                id="select_all",
                name="全选",
                keys="Ctrl+A",
                group="编辑",
                description="选中所有内容"
            ),
            Shortcut(
                id="find",
                name="查找",
                keys="Ctrl+F",
                group="编辑",
                description="打开查找对话框"
            ),
            Shortcut(
                id="zoom_in",
                name="放大",
                keys="Ctrl+=",
                group="视图",
                description="放大界面"
            ),
            Shortcut(
                id="zoom_out",
                name="缩小",
                keys="Ctrl+-",
                group="视图",
                description="缩小界面"
            ),
            Shortcut(
                id="zoom_reset",
                name="重置缩放",
                keys="Ctrl+0",
                group="视图",
                description="重置界面缩放"
            )
        ]
        
        for shortcut in defaults:
            if shortcut.id not in self._shortcuts:
                self.register(shortcut, bind=False)  # 默认不实际绑定
    
    def register(
        self,
        shortcut: Shortcut,
        bind: bool = True
    ) -> bool:
        """注册快捷键"""
        if len(self._shortcuts) >= self.MAX_SHORTCUTS:
            logger.warning("快捷键数量已达上限")
            return False
        
        # 检查冲突
        tk_key = self._parse_keys(shortcut.keys)
        if tk_key in self._bindings:
            existing_id = self._bindings[tk_key]
            if existing_id != shortcut.id:
                logger.warning(f"快捷键冲突: {shortcut.keys} 已被 {existing_id} 使用")
                return False
        
        self._shortcuts[shortcut.id] = shortcut
        self._bindings[tk_key] = shortcut.id
        
        if bind and shortcut.callback:
            self._bind_key(tk_key, shortcut)
        
        return True
    
    def unregister(self, shortcut_id: str):
        """注销快捷键"""
        if shortcut_id not in self._shortcuts:
            return
        
        shortcut = self._shortcuts[shortcut_id]
        tk_key = self._parse_keys(shortcut.keys)
        
        # 解绑
        try:
            self.root.unbind_all(f"<{tk_key}>")
        except tk.TclError:
            pass
        
        # 移除
        if tk_key in self._bindings:
            del self._bindings[tk_key]
        del self._shortcuts[shortcut_id]
    
    def bind_callback(self, shortcut_id: str, callback: Callable[[], None]):
        """为已注册的快捷键绑定回调"""
        if shortcut_id not in self._shortcuts:
            logger.warning(f"快捷键不存在: {shortcut_id}")
            return
        
        shortcut = self._shortcuts[shortcut_id]
        shortcut.callback = callback
        
        tk_key = self._parse_keys(shortcut.keys)
        self._bind_key(tk_key, shortcut)
    
    def _bind_key(self, tk_key: str, shortcut: Shortcut):
        """绑定Tk事件"""
        def handler(event):
            if not self._enabled or not shortcut.enabled:
                return
            
            if shortcut.callback:
                try:
                    shortcut.callback()
                except Exception as e:
                    logger.error(f"快捷键回调执行失败 ({shortcut.id}): {e}")
            
            return "break"  # 阻止事件传播
        
        try:
            self.root.bind_all(f"<{tk_key}>", handler)
        except tk.TclError as e:
            logger.error(f"绑定快捷键失败 ({shortcut.keys}): {e}")
    
    def _parse_keys(self, keys: str) -> str:
        """解析快捷键字符串为Tk格式"""
        parts = keys.split("+")
        tk_parts = []
        
        for part in parts:
            part = part.strip()
            
            if part in self.MODIFIER_MAP:
                tk_parts.append(self.MODIFIER_MAP[part])
            elif part == "?":
                tk_parts.append("question")
            elif part == "=":
                tk_parts.append("equal")
            elif part == "-":
                tk_parts.append("minus")
            elif len(part) == 1:
                tk_parts.append(part.lower())
            else:
                tk_parts.append(part)
        
        return "-".join(tk_parts)
    
    def rebind(self, shortcut_id: str, new_keys: str) -> bool:
        """重新绑定快捷键"""
        if shortcut_id not in self._shortcuts:
            return False
        
        shortcut = self._shortcuts[shortcut_id]
        old_tk_key = self._parse_keys(shortcut.keys)
        new_tk_key = self._parse_keys(new_keys)
        
        # 检查新键是否冲突
        if new_tk_key in self._bindings and self._bindings[new_tk_key] != shortcut_id:
            logger.warning(f"快捷键冲突: {new_keys}")
            return False
        
        # 解绑旧键
        try:
            self.root.unbind_all(f"<{old_tk_key}>")
        except tk.TclError:
            pass
        
        if old_tk_key in self._bindings:
            del self._bindings[old_tk_key]
        
        # 更新
        shortcut.keys = new_keys
        self._bindings[new_tk_key] = shortcut_id
        
        if shortcut.callback:
            self._bind_key(new_tk_key, shortcut)
        
        # 保存自定义绑定
        self._save_custom_bindings()
        
        return True
    
    def enable(self, shortcut_id: Optional[str] = None):
        """启用快捷键"""
        if shortcut_id:
            if shortcut_id in self._shortcuts:
                self._shortcuts[shortcut_id].enabled = True
        else:
            self._enabled = True
    
    def disable(self, shortcut_id: Optional[str] = None):
        """禁用快捷键"""
        if shortcut_id:
            if shortcut_id in self._shortcuts:
                self._shortcuts[shortcut_id].enabled = False
        else:
            self._enabled = False
    
    def get_shortcut(self, shortcut_id: str) -> Optional[Shortcut]:
        """获取快捷键"""
        return self._shortcuts.get(shortcut_id)
    
    def get_all_shortcuts(self) -> Dict[str, List[Shortcut]]:
        """获取所有快捷键（按组分类）"""
        grouped = {}
        for shortcut in self._shortcuts.values():
            if shortcut.group not in grouped:
                grouped[shortcut.group] = []
            grouped[shortcut.group].append(shortcut)
        return grouped
    
    def _load_custom_bindings(self):
        """加载自定义绑定"""
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, "r", encoding="utf-8") as f:
                    custom = json.load(f)
                
                for shortcut_id, keys in custom.items():
                    if shortcut_id in self._shortcuts:
                        self._shortcuts[shortcut_id].keys = keys
                        
        except Exception as e:
            logger.warning(f"加载快捷键配置失败: {e}")
    
    def _save_custom_bindings(self):
        """保存自定义绑定"""
        try:
            os.makedirs(os.path.dirname(self._config_file), exist_ok=True)
            
            custom = {
                s.id: s.keys
                for s in self._shortcuts.values()
            }
            
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(custom, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"保存快捷键配置失败: {e}")
    
    def show_help_panel(self):
        """显示快捷键帮助面板"""
        ShortcutHelpPanel(self.root, self)


class ShortcutHelpPanel(tk.Toplevel):
    """快捷键帮助面板"""
    
    def __init__(self, parent: tk.Tk, manager: KeyboardShortcutManager):
        super().__init__(parent)
        
        self.manager = manager
        
        # 窗口设置
        self.title("快捷键帮助")
        self.geometry("500x600")
        self.configure(bg="#1a1a1a")
        
        # 居中显示
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 600) // 2
        self.geometry(f"+{x}+{y}")
        
        # 样式
        self.colors = {
            "bg": "#1a1a1a",
            "card_bg": "#252525",
            "text": "#e5e5e5",
            "text_secondary": "#808080",
            "accent": "#3b82f6",
            "border": "#404040"
        }
        
        self._setup_ui()
        
        # ESC关闭
        self.bind("<Escape>", lambda e: self.destroy())
        
        # 获取焦点
        self.focus_set()
        self.grab_set()
    
    def _setup_ui(self):
        """构建UI"""
        # 标题栏
        header = tk.Frame(self, bg=self.colors["bg"], height=60)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        tk.Label(
            header,
            text="⌨️ 快捷键帮助",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=("Segoe UI", 16, "bold")
        ).pack(side=tk.LEFT)
        
        tk.Label(
            header,
            text="按 Esc 关闭",
            bg=self.colors["bg"],
            fg=self.colors["text_secondary"],
            font=("Segoe UI", 10)
        ).pack(side=tk.RIGHT)
        
        # 滚动区域
        canvas = tk.Canvas(
            self,
            bg=self.colors["bg"],
            highlightthickness=0
        )
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        
        content = tk.Frame(canvas, bg=self.colors["bg"])
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        
        canvas.create_window((0, 0), window=content, anchor=tk.NW)
        
        # 渲染快捷键分组
        grouped = self.manager.get_all_shortcuts()
        
        for group_name, shortcuts in grouped.items():
            self._render_group(content, group_name, shortcuts)
        
        # 更新滚动区域
        content.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # 鼠标滚轮
        def on_mousewheel(event):
            canvas.yview_scroll(-event.delta // 120, "units")
        
        canvas.bind("<MouseWheel>", on_mousewheel)
    
    def _render_group(self, parent: tk.Frame, group_name: str, shortcuts: List[Shortcut]):
        """渲染快捷键分组"""
        # 分组标题
        group_header = tk.Frame(parent, bg=self.colors["bg"])
        group_header.pack(fill=tk.X, pady=(15, 8))
        
        tk.Label(
            group_header,
            text=group_name,
            bg=self.colors["bg"],
            fg=self.colors["accent"],
            font=("Segoe UI", 12, "bold")
        ).pack(side=tk.LEFT)
        
        # 分隔线
        tk.Frame(
            group_header,
            bg=self.colors["border"],
            height=1
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 快捷键列表
        for shortcut in shortcuts:
            self._render_shortcut(parent, shortcut)
    
    def _render_shortcut(self, parent: tk.Frame, shortcut: Shortcut):
        """渲染单个快捷键"""
        row = tk.Frame(parent, bg=self.colors["card_bg"], padx=12, pady=8)
        row.pack(fill=tk.X, pady=2)
        
        # 名称
        tk.Label(
            row,
            text=shortcut.name,
            bg=self.colors["card_bg"],
            fg=self.colors["text"],
            font=("Segoe UI", 11),
            anchor="w"
        ).pack(side=tk.LEFT)
        
        # 快捷键
        key_frame = tk.Frame(row, bg=self.colors["card_bg"])
        key_frame.pack(side=tk.RIGHT)
        
        for i, part in enumerate(shortcut.keys.split("+")):
            if i > 0:
                tk.Label(
                    key_frame,
                    text="+",
                    bg=self.colors["card_bg"],
                    fg=self.colors["text_secondary"],
                    font=("Segoe UI", 10)
                ).pack(side=tk.LEFT, padx=2)
            
            key_label = tk.Label(
                key_frame,
                text=part.strip(),
                bg="#3a3a3a",
                fg=self.colors["text"],
                font=("Segoe UI", 10),
                padx=6,
                pady=2
            )
            key_label.pack(side=tk.LEFT)


# 使用示例
if __name__ == "__main__":
    root = tk.Tk()
    root.title("快捷键系统测试")
    root.geometry("600x400")
    root.configure(bg="#121212")
    
    # 初始化快捷键管理器
    manager = KeyboardShortcutManager(root)
    
    # 绑定回调
    manager.bind_callback("save", lambda: print("保存!"))
    manager.bind_callback("open", lambda: print("打开!"))
    manager.bind_callback("find", lambda: print("查找!"))
    
    # 注册自定义快捷键
    manager.register(Shortcut(
        id="custom_action",
        name="自定义操作",
        keys="Ctrl+Shift+X",
        callback=lambda: print("自定义操作触发!"),
        group="自定义",
        description="这是一个自定义快捷键"
    ))
    
    # 标签
    tk.Label(
        root,
        text="按 Ctrl+? 查看快捷键帮助\n\n"
             "试试:\n"
             "Ctrl+S - 保存\n"
             "Ctrl+O - 打开\n"
             "Ctrl+F - 查找\n"
             "Ctrl+Shift+X - 自定义",
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 14),
        justify="center"
    ).pack(expand=True)
    
    root.mainloop()
