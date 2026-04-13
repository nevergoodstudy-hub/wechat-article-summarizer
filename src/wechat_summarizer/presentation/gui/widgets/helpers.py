"""GUI辅助类

从 app.py 提取的辅助组件：
- GUILogHandler: 日志面板处理器
- UserPreferences: 用户偏好设置管理
- SummarizerInfo / ExporterInfo: 服务信息数据类
- get_available_memory_gb: 内存检测工具
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from loguru import logger

from ....shared.constants import CONFIG_DIR_NAME
from ....shared.utils.security import decrypt_credential, encrypt_credential, is_encrypted

# ==================== 内存检测 ====================

try:
    import psutil

    _psutil_available = True
except ImportError:
    _psutil_available = False


def get_available_memory_gb() -> float | None:
    """获取可用内存(GB)，如果无法检测则返回 None"""
    if not _psutil_available:
        return None
    try:
        mem = psutil.virtual_memory()
        return float(cast(float, mem.available) / (1024**3))
    except Exception:
        return None


LOW_MEMORY_THRESHOLD_GB = 4.0  # 低内存阈值：4GB


# ==================== 颜色工具 ====================


def adjust_color_brightness(hex_color: str, factor: float) -> str:
    """调整颜色亮度

    Args:
        hex_color: 十六进制颜色 (#RRGGBB)
        factor: 亮度因子 (>1 变亮, <1 变暗)
    """
    try:
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color


# ==================== 日志处理器 ====================


class GUILogHandler:
    """自定义日志Handler"""

    DEFAULT_MAX_LINES = 1000
    LOW_MEMORY_MAX_LINES = 200

    def __init__(self, text_widget, root, low_memory_mode: bool = False):
        self.text_widget = text_widget
        self.root = root
        self._max_lines = self.LOW_MEMORY_MAX_LINES if low_memory_mode else self.DEFAULT_MAX_LINES

    def set_low_memory_mode(self, enabled: bool):
        """设置低内存模式"""
        self._max_lines = self.LOW_MEMORY_MAX_LINES if enabled else self.DEFAULT_MAX_LINES

    def write(self, message: str):
        if not message.strip():
            return None
        else:
            self.root.after(0, self._append_log, message)

    # 日志级别 -> 标签映射
    _LEVEL_TAGS = {
        "ERROR": "ERROR",
        "WARNING": "WARNING",
        "INFO": "INFO",
        "DEBUG": "DEBUG",
        "SUCCESS": "SUCCESS",
    }

    @staticmethod
    def _detect_level(msg: str) -> str | None:
        """从格式化日志行中提取级别，格式: HH:mm:ss | LEVEL    | ..."""
        try:
            parts = msg.split("|", 2)
            if len(parts) >= 2:
                tag = parts[1].strip().upper()
                if tag in GUILogHandler._LEVEL_TAGS:
                    return GUILogHandler._LEVEL_TAGS[tag]
        except Exception:
            pass
        return None

    def _append_log(self, message: str):
        try:
            self.text_widget.configure(state="normal")
            # 记录插入前位置
            tw = self.text_widget._textbox  # 内部 tk.Text
            start_index = tw.index("end-1c")
            self.text_widget.insert("end", message)
            # 按级别着色
            tag = self._detect_level(message)
            if tag:
                end_index = tw.index("end-1c")
                tw.tag_add(tag, start_index, end_index)
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")
            lines = int(self.text_widget.index("end-1c").split(".")[0])
            if lines > self._max_lines:
                self.text_widget.configure(state="normal")
                # 删除前半部分日志
                delete_to = self._max_lines // 2
                self.text_widget.delete("1.0", f"{delete_to}.0")
                self.text_widget.configure(state="disabled")
        except Exception:
            pass


# ==================== 用户偏好设置 ====================


class UserPreferences:
    """用户偏好设置管理"""

    DEFAULT_PREFS: dict[str, Any] = {
        "export_dir": "",
        "remember_export_dir": True,
        "default_export_format": "word",
        "auto_generate_summary": True,
        "default_summary_method": "simple",
        "auto_start_enabled": False,
        "minimize_to_tray": False,
        "low_memory_mode": False,
        "low_memory_prompt_dismissed": False,
        "language": "auto",
        "api_keys": {"openai": "", "anthropic": "", "zhipu": ""},
    }

    def __init__(self):
        self._prefs_file = Path.home() / CONFIG_DIR_NAME / "gui_preferences.json"
        self._prefs: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        """加载用户偏好"""
        try:
            if self._prefs_file.exists():
                with open(self._prefs_file, encoding="utf-8") as f:
                    loaded = cast(dict[str, Any], json.load(f))
                    return {**self.DEFAULT_PREFS, **loaded}
        except Exception as e:
            logger.warning(f"加载偏好设置失败: {e}")
        return self.DEFAULT_PREFS.copy()

    def _save(self) -> None:
        """保存用户偏好"""
        try:
            self._prefs_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._prefs_file, "w", encoding="utf-8") as f:
                json.dump(self._prefs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存偏好设置失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取偏好设置"""
        return self._prefs.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置偏好并保存"""
        self._prefs[key] = value
        self._save()

    @property
    def export_dir(self) -> str:
        return cast(str, self._prefs.get("export_dir", ""))

    @export_dir.setter
    def export_dir(self, value: str):
        self._prefs["export_dir"] = value
        self._save()

    @property
    def remember_export_dir(self) -> bool:
        return bool(self._prefs.get("remember_export_dir", True))

    @remember_export_dir.setter
    def remember_export_dir(self, value: bool):
        self._prefs["remember_export_dir"] = value
        self._save()

    @property
    def default_export_format(self) -> str:
        return cast(str, self._prefs.get("default_export_format", "word"))

    @default_export_format.setter
    def default_export_format(self, value: str):
        self._prefs["default_export_format"] = value
        self._save()

    def get_api_key(self, provider: str) -> str:
        """获取API密钥（自动解密）"""
        api_keys = cast(dict[str, str], self._prefs.get("api_keys", {}))
        raw = cast(str, api_keys.get(provider, ""))
        if not raw:
            return ""
        try:
            if is_encrypted(raw):
                return decrypt_credential(raw)
            # 明文旧数据 — 自动迁移为加密存储
            self.set_api_key(provider, raw)
            return raw
        except Exception as e:
            logger.warning(f"解密 {provider} API密钥失败: {e}")
            return ""

    def set_api_key(self, provider: str, key: str) -> None:
        """设置API密钥（自动加密）"""
        if "api_keys" not in self._prefs:
            self._prefs["api_keys"] = {}
        api_keys = cast(dict[str, str], self._prefs["api_keys"])
        if key:
            try:
                api_keys[provider] = encrypt_credential(key)
            except Exception as e:
                logger.warning(f"加密 {provider} API密钥失败，回退明文存储: {e}")
                api_keys[provider] = key
        else:
            api_keys[provider] = ""
        self._save()

    def get_all_api_keys(self) -> dict[str, str]:
        """获取所有API密钥（自动解密）"""
        raw_keys = cast(dict[str, str], self._prefs.get("api_keys", {}))
        result: dict[str, str] = {}
        for provider, raw in raw_keys.items():
            if not raw:
                result[provider] = ""
                continue
            try:
                if is_encrypted(raw):
                    result[provider] = decrypt_credential(raw)
                else:
                    result[provider] = raw
                    # 自动迁移
                    self.set_api_key(provider, raw)
            except Exception as e:
                logger.warning(f"解密 {provider} API密钥失败: {e}")
                result[provider] = ""
        return result

    @property
    def auto_start_enabled(self) -> bool:
        """开机自启动是否启用"""
        return bool(self._prefs.get("auto_start_enabled", False))

    @auto_start_enabled.setter
    def auto_start_enabled(self, value: bool):
        self._prefs["auto_start_enabled"] = value
        self._save()

    @property
    def minimize_to_tray(self) -> bool:
        """最小化到系统托盘"""
        return bool(self._prefs.get("minimize_to_tray", False))

    @minimize_to_tray.setter
    def minimize_to_tray(self, value: bool):
        self._prefs["minimize_to_tray"] = value
        self._save()

    @property
    def low_memory_mode(self) -> bool:
        """低内存模式"""
        return bool(self._prefs.get("low_memory_mode", False))

    @low_memory_mode.setter
    def low_memory_mode(self, value: bool):
        self._prefs["low_memory_mode"] = value
        self._save()

    @property
    def low_memory_prompt_dismissed(self) -> bool:
        """是否已忽略低内存提示"""
        return bool(self._prefs.get("low_memory_prompt_dismissed", False))

    @low_memory_prompt_dismissed.setter
    def low_memory_prompt_dismissed(self, value: bool):
        self._prefs["low_memory_prompt_dismissed"] = value
        self._save()

    @property
    def language(self) -> str:
        """界面语言设置 ('auto', 'zh_CN', 'en')"""
        return cast(str, self._prefs.get("language", "auto"))

    @language.setter
    def language(self, value: str):
        self._prefs["language"] = value
        self._save()


# ==================== 服务信息数据类 ====================


class SummarizerInfo:
    """摘要器信息"""

    def __init__(self, name: str, available: bool, reason: str = ""):
        self.name = name
        self.available = available
        self.reason = reason

    @property
    def display_name(self) -> str:
        if self.available:
            return f"✓ {self.name}"
        else:
            return f"✗ {self.name}"


class ExporterInfo:
    """导出器信息"""

    def __init__(self, name: str, available: bool, reason: str = ""):
        self.name = name
        self.available = available
        self.reason = reason

    @property
    def display_name(self) -> str:
        if self.available:
            return f"✓ {self.name}"
        else:
            return f"✗ {self.name}"
