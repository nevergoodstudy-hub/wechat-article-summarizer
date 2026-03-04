"""
表单自动保存系统 (Auto Save)
符合2026年设计趋势的现代自动保存管理

功能特性:
- 输入防抖(可配置延迟)
- 本地草稿存储
- 恢复提示对话框
- 多表单支持
- 版本历史

安全措施:
- 敏感数据加密存储
- 存储大小限制
- 自动过期清理
- 路径安全验证
"""

import base64
import hashlib
import json
import logging
import os
import threading
import time
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from tkinter import ttk
from typing import Any, cast

logger = logging.getLogger(__name__)


# 安全限制常量
MAX_DRAFT_SIZE = 100 * 1024  # 单个草稿最大 100KB
MAX_TOTAL_SIZE = 5 * 1024 * 1024  # 总存储最大 5MB
MAX_DRAFTS_PER_FORM = 10  # 每个表单最大草稿数
DRAFT_EXPIRE_DAYS = 7  # 草稿过期天数
DEFAULT_DEBOUNCE_MS = 300  # 默认防抖延迟


@dataclass
class Draft:
    """草稿数据"""

    form_id: str
    data: dict[str, Any]
    timestamp: float
    version: int = 1
    encrypted: bool = False


@dataclass
class FormField:
    """表单字段定义"""

    name: str
    widget: tk.Widget
    get_value: Callable[[], Any] | None = None
    set_value: Callable[[Any], None] | None = None
    sensitive: bool = False  # 是否敏感数据


