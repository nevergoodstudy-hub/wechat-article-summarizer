"""设置页面

从 WechatSummarizerGUI 提取的设置页面。
采用 CustomTkinter CTkFrame 子类化 + controller 模式。
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from ..dialogs import (
    choose_export_directory,
    confirm_create_missing_directory,
    confirm_reset_export_settings,
    show_create_directory_error,
    show_export_directory_not_configured,
    show_missing_export_directory,
    show_startup_error,
)
from ..frames import (
    SettingsApiKeysSection,
    SettingsExportSection,
    SettingsLanguageSection,
    SettingsPerformanceSection,
    SettingsQuickActionsFrame,
    SettingsSummarizerSection,
    SettingsSystemSection,
)
from ..settings_api_actions import SettingsApiActionsMixin
from ..styles.colors import ModernColors
from ..utils.i18n import set_language, tr
from ..widgets.toast_notification import ToastNotification

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False


class SettingsPage(SettingsApiActionsMixin, ctk.CTkFrame):
    """设置页面

    Args:
        master: 父容器
        gui: WechatSummarizerGUI 控制器引用
    """

    def __init__(self, master, gui, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui

        # 公开属性 - 供外部通过别名访问
        self.summarizer_status_frame = None
        self._api_key_entries = {}
        self._openai_show_var = None
        self._deepseek_show_var = None
        self._anthropic_show_var = None
        self._zhipu_show_var = None
        self.api_status_label = None
        self.export_dir_entry = None
        self.remember_dir_var = None
        self.default_format_var = None
        self.autostart_var = None
        self.minimize_tray_var = None
        self.low_memory_var = None
        self.language_var = None
        self.settings_status_label = None
        self.memory_status_label = None
        self._unsubscribe_navigate = None
        if hasattr(self.gui, "event_bus"):
            self._unsubscribe_navigate = self.gui.event_bus.subscribe(
                "navigate", self._on_navigate_event
            )

        self._build()

    def _build(self):
        """构建设置页面"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text=tr("⚙️ 设置"), font=ctk.CTkFont(size=24, weight="bold")).pack(
            side="left"
        )

        settings_scroll = ctk.CTkScrollableFrame(
            self, corner_radius=15, fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD)
        )
        settings_scroll.pack(fill="both", expand=True)
        settings_card = settings_scroll

        # 摘要服务状态
        self._build_summarizer_section(settings_card)
        self._add_separator(settings_card)

        # API 密钥配置
        self._build_api_section(settings_card)
        self._add_separator(settings_card)

        # 导出设置
        self._build_export_section(settings_card)
        self._add_separator(settings_card)

        # 系统设置
        self._build_system_section(settings_card)
        self._add_separator(settings_card)

        # 性能设置
        self._build_perf_section(settings_card)
        self._add_separator(settings_card)

        # 语言设置
        self._build_lang_section(settings_card)
        self._add_separator(settings_card)

        # 快捷操作 + 保存
        self._build_quick_section(settings_card)

    def _add_separator(self, parent):
        ctk.CTkFrame(
            parent,
            height=2,
            fg_color=(ModernColors.LIGHT_SEPARATOR, ModernColors.DARK_SEPARATOR),
        ).pack(fill="x", padx=30, pady=15)

    def _build_summarizer_section(self, parent):
        """摘要服务状态"""
        self.summarizer_section = SettingsSummarizerSection(parent, gui=self.gui)
        self.summarizer_section.pack(fill="x", padx=30, pady=(20, 10))
        self.summarizer_status_frame = self.summarizer_section.status_frame

    def _build_api_section(self, parent):
        """API 密钥配置"""
        self.api_keys_section = SettingsApiKeysSection(
            parent,
            gui=self.gui,
            on_toggle_visibility=self._toggle_key_visibility,
            on_save=self._save_api_keys,
            on_clear=self._clear_api_keys,
        )
        self.api_keys_section.pack(fill="x", padx=30, pady=10)
        self._api_key_entries = self.api_keys_section.api_key_entries
        self.api_status_label = self.api_keys_section.status_label
        for provider, show_var in self.api_keys_section.show_vars.items():
            setattr(self, f"_{provider}_show_var", show_var)

    def _build_export_section(self, parent):
        """导出设置"""
        self.export_section = SettingsExportSection(
            parent,
            gui=self.gui,
            on_browse=self._browse_export_dir,
            on_remember_change=self._on_remember_dir_change,
            on_format_change=self._on_default_format_change,
        )
        self.export_section.pack(fill="x", padx=30, pady=10)
        self.export_dir_entry = self.export_section.export_dir_entry
        self.remember_dir_var = self.export_section.remember_dir_var
        self.default_format_var = self.export_section.default_format_var

    def _build_system_section(self, parent):
        """系统设置"""
        self.system_section = SettingsSystemSection(
            parent,
            gui=self.gui,
            on_autostart_change=self._on_autostart_change,
            on_minimize_tray_change=self._on_minimize_tray_change,
        )
        self.system_section.pack(fill="x", padx=30, pady=10)
        self.autostart_var = self.system_section.autostart_var
        self.minimize_tray_var = self.system_section.minimize_tray_var

    def _build_perf_section(self, parent):
        """性能设置"""
        self.performance_section = SettingsPerformanceSection(
            parent,
            gui=self.gui,
            on_low_memory_change=self._on_low_memory_change,
        )
        self.performance_section.pack(fill="x", padx=30, pady=10)
        self.low_memory_var = self.performance_section.low_memory_var
        self.memory_status_label = self.performance_section.memory_status_label

    def _build_lang_section(self, parent):
        """语言设置"""
        self.language_section = SettingsLanguageSection(
            parent,
            gui=self.gui,
            on_language_change=self._on_language_change,
        )
        self.language_section.pack(fill="x", padx=30, pady=10)
        self.language_var = self.language_section.language_var
        self.language_menu = self.language_section.language_menu

    def _build_quick_section(self, parent):
        """快捷操作 + 保存"""
        self.quick_actions_frame = SettingsQuickActionsFrame(
            parent,
            gui=self.gui,
            on_open_export_dir=self._open_export_dir,
            on_reset_export_settings=self._reset_export_settings,
            on_save_settings=self._save_settings,
        )
        self.quick_actions_frame.pack(fill="x")
        self.settings_status_label = self.quick_actions_frame.status_label

    # ============================================================
    # 设置处理器 (从 app.py 迁移)
    # ============================================================

    def _browse_export_dir(self):
        """浏览选择导出目录"""
        current_dir = self.export_dir_entry.get().strip()
        dir_path = choose_export_directory(current_dir)
        if dir_path:
            self.export_dir_entry.delete(0, "end")
            self.export_dir_entry.insert(0, dir_path)
            logger.info(f"已选择导出目录: {dir_path}")

    def _on_remember_dir_change(self):
        """记住目录选项变更"""
        self.gui.user_prefs.remember_export_dir = self.remember_dir_var.get()
        logger.info(f"记住导出目录: {('启用' if self.remember_dir_var.get() else '禁用')}")

    def _on_default_format_change(self, value: str):
        """默认格式变更"""
        self.gui.user_prefs.default_export_format = value
        logger.info(f"默认导出格式: {value}")

    def _on_autostart_change(self):
        """开机自启动设置变更"""
        enabled = self.autostart_var.get()
        self.gui.user_prefs.auto_start_enabled = enabled
        startup_folder = (
            Path.home()
            / "AppData"
            / "Roaming"
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / "Startup"
        )
        shortcut_path = startup_folder / "微信文章总结器.lnk"
        project_root = Path(__file__).parent.parent.parent.parent.parent.parent
        vbs_path = project_root / "start_silent.vbs"
        if enabled:
            try:
                import subprocess

                ps_script = f'\n$WshShell = New-Object -ComObject WScript.Shell\n$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")\n$Shortcut.TargetPath = "{vbs_path}"\n$Shortcut.WorkingDirectory = "{project_root}"\n$Shortcut.Description = "微信文章总结器 - 开机自启动"\n$Shortcut.Save()\n'
                result = subprocess.run(
                    ["powershell", "-Command", ps_script], capture_output=True, text=True
                )
                if result.returncode == 0:
                    self.settings_status_label.configure(
                        text="✓ 已启用开机自启动", text_color=ModernColors.SUCCESS
                    )
                    logger.success("已启用开机自启动")
                else:
                    raise Exception(result.stderr)
            except Exception as e:
                self.autostart_var.set(False)
                self.gui.user_prefs.auto_start_enabled = False
                show_startup_error(f"创建开机启动项失败: {e}")
                logger.error(f"创建开机启动项失败: {e}")
                return None
        else:
            try:
                if shortcut_path.exists():
                    shortcut_path.unlink()
                self.settings_status_label.configure(
                    text="✓ 已禁用开机自启动", text_color=ModernColors.SUCCESS
                )
                logger.info("已禁用开机自启动")
            except Exception as e:
                self.autostart_var.set(True)
                self.gui.user_prefs.auto_start_enabled = True
                show_startup_error(f"删除开机启动项失败: {e}")
                logger.error(f"删除开机启动项失败: {e}")

    def _on_minimize_tray_change(self):
        """最小化到托盘设置变更"""
        enabled = self.minimize_tray_var.get()
        self.gui.user_prefs.minimize_to_tray = enabled
        if enabled:
            self.settings_status_label.configure(
                text="✓ 已启用最小化到托盘", text_color=ModernColors.SUCCESS
            )
            logger.info("已启用最小化到系统托盘")
        else:
            self.settings_status_label.configure(
                text="✓ 已禁用最小化到托盘", text_color=ModernColors.SUCCESS
            )
            logger.info("已禁用最小化到系统托盘")

    def _on_low_memory_change(self):
        """低内存模式设置变更"""
        enabled = self.low_memory_var.get()
        self.gui.user_prefs.low_memory_mode = enabled
        self.gui.user_prefs.low_memory_prompt_dismissed = False
        if enabled:
            self.gui._apply_low_memory_optimizations()
            self.settings_status_label.configure(
                text="✓ 已启用低内存模式", text_color=ModernColors.SUCCESS
            )
            logger.info("已启用低内存模式")
        else:
            self.settings_status_label.configure(
                text="✓ 已禁用低内存模式", text_color=ModernColors.SUCCESS
            )
            logger.info("已禁用低内存模式，重启后完全生效")

    def _on_language_change(self, display_value: str, lang_code_map: dict):
        """界面语言设置变更"""
        lang_code = lang_code_map.get(display_value, "auto")
        self.gui.user_prefs.language = lang_code
        set_language(lang_code)
        self.settings_status_label.configure(
            text=f"✓ 语言已设置为: {display_value}", text_color=ModernColors.SUCCESS
        )
        logger.info(f"界面语言已切换: {lang_code}")
        if hasattr(self.gui, "_toast_manager") and self.gui._toast_manager:
            self.gui._toast_manager.info(f"语言已设置为 {display_value}，重启应用后完全生效")
        else:
            ToastNotification(
                self.gui.root,
                "🌐 语言已切换",
                f"语言已设置为 {display_value}\n重启应用后完全生效",
                toast_type="info",
                duration_ms=3000,
            )

    def _open_export_dir(self):
        """打开导出目录"""
        export_dir = self.export_dir_entry.get().strip() or self.gui.user_prefs.export_dir
        if not export_dir:
            export_dir = self.gui.settings.export.default_output_dir
        if export_dir:
            path = Path(export_dir)
            if path.exists():
                import os

                os.startfile(str(path))
                logger.info(f"已打开目录: {path}")
            else:
                show_missing_export_directory(export_dir)
        else:
            show_export_directory_not_configured()

    def _reset_export_settings(self):
        """重置导出设置"""
        if not confirm_reset_export_settings():
            return None
        self.export_dir_entry.delete(0, "end")
        self.remember_dir_var.set(True)
        self.default_format_var.set("word")
        self.gui.user_prefs.export_dir = ""
        self.gui.user_prefs.remember_export_dir = True
        self.gui.user_prefs.default_export_format = "word"
        self.settings_status_label.configure(text="✓ 设置已重置", text_color=ModernColors.SUCCESS)
        logger.info("导出设置已重置")

    def _save_settings(self):
        """保存设置"""
        export_dir = self.export_dir_entry.get().strip()
        if export_dir and (not Path(export_dir).exists()):
            if confirm_create_missing_directory(export_dir):
                try:
                    Path(export_dir).mkdir(parents=True, exist_ok=True)
                    logger.info(f"已创建目录: {export_dir}")
                except Exception as e:
                    show_create_directory_error(f"创建目录失败: {e}")
                    return None
            else:
                return None
        self.gui.user_prefs.export_dir = export_dir
        self.gui.user_prefs.remember_export_dir = self.remember_dir_var.get()
        self.gui.user_prefs.default_export_format = self.default_format_var.get()
        self.settings_status_label.configure(text="✓ 设置已保存", text_color=ModernColors.SUCCESS)
        self.gui._set_status("设置已保存", ModernColors.SUCCESS)
        logger.success("设置已保存")

    def update_summarizer_status_display(self):
        """更新摘要器状态显示"""
        self.summarizer_section.update_status(self.gui._summarizer_info)

    def _on_navigate_event(self, *, from_page: str, to_page: str) -> None:
        """响应导航事件。"""
        _ = from_page
        if to_page == self.gui.PAGE_SETTINGS:
            self.update_summarizer_status_display()
