"""设置页面

从 WechatSummarizerGUI 提取的设置页面。
采用 CustomTkinter CTkFrame 子类化 + controller 模式。
"""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING

from loguru import logger

from ..styles.colors import ModernColors
from ..utils.i18n import set_language, tr
from ..widgets.helpers import LOW_MEMORY_THRESHOLD_GB, get_available_memory_gb
from ..widgets.toast_notification import ToastNotification

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False

if TYPE_CHECKING:
    pass


class SettingsPage(ctk.CTkFrame):
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
        ctk.CTkFrame(settings_card, height=2, fg_color=(ModernColors.LIGHT_SEPARATOR, ModernColors.DARK_SEPARATOR)).pack(
            fill="x", padx=30, pady=15
        )

        # API 密钥配置
        self._build_api_section(settings_card)
        ctk.CTkFrame(settings_card, height=2, fg_color=(ModernColors.LIGHT_SEPARATOR, ModernColors.DARK_SEPARATOR)).pack(
            fill="x", padx=30, pady=15
        )

        # 导出设置
        self._build_export_section(settings_card)
        ctk.CTkFrame(settings_card, height=2, fg_color=(ModernColors.LIGHT_SEPARATOR, ModernColors.DARK_SEPARATOR)).pack(
            fill="x", padx=30, pady=15
        )

        # 系统设置
        self._build_system_section(settings_card)
        ctk.CTkFrame(settings_card, height=2, fg_color=(ModernColors.LIGHT_SEPARATOR, ModernColors.DARK_SEPARATOR)).pack(
            fill="x", padx=30, pady=15
        )

        # 性能设置
        self._build_perf_section(settings_card)
        ctk.CTkFrame(settings_card, height=2, fg_color=(ModernColors.LIGHT_SEPARATOR, ModernColors.DARK_SEPARATOR)).pack(
            fill="x", padx=30, pady=15
        )

        # 语言设置
        self._build_lang_section(settings_card)
        ctk.CTkFrame(settings_card, height=2, fg_color=(ModernColors.LIGHT_SEPARATOR, ModernColors.DARK_SEPARATOR)).pack(
            fill="x", padx=30, pady=15
        )

        # 快捷操作 + 保存
        self._build_quick_section(settings_card)

    def _build_summarizer_section(self, parent):
        """摘要服务状态"""
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", padx=30, pady=(20, 10))
        ctk.CTkLabel(
            section,
            text=tr("🤖 摘要服务状态"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
        ).pack(anchor="w", pady=(0, 15))

        self.summarizer_status_frame = ctk.CTkFrame(
            section, corner_radius=10, fg_color=(ModernColors.LIGHT_INSET, ModernColors.DARK_INSET)
        )
        self.summarizer_status_frame.pack(fill="x", pady=5)

    def _build_api_section(self, parent):
        """API 密钥配置"""
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(
            section,
            text=tr("🔑 API 密钥配置"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
        ).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(
            section,
            text=tr("配置 API 密钥后可使用对应的AI摘要服务，密钥将安全地保存在本地"),
            font=ctk.CTkFont(size=12),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack(anchor="w", pady=(0, 15))

        self._api_key_entries = {}

        # 各 API 密钥配置
        api_configs = [
            ("openai", "OpenAI:", "sk-... (用于GPT-4等模型)"),
            ("deepseek", "DeepSeek:", "sk-... (国产高性能模型，推荐)"),
            ("anthropic", "Anthropic:", "sk-ant-... (用于Claude模型)"),
            ("zhipu", "智谱AI:", "智谱AI API Key (用于GLM模型)"),
        ]
        for provider, label_text, placeholder in api_configs:
            frame = ctk.CTkFrame(section, fg_color="transparent")
            frame.pack(fill="x", pady=8)
            ctk.CTkLabel(
                frame, text=label_text, font=ctk.CTkFont(size=14), width=100, anchor="w"
            ).pack(side="left")

            entry = ctk.CTkEntry(
                frame,
                placeholder_text=placeholder,
                height=38,
                corner_radius=8,
                font=ctk.CTkFont(size=12),
                show="•",
            )
            entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
            self._api_key_entries[provider] = entry

            saved_key = self.gui.user_prefs.get_api_key(provider)
            if saved_key:
                entry.insert(0, saved_key)

            show_var = ctk.BooleanVar(value=False)
            setattr(self, f"_{provider}_show_var", show_var)
            ctk.CTkCheckBox(
                frame,
                text=tr("显示"),
                variable=show_var,
                width=60,
                font=ctk.CTkFont(size=11),
                command=lambda p=provider: self._toggle_key_visibility(p),
            ).pack(side="left")

        api_btn_frame = ctk.CTkFrame(section, fg_color="transparent")
        api_btn_frame.pack(fill="x", pady=(15, 5))
        ctk.CTkButton(
            api_btn_frame,
            text=tr("💾 保存 API 密钥"),
            width=150,
            height=38,
            corner_radius=8,
            fg_color=ModernColors.SUCCESS,
            command=self._save_api_keys,
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            api_btn_frame,
            text=tr("🗑️ 清除所有密钥"),
            width=150,
            height=38,
            corner_radius=8,
            fg_color=ModernColors.NEUTRAL_BTN,
            hover_color=ModernColors.ERROR,
            command=self._clear_api_keys,
        ).pack(side="left")
        self.api_status_label = ctk.CTkLabel(
            api_btn_frame, text="", font=ctk.CTkFont(size=12), text_color=ModernColors.SUCCESS
        )
        self.api_status_label.pack(side="left", padx=20)

    def _build_export_section(self, parent):
        """导出设置"""
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(
            section,
            text=tr("📁 导出设置"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
        ).pack(anchor="w", pady=(0, 15))

        export_dir_frame = ctk.CTkFrame(section, fg_color="transparent")
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
            command=self._browse_export_dir,
        ).pack(side="left")

        remember_frame = ctk.CTkFrame(section, fg_color="transparent")
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
            command=self._on_remember_dir_change,
        ).pack(side="left")

        format_frame = ctk.CTkFrame(section, fg_color="transparent")
        format_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(
            format_frame, text=tr("默认导出格式:"), font=ctk.CTkFont(size=14), width=140, anchor="w"
        ).pack(side="left")
        self.default_format_var = ctk.StringVar(value=self.gui.user_prefs.default_export_format)
        ctk.CTkSegmentedButton(
            format_frame,
            values=["word", "html", "markdown"],
            variable=self.default_format_var,
            command=self._on_default_format_change,
            font=ctk.CTkFont(size=12),
        ).pack(side="left")

    def _build_system_section(self, parent):
        """系统设置"""
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(
            section,
            text=tr("⚙️ 系统设置"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
        ).pack(anchor="w", pady=(0, 15))

        autostart_frame = ctk.CTkFrame(section, fg_color="transparent")
        autostart_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(
            autostart_frame,
            text=tr("开机自启动:"),
            font=ctk.CTkFont(size=14),
            width=140,
            anchor="w",
        ).pack(side="left")
        self.autostart_var = ctk.BooleanVar(value=self.gui.user_prefs.auto_start_enabled)
        ctk.CTkSwitch(
            autostart_frame,
            text=tr("系统启动时自动运行本程序"),
            variable=self.autostart_var,
            font=ctk.CTkFont(size=12),
            command=self._on_autostart_change,
        ).pack(side="left")

        minimize_frame = ctk.CTkFrame(section, fg_color="transparent")
        minimize_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(
            minimize_frame,
            text=tr("最小化到托盘:"),
            font=ctk.CTkFont(size=14),
            width=140,
            anchor="w",
        ).pack(side="left")
        self.minimize_tray_var = ctk.BooleanVar(value=self.gui.user_prefs.minimize_to_tray)
        ctk.CTkSwitch(
            minimize_frame,
            text=tr("关闭窗口时最小化到系统托盘而不是退出"),
            variable=self.minimize_tray_var,
            font=ctk.CTkFont(size=12),
            command=self._on_minimize_tray_change,
        ).pack(side="left")

        ctk.CTkLabel(
            section,
            text=tr("💡 提示：开启开机自启动后，程序将在后台静默运行"),
            font=ctk.CTkFont(size=11),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack(anchor="w", pady=(5, 0))

    def _build_perf_section(self, parent):
        """性能设置"""
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(
            section,
            text=tr("🚀 性能设置"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
        ).pack(anchor="w", pady=(0, 15))

        # 内存状态显示
        memory_status_frame = ctk.CTkFrame(section, fg_color="transparent")
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

        # 低内存模式开关
        low_memory_frame = ctk.CTkFrame(section, fg_color="transparent")
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
            command=self._on_low_memory_change,
        ).pack(side="left")

        ctk.CTkLabel(
            section,
            text=tr("💡 提示：当系统可用内存低于 4GB 时，建议开启低内存模式以获得更流畅的体验"),
            font=ctk.CTkFont(size=11),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack(anchor="w", pady=(5, 0))

    def _build_lang_section(self, parent):
        """语言设置"""
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(
            section,
            text=tr("🌐 语言设置"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
        ).pack(anchor="w", pady=(0, 15))

        lang_frame = ctk.CTkFrame(section, fg_color="transparent")
        lang_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(
            lang_frame, text=tr("界面语言:"), font=ctk.CTkFont(size=14), width=140, anchor="w"
        ).pack(side="left")

        # 语言选择下拉框
        lang_values = ["跟随系统", "简体中文", "English"]
        lang_code_map = {"跟随系统": "auto", "简体中文": "zh_CN", "English": "en"}
        lang_display_map = {"auto": "跟随系统", "zh_CN": "简体中文", "en": "English"}

        current_lang = self.gui.user_prefs.language
        current_display = lang_display_map.get(current_lang, "跟随系统")

        self.language_var = ctk.StringVar(value=current_display)
        self.language_menu = ctk.CTkOptionMenu(
            lang_frame,
            values=lang_values,
            variable=self.language_var,
            width=180,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            command=lambda v: self._on_language_change(v, lang_code_map),
        )
        self.language_menu.pack(side="left")

        ctk.CTkLabel(
            section,
            text=tr("💡 提示：切换语言后需要重启应用才能完全生效"),
            font=ctk.CTkFont(size=11),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack(anchor="w", pady=(5, 0))

    def _build_quick_section(self, parent):
        """快捷操作 + 保存"""
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(
            section,
            text=tr("📂 快捷操作"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
        ).pack(anchor="w", pady=(0, 15))

        btn_frame = ctk.CTkFrame(section, fg_color="transparent")
        btn_frame.pack(fill="x")
        ctk.CTkButton(
            btn_frame,
            text=tr("📁 打开导出目录"),
            width=150,
            height=40,
            corner_radius=8,
            fg_color=ModernColors.SUCCESS,
            command=self._open_export_dir,
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            btn_frame,
            text=tr("🗑️ 清空设置"),
            width=150,
            height=40,
            corner_radius=8,
            fg_color=ModernColors.NEUTRAL_BTN,
            command=self._reset_export_settings,
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            btn_frame,
            text=tr("🔄 刷新服务状态"),
            width=150,
            height=40,
            corner_radius=8,
            fg_color=ModernColors.NEUTRAL_BTN,
            command=self.gui._refresh_availability,
        ).pack(side="left")

        save_frame = ctk.CTkFrame(parent, fg_color="transparent")
        save_frame.pack(fill="x", padx=30, pady=20)
        ctk.CTkButton(
            save_frame,
            text=tr("✔️ 保存设置"),
            width=150,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=ModernColors.SUCCESS,
            command=self._save_settings,
        ).pack(side="right")

        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack(fill="x", padx=30, pady=(0, 20))
        self.settings_status_label = ctk.CTkLabel(
            info_frame, text="", font=ctk.CTkFont(size=12), text_color=ModernColors.SUCCESS
        )
        self.settings_status_label.pack(anchor="w")

    # ============================================================
    # 设置处理器 (从 app.py 迁移)
    # ============================================================

    def _browse_export_dir(self):
        """浏览选择导出目录"""
        current_dir = self.export_dir_entry.get().strip()
        initial_dir = (
            current_dir if current_dir and Path(current_dir).exists() else str(Path.home())
        )
        dir_path = filedialog.askdirectory(title="选择默认导出目录", initialdir=initial_dir)
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
                messagebox.showerror("错误", f"创建开机启动项失败: {e}")
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
                messagebox.showerror("错误", f"删除开机启动项失败: {e}")
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
                messagebox.showwarning("提示", f"目录不存在: {export_dir}")
        else:
            messagebox.showinfo("提示", "请先设置导出目录")

    def _reset_export_settings(self):
        """重置导出设置"""
        if not messagebox.askyesno("确认", "确定要重置所有导出设置吗？"):
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
            if messagebox.askyesno("确认", f"目录不存在\n{export_dir}\n\n是否创建？"):
                try:
                    Path(export_dir).mkdir(parents=True, exist_ok=True)
                    logger.info(f"已创建目录: {export_dir}")
                except Exception as e:
                    messagebox.showerror("错误", f"创建目录失败: {e}")
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
        for widget in self.summarizer_status_frame.winfo_children():
            widget.destroy()
        for name, info in self.gui._summarizer_info.items():
            row_frame = ctk.CTkFrame(self.summarizer_status_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=15, pady=4)
            icon = "✓" if info.available else "✗"
            color = ModernColors.SUCCESS if info.available else ModernColors.ERROR
            display_names = {
                "simple": "简单摘要",
                "textrank": "TextRank",
                "ollama": "Ollama",
                "openai": "OpenAI",
                "deepseek": "DeepSeek",
                "anthropic": "Anthropic",
                "zhipu": "智谱AI",
            }
            display_name = display_names.get(name, name)
            ctk.CTkLabel(
                row_frame,
                text=f"{icon} {display_name}",
                font=ctk.CTkFont(size=13, weight="bold" if info.available else "normal"),
                text_color=color,
                width=120,
                anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                row_frame,
                text=info.reason,
                font=ctk.CTkFont(size=11),
                text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
                anchor="w",
            ).pack(side="left", padx=(10, 0))

    def _on_navigate_event(self, *, from_page: str, to_page: str) -> None:
        """响应导航事件。"""
        _ = from_page
        if to_page == self.gui.PAGE_SETTINGS:
            self.update_summarizer_status_display()

    def _toggle_key_visibility(self, provider: str):
        """切换API密钥可见性"""
        entry = self._api_key_entries.get(provider)
        if not entry:
            return None
        show_var = getattr(self, f"_{provider}_show_var", None)
        if show_var and show_var.get():
            entry.configure(show="")
        else:
            entry.configure(show="•")

    def _save_api_keys(self):
        """保存API密钥"""
        from ....infrastructure.config import get_container

        saved_count = 0
        api_keys = {}
        for provider, entry in self._api_key_entries.items():
            key = entry.get().strip()
            self.gui.user_prefs.set_api_key(provider, key)
            if key:
                saved_count += 1
                api_keys[provider] = key
        container = get_container()
        container.reload_summarizers(api_keys)
        self.gui._summarizer_info = self.gui._get_summarizer_info()
        self.update_summarizer_status_display()
        self.gui._refresh_summarizer_menus()
        if saved_count > 0:
            self.api_status_label.configure(
                text=f"✓ 已保存 {saved_count} 个 API 密钥", text_color=ModernColors.SUCCESS
            )
            logger.success(f"已保存 {saved_count} 个 API 密钥")
        else:
            self.api_status_label.configure(text="✓ 密钥已清除", text_color=ModernColors.WARNING)
            logger.info("API 密钥已清除")
        self.gui._set_status("API密钥已更新", ModernColors.SUCCESS)

    def _clear_api_keys(self):
        """清除所有API密钥"""
        if not messagebox.askyesno("确认", "确定要清除所有API密钥吗？"):
            return None
        for provider, entry in self._api_key_entries.items():
            entry.delete(0, "end")
            self.gui.user_prefs.set_api_key(provider, "")
        self.gui._summarizer_info = self.gui._get_summarizer_info()
        self.update_summarizer_status_display()
        self.gui._refresh_summarizer_menus()
        self.api_status_label.configure(text="✓ 所有密钥已清除", text_color=ModernColors.WARNING)
        logger.info("所有 API 密钥已清除")