class SimpleEncryptor:
    """简单加密器 (用于本地草稿保护)

    注意: 这不是强加密，仅用于防止明文存储敏感数据
    生产环境应使用更强的加密方案
    """

    def __init__(self, key: str | None = None):
        # 使用机器特征生成默认密钥
        if key is None:
            import platform

            machine_id = f"{platform.node()}-{os.getlogin()}"
            key = hashlib.sha256(machine_id.encode()).hexdigest()[:32]
        self._key = key.encode()

    def encrypt(self, data: str) -> str:
        """加密数据"""
        try:
            # 简单XOR加密 + Base64编码
            encrypted = bytes(
                a ^ b
                for a, b in zip(
                    data.encode("utf-8"),
                    (self._key * (len(data) // len(self._key) + 1))[: len(data.encode("utf-8"))],
                    strict=False,
                )
            )
            return base64.b64encode(encrypted).decode("ascii")
        except Exception as e:
            logger.error(f"加密失败: {e}")
            return data

    def decrypt(self, data: str) -> str:
        """解密数据"""
        try:
            encrypted = base64.b64decode(data.encode("ascii"))
            decrypted = bytes(
                a ^ b
                for a, b in zip(
                    encrypted,
                    (self._key * (len(encrypted) // len(self._key) + 1))[: len(encrypted)],
                    strict=False,
                )
            )
            return decrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"解密失败: {e}")
            return data


class DraftStorage:
    """草稿存储管理"""

    def __init__(self, storage_dir: str | None = None):
        if storage_dir is None:
            storage_dir = os.path.join(os.path.expanduser("~"), ".wechat_summarizer", "drafts")

        self._storage_dir = storage_dir
        self._encryptor = SimpleEncryptor()

        # 确保目录存在
        self._ensure_dir()

        # 启动时清理过期草稿
        self._cleanup_expired()

    def _ensure_dir(self):
        """确保存储目录存在"""
        try:
            os.makedirs(self._storage_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"创建草稿目录失败: {e}")

    def _get_file_path(self, form_id: str) -> str:
        """获取草稿文件路径"""
        # 安全: 使用哈希避免路径遍历 (MD5仅用于文件名生成，非安全用途)
        safe_id = hashlib.md5(form_id.encode(), usedforsecurity=False).hexdigest()
        return os.path.join(self._storage_dir, f"draft_{safe_id}.json")

    def save(self, draft: Draft) -> bool:
        """保存草稿"""
        try:
            file_path = self._get_file_path(draft.form_id)

            # 加载现有草稿
            drafts = self._load_drafts(draft.form_id)

            # 处理敏感数据
            data = draft.data.copy()
            if draft.encrypted:
                for key, value in data.items():
                    if isinstance(value, str):
                        data[key] = self._encryptor.encrypt(value)

            # 添加新草稿
            draft_dict = {
                "form_id": draft.form_id,
                "data": data,
                "timestamp": draft.timestamp,
                "version": draft.version,
                "encrypted": draft.encrypted,
            }

            drafts.append(draft_dict)

            # 限制草稿数量
            if len(drafts) > MAX_DRAFTS_PER_FORM:
                drafts = drafts[-MAX_DRAFTS_PER_FORM:]

            # 检查大小限制
            content = json.dumps(drafts, ensure_ascii=False)
            if len(content) > MAX_DRAFT_SIZE:
                logger.warning("草稿大小超限，仅保留最新版本")
                drafts = [draft_dict]

            # 保存
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(drafts, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            logger.error(f"保存草稿失败: {e}")
            return False

    def _load_drafts(self, form_id: str) -> list[dict[str, Any]]:
        """加载表单的所有草稿"""
        try:
            file_path = self._get_file_path(form_id)
            if os.path.exists(file_path):
                with open(file_path, encoding="utf-8") as f:
                    payload = json.load(f)
                    if isinstance(payload, list):
                        return cast(list[dict[str, Any]], payload)
        except Exception as e:
            logger.warning(f"加载草稿失败: {e}")
        return []

    def load_latest(self, form_id: str) -> Draft | None:
        """加载最新草稿"""
        drafts = self._load_drafts(form_id)
        if not drafts:
            return None

        latest = drafts[-1]

        # 解密敏感数据
        data = latest["data"].copy()
        if latest.get("encrypted"):
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = self._encryptor.decrypt(value)

        return Draft(
            form_id=latest["form_id"],
            data=data,
            timestamp=latest["timestamp"],
            version=latest.get("version", 1),
            encrypted=latest.get("encrypted", False),
        )

    def load_history(self, form_id: str) -> list[Draft]:
        """加载草稿历史"""
        drafts_data = self._load_drafts(form_id)
        drafts = []

        for d in drafts_data:
            data = d["data"].copy()
            if d.get("encrypted"):
                for key, value in data.items():
                    if isinstance(value, str):
                        data[key] = self._encryptor.decrypt(value)

            drafts.append(
                Draft(
                    form_id=d["form_id"],
                    data=data,
                    timestamp=d["timestamp"],
                    version=d.get("version", 1),
                    encrypted=d.get("encrypted", False),
                )
            )

        return drafts

    def delete(self, form_id: str) -> bool:
        """删除表单草稿"""
        try:
            file_path = self._get_file_path(form_id)
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"删除草稿失败: {e}")
            return False

    def _cleanup_expired(self):
        """清理过期草稿"""
        try:
            expire_time = time.time() - (DRAFT_EXPIRE_DAYS * 24 * 3600)

            for filename in os.listdir(self._storage_dir):
                if not filename.startswith("draft_"):
                    continue

                file_path = os.path.join(self._storage_dir, filename)

                try:
                    with open(file_path, encoding="utf-8") as f:
                        drafts = json.load(f)

                    # 过滤过期草稿
                    valid_drafts = [d for d in drafts if d.get("timestamp", 0) > expire_time]

                    if not valid_drafts:
                        os.remove(file_path)
                    elif len(valid_drafts) < len(drafts):
                        with open(file_path, "w", encoding="utf-8") as f:
                            json.dump(valid_drafts, f, ensure_ascii=False)

                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"清理过期草稿失败: {e}")


class AutoSaveManager:
    """表单自动保存管理器"""

    _instance: AutoSaveManager | None = None

    def __init__(self) -> None:
        self._storage: DraftStorage = DraftStorage()
        self._forms: dict[str, dict[str, FormField]] = {}
        self._debounce_timers: dict[str, threading.Timer] = {}
        self._debounce_delays: dict[str, int] = {}
        self._callbacks: dict[str, Callable[[Draft], None]] = {}
        self._enabled = True

    @classmethod
    def get_instance(cls) -> AutoSaveManager:
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_form(
        self,
        form_id: str,
        fields: list[FormField],
        debounce_ms: int = DEFAULT_DEBOUNCE_MS,
        on_restore: Callable[[Draft], None] | None = None,
    ):
        """注册表单"""
        self._forms[form_id] = {f.name: f for f in fields}
        self._debounce_delays[form_id] = debounce_ms

        if on_restore:
            self._callbacks[form_id] = on_restore

        # 为每个字段绑定变化监听
        for field in fields:
            self._bind_field_change(form_id, field)

    def _bind_field_change(self, form_id: str, field: FormField):
        """绑定字段变化监听"""
        widget = field.widget

        # 根据组件类型绑定事件
        if isinstance(widget, (tk.Entry, ttk.Entry, tk.Text)):
            widget.bind("<KeyRelease>", lambda e: self._on_field_change(form_id))
        elif isinstance(widget, (ttk.Combobox,)):
            widget.bind("<<ComboboxSelected>>", lambda e: self._on_field_change(form_id))
        elif isinstance(widget, (tk.Checkbutton, ttk.Checkbutton)):
            # 需要绑定到variable
            pass

    def _on_field_change(self, form_id: str):
        """字段变化回调"""
        if not self._enabled:
            return

        # 取消之前的定时器
        if form_id in self._debounce_timers:
            self._debounce_timers[form_id].cancel()

        # 设置新的防抖定时器
        delay = self._debounce_delays.get(form_id, DEFAULT_DEBOUNCE_MS)
        timer = threading.Timer(delay / 1000.0, lambda: self._save_form(form_id))
        timer.start()
        self._debounce_timers[form_id] = timer

    def _save_form(self, form_id: str):
        """保存表单"""
        if form_id not in self._forms:
            return

        fields = self._forms[form_id]
        data = {}
        has_sensitive = False

        for name, field in fields.items():
            try:
                if field.get_value:
                    value = field.get_value()
                else:
                    value = self._get_widget_value(field.widget)

                data[name] = value

                if field.sensitive:
                    has_sensitive = True

            except Exception as e:
                logger.warning(f"获取字段值失败 ({name}): {e}")

        # 创建草稿
        draft = Draft(
            form_id=form_id, data=data, timestamp=time.time(), version=1, encrypted=has_sensitive
        )

        # 保存
        self._storage.save(draft)
        logger.debug(f"自动保存表单: {form_id}")

    def _get_widget_value(self, widget: tk.Widget) -> Any:
        """获取组件值"""
        if isinstance(widget, (tk.Entry, ttk.Entry)):
            return widget.get()
        elif isinstance(widget, tk.Text):
            return widget.get("1.0", tk.END).strip()
        elif isinstance(widget, ttk.Combobox) or hasattr(widget, "get"):
            return widget.get()
        return None

    def _set_widget_value(self, widget: tk.Widget, value: Any):
        """设置组件值"""
        if isinstance(widget, (tk.Entry, ttk.Entry)):
            widget.delete(0, tk.END)
            widget.insert(0, str(value) if value else "")
        elif isinstance(widget, tk.Text):
            widget.delete("1.0", tk.END)
            widget.insert("1.0", str(value) if value else "")
        elif isinstance(widget, ttk.Combobox):
            widget.set(str(value) if value else "")

    def save_now(self, form_id: str):
        """立即保存"""
        # 取消防抖定时器
        if form_id in self._debounce_timers:
            self._debounce_timers[form_id].cancel()

        self._save_form(form_id)

    def has_draft(self, form_id: str) -> bool:
        """检查是否有草稿"""
        draft = self._storage.load_latest(form_id)
        return draft is not None

    def get_draft(self, form_id: str) -> Draft | None:
        """获取最新草稿"""
        return self._storage.load_latest(form_id)

    def get_history(self, form_id: str) -> list[Draft]:
        """获取草稿历史"""
        return self._storage.load_history(form_id)

    def restore(self, form_id: str, draft: Draft | None = None) -> bool:
        """恢复草稿"""
        if draft is None:
            draft = self._storage.load_latest(form_id)

        if draft is None:
            return False

        if form_id not in self._forms:
            return False

        fields = self._forms[form_id]

        # 恢复字段值
        for name, value in draft.data.items():
            if name in fields:
                field = fields[name]
                try:
                    if field.set_value:
                        field.set_value(value)
                    else:
                        self._set_widget_value(field.widget, value)
                except Exception as e:
                    logger.warning(f"恢复字段值失败 ({name}): {e}")

        # 触发回调
        if form_id in self._callbacks:
            try:
                self._callbacks[form_id](draft)
            except Exception as e:
                logger.error(f"恢复回调执行失败: {e}")

        return True

    def clear_draft(self, form_id: str):
        """清除草稿"""
        self._storage.delete(form_id)

    def enable(self):
        """启用自动保存"""
        self._enabled = True

    def disable(self):
        """禁用自动保存"""
        self._enabled = False

        # 取消所有定时器
        for timer in self._debounce_timers.values():
            timer.cancel()
        self._debounce_timers.clear()

    def unregister_form(self, form_id: str):
        """注销表单"""
        if form_id in self._forms:
            del self._forms[form_id]

        if form_id in self._debounce_timers:
            self._debounce_timers[form_id].cancel()
            del self._debounce_timers[form_id]

        if form_id in self._debounce_delays:
            del self._debounce_delays[form_id]

        if form_id in self._callbacks:
            del self._callbacks[form_id]


class RestoreDialog(tk.Toplevel):
    """草稿恢复对话框"""

    def __init__(
        self,
        parent: tk.Tk,
        draft: Draft,
        on_restore: Callable[[], None],
        on_discard: Callable[[], None],
    ):
        super().__init__(parent)

        self.draft = draft
        self.on_restore = on_restore
        self.on_discard = on_discard

        self.result = False

        # 窗口设置
        self.title("恢复草稿")
        self.geometry("400x200")
        self.configure(bg="#1a1a1a")
        self.resizable(False, False)

        # 居中
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 400) // 2
        y = (self.winfo_screenheight() - 200) // 2
        self.geometry(f"+{x}+{y}")

        self._setup_ui()

        # 模态
        self.transient(parent)
        self.grab_set()
        self.focus_set()

    def _setup_ui(self):
        """构建UI"""
        # 图标和消息
        msg_frame = tk.Frame(self, bg="#1a1a1a", padx=20, pady=20)
        msg_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(msg_frame, text="📝", bg="#1a1a1a", fg="#e5e5e5", font=("Segoe UI", 32)).pack()

        # 时间格式化
        draft_time = datetime.fromtimestamp(self.draft.timestamp)
        time_str = draft_time.strftime("%Y-%m-%d %H:%M:%S")

        tk.Label(
            msg_frame,
            text=f"发现未保存的草稿\n保存于: {time_str}",
            bg="#1a1a1a",
            fg="#e5e5e5",
            font=("Segoe UI", 12),
            justify="center",
        ).pack(pady=10)

        # 按钮
        btn_frame = tk.Frame(self, bg="#1a1a1a", pady=15)
        btn_frame.pack(fill=tk.X)

        restore_btn = tk.Button(
            btn_frame,
            text="恢复草稿",
            bg="#3b82f6",
            fg="#ffffff",
            font=("Segoe UI", 11),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._on_restore,
        )
        restore_btn.pack(side=tk.LEFT, padx=(60, 10))

        discard_btn = tk.Button(
            btn_frame,
            text="放弃",
            bg="#404040",
            fg="#e5e5e5",
            font=("Segoe UI", 11),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._on_discard,
        )
        discard_btn.pack(side=tk.LEFT, padx=10)

    def _on_restore(self):
        """恢复按钮"""
        self.result = True
        try:
            self.on_restore()
        except Exception as e:
            logger.error(f"恢复回调失败: {e}")
        self.destroy()

    def _on_discard(self):
        """放弃按钮"""
        self.result = False
        try:
            self.on_discard()
        except Exception as e:
            logger.error(f"放弃回调失败: {e}")
        self.destroy()


def check_and_restore(root: tk.Tk, form_id: str, manager: AutoSaveManager | None = None) -> bool:
    """检查并提示恢复草稿

    Args:
        root: Tk根窗口
        form_id: 表单ID
        manager: 自动保存管理器

    Returns:
        是否恢复了草稿
    """
    if manager is None:
        manager = AutoSaveManager.get_instance()

    draft = manager.get_draft(form_id)
    if draft is None:
        return False

    restored = [False]

    def on_restore():
        manager.restore(form_id, draft)
        restored[0] = True

    def on_discard():
        manager.clear_draft(form_id)
        restored[0] = False

    dialog = RestoreDialog(root, draft, on_restore, on_discard)
    root.wait_window(dialog)

    return restored[0]


# 使用示例
if __name__ == "__main__":
    root = tk.Tk()
    root.title("自动保存测试")
    root.geometry("500x400")
    root.configure(bg="#121212")

    # 创建表单
    form_frame = tk.Frame(root, bg="#121212", padx=30, pady=30)
    form_frame.pack(fill=tk.BOTH, expand=True)

    # 标题输入
    tk.Label(form_frame, text="标题:", bg="#121212", fg="#e5e5e5", font=("Segoe UI", 12)).pack(
        anchor="w", pady=(0, 5)
    )

    title_entry = tk.Entry(
        form_frame,
        bg="#252525",
        fg="#e5e5e5",
        font=("Segoe UI", 12),
        relief="flat",
        insertbackground="#e5e5e5",
    )
    title_entry.pack(fill=tk.X, pady=(0, 15))

    # 内容输入
    tk.Label(form_frame, text="内容:", bg="#121212", fg="#e5e5e5", font=("Segoe UI", 12)).pack(
        anchor="w", pady=(0, 5)
    )

    content_text = tk.Text(
        form_frame,
        bg="#252525",
        fg="#e5e5e5",
        font=("Segoe UI", 12),
        relief="flat",
        insertbackground="#e5e5e5",
        height=8,
    )
    content_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

    # 注册表单
    manager = AutoSaveManager.get_instance()
    manager.register_form(
        form_id="test_form",
        fields=[
            FormField(name="title", widget=title_entry),
            FormField(name="content", widget=content_text),
        ],
        debounce_ms=500,
    )

    # 状态标签
    status_label = tk.Label(
        form_frame, text="输入内容后自动保存...", bg="#121212", fg="#808080", font=("Segoe UI", 10)
    )
    status_label.pack(anchor="w")

    # 检查并恢复草稿
    root.after(100, lambda: check_and_restore(root, "test_form", manager))

    root.mainloop()
