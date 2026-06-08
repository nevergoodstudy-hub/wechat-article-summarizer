"""Settings page preference frame sections."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..styles.colors import ModernColors
from ..utils.i18n import tr
from ..widgets.helpers import LOW_MEMORY_THRESHOLD_GB, get_available_memory_gb

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False


def _section_title(master: Any, text: str) -> None:
    ctk.CTkLabel(
        master,
        text=text,
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
    ).pack(anchor="w", pady=(0, 15))


class SettingsExportSection(ctk.CTkFrame):
    """Export-directory and default-format settings."""

    def __init__(
        self,
        master: Any,
        *,
        gui: Any,
        on_browse: Callable[[], None],
        on_remember_change: Callable[[], None],
        on_format_change: Callable[[str], None],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui
        self.on_browse = on_browse
        self.on_remember_change = on_remember_change
        self.on_format_change = on_format_change
        self._build()

    def _build(self) -> None:
        _section_title(self, tr("📁 导出设置"))

        export_dir_frame = ctk.CTkFrame(self, fg_color="transparent")
        export_dir_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(
            export_dir_frame,
            text=tr("默认导出目录:"),
            font=ctk.CTkFont(size=14),
            width=140,
            anchor="w",
        ).pack(side="left")
        self.export_dir_entry = ctk.CTkEntry(
            export_dir_frame,
            placeholder_text=tr("留空则每次手动选择..."),
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
        )
        self.export_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        saved_dir = self.gui.user_prefs.export_dir
        if saved_dir:
            self.export_dir_entry.insert(0, saved_dir)
        ctk.CTkButton(
            export_dir_frame,
            text=tr("📂 浏览"),
            width=80,
            height=40,
            corner_radius=8,
            fg_color=ModernColors.INFO,
            command=self.on_browse,
        ).pack(side="left")

        remember_frame = ctk.CTkFrame(self, fg_color="transparent")
        remember_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(
            remember_frame,
            text=tr("记住上次导出目录:"),
            font=ctk.CTkFont(size=14),
            width=140,
            anchor="w",
        ).pack(side="left")
        self.remember_dir_var = ctk.BooleanVar(value=self.gui.user_prefs.remember_export_dir)
        ctk.CTkSwitch(
            remember_frame,
            text=tr("启用后，导出时将自动打开上次使用的目录"),
            variable=self.remember_dir_var,
            font=ctk.CTkFont(size=12),
            command=self.on_remember_change,
        ).pack(side="left")

        format_frame = ctk.CTkFrame(self, fg_color="transparent")
        format_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(
            format_frame,
            text=tr("默认导出格式:"),
            font=ctk.CTkFont(size=14),
            width=140,
            anchor="w",
        ).pack(side="left")
        self.default_format_var = ctk.StringVar(value=self.gui.user_prefs.default_export_format)
        ctk.CTkSegmentedButton(
            format_frame,
            values=["word", "html", "markdown"],
            variable=self.default_format_var,
            command=self.on_format_change,
            font=ctk.CTkFont(size=12),
        ).pack(side="left")


class SettingsSystemSection(ctk.CTkFrame):
    """Autostart and tray settings."""

    def __init__(
        self,
        master: Any,
        *,
        gui: Any,
        on_autostart_change: Callable[[], None],
        on_minimize_tray_change: Callable[[], None],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui
        self.on_autostart_change = on_autostart_change
        self.on_minimize_tray_change = on_minimize_tray_change
        self._build()

    def _build(self) -> None:
        _section_title(self, tr("⚙️ 系统设置"))
        self.autostart_var = self._build_switch_row(
            tr("开机自启动:"),
            tr("系统启动时自动运行本程序"),
            self.gui.user_prefs.auto_start_enabled,
            self.on_autostart_change,
        )
        self.minimize_tray_var = self._build_switch_row(
            tr("最小化到托盘:"),
            tr("关闭窗口时最小化到系统托盘而不是退出"),
            self.gui.user_prefs.minimize_to_tray,
            self.on_minimize_tray_change,
        )
        ctk.CTkLabel(
            self,
            text=tr("💡 提示：开启开机自启动后，程序将在后台静默运行"),
            font=ctk.CTkFont(size=11),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack(anchor="w", pady=(5, 0))

    def _build_switch_row(
        self,
        label: str,
        text: str,
        value: bool,
        command: Callable[[], None],
    ) -> Any:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", pady=10)
        ctk.CTkLabel(
            frame,
            text=label,
            font=ctk.CTkFont(size=14),
            width=140,
            anchor="w",
        ).pack(side="left")
        variable = ctk.BooleanVar(value=value)
        ctk.CTkSwitch(
            frame,
            text=text,
            variable=variable,
            font=ctk.CTkFont(size=12),
            command=command,
        ).pack(side="left")
        return variable


class SettingsPerformanceSection(ctk.CTkFrame):
    """Memory and low-memory mode settings."""

    def __init__(
        self,
        master: Any,
        *,
        gui: Any,
        on_low_memory_change: Callable[[], None],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui
        self.on_low_memory_change = on_low_memory_change
        self._build()

    def _build(self) -> None:
        _section_title(self, tr("🚀 性能设置"))
        self._build_memory_status()
        low_memory_frame = ctk.CTkFrame(self, fg_color="transparent")
        low_memory_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(
            low_memory_frame,
            text=tr("低内存模式:"),
            font=ctk.CTkFont(size=14),
            width=140,
            anchor="w",
        ).pack(side="left")
        self.low_memory_var = ctk.BooleanVar(value=self.gui.user_prefs.low_memory_mode)
        ctk.CTkSwitch(
            low_memory_frame,
            text=tr("减少内存占用（禁用部分动画、限制日志缓存）"),
            variable=self.low_memory_var,
            font=ctk.CTkFont(size=12),
            command=self.on_low_memory_change,
        ).pack(side="left")
        ctk.CTkLabel(
            self,
            text=tr("💡 提示：当系统可用内存低于 4GB 时，建议开启低内存模式以获得更流畅的体验"),
            font=ctk.CTkFont(size=11),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack(anchor="w", pady=(5, 0))

    def _build_memory_status(self) -> None:
        memory_status_frame = ctk.CTkFrame(self, fg_color="transparent")
        memory_status_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(
            memory_status_frame,
            text=tr("当前可用内存:"),
            font=ctk.CTkFont(size=14),
            width=140,
            anchor="w",
        ).pack(side="left")
        available_mem = get_available_memory_gb()
        if available_mem is not None:
            mem_color = (
                ModernColors.SUCCESS
                if available_mem >= LOW_MEMORY_THRESHOLD_GB
                else ModernColors.WARNING
            )
            mem_text = f"{available_mem:.1f} GB"
            if available_mem < LOW_MEMORY_THRESHOLD_GB:
                mem_text += f" (低于 {LOW_MEMORY_THRESHOLD_GB:.0f} GB 阈值)"
        else:
            mem_color = ModernColors.LIGHT_TEXT_SECONDARY
            mem_text = tr("无法检测 (psutil 未安装)")
        self.memory_status_label = ctk.CTkLabel(
            memory_status_frame,
            text=mem_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=mem_color,
        )
        self.memory_status_label.pack(side="left")


class SettingsLanguageSection(ctk.CTkFrame):
    """Language preference section."""

    def __init__(
        self,
        master: Any,
        *,
        gui: Any,
        on_language_change: Callable[[str, dict[str, str]], None],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui
        self.on_language_change = on_language_change
        self.lang_code_map = {"跟随系统": "auto", "简体中文": "zh_CN", "English": "en"}
        self._build()

    def _build(self) -> None:
        _section_title(self, tr("🌐 语言设置"))
        lang_frame = ctk.CTkFrame(self, fg_color="transparent")
        lang_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(
            lang_frame, text=tr("界面语言:"), font=ctk.CTkFont(size=14), width=140, anchor="w"
        ).pack(side="left")

        lang_values = ["跟随系统", "简体中文", "English"]
        lang_display_map = {"auto": "跟随系统", "zh_CN": "简体中文", "en": "English"}
        current_display = lang_display_map.get(self.gui.user_prefs.language, "跟随系统")
        self.language_var = ctk.StringVar(value=current_display)
        self.language_menu = ctk.CTkOptionMenu(
            lang_frame,
            values=lang_values,
            variable=self.language_var,
            width=180,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            command=self._on_language_selected,
        )
        self.language_menu.pack(side="left")
        ctk.CTkLabel(
            self,
            text=tr("💡 提示：切换语言后需要重启应用才能完全生效"),
            font=ctk.CTkFont(size=11),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack(anchor="w", pady=(5, 0))

    def _on_language_selected(self, display_value: str) -> None:
        self.on_language_change(display_value, self.lang_code_map)


class SettingsQuickActionsFrame(ctk.CTkFrame):
    """Quick actions and save controls."""

    def __init__(
        self,
        master: Any,
        *,
        gui: Any,
        on_open_export_dir: Callable[[], None],
        on_reset_export_settings: Callable[[], None],
        on_save_settings: Callable[[], None],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui
        self.on_open_export_dir = on_open_export_dir
        self.on_reset_export_settings = on_reset_export_settings
        self.on_save_settings = on_save_settings
        self._build()

    def _build(self) -> None:
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=30, pady=10)
        _section_title(actions, tr("📂 快捷操作"))
        btn_frame = ctk.CTkFrame(actions, fg_color="transparent")
        btn_frame.pack(fill="x")
        self._build_action_button(
            btn_frame, tr("📁 打开导出目录"), ModernColors.SUCCESS, self.on_open_export_dir
        )
        self._build_action_button(
            btn_frame,
            tr("🗑️ 清空设置"),
            ModernColors.NEUTRAL_BTN,
            self.on_reset_export_settings,
        )
        self._build_action_button(
            btn_frame,
            tr("🔄 刷新服务状态"),
            ModernColors.NEUTRAL_BTN,
            self.gui._refresh_availability,
        )

        save_frame = ctk.CTkFrame(self, fg_color="transparent")
        save_frame.pack(fill="x", padx=30, pady=20)
        ctk.CTkButton(
            save_frame,
            text=tr("✔️ 保存设置"),
            width=150,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=ModernColors.SUCCESS,
            command=self.on_save_settings,
        ).pack(side="right")

        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=30, pady=(0, 20))
        self.status_label = ctk.CTkLabel(
            info_frame, text="", font=ctk.CTkFont(size=12), text_color=ModernColors.SUCCESS
        )
        self.status_label.pack(anchor="w")

    def _build_action_button(
        self,
        master: Any,
        text: str,
        color: str,
        command: Callable[[], None],
    ) -> None:
        ctk.CTkButton(
            master,
            text=text,
            width=150,
            height=40,
            corner_radius=8,
            fg_color=color,
            command=command,
        ).pack(side="left", padx=(0, 10))
