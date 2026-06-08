"""Settings page service and API-key frame sections."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from ..styles.colors import ModernColors
from ..utils.i18n import tr

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False

_API_CONFIGS = [
    ("openai", "OpenAI:", "sk-... (用于GPT-4等模型)"),
    ("deepseek", "DeepSeek:", "sk-... (国产高性能模型，推荐)"),
    ("anthropic", "Anthropic:", "sk-ant-... (用于Claude模型)"),
    ("zhipu", "智谱AI:", "智谱AI API Key (用于GLM模型)"),
]

_SUMMARIZER_DISPLAY_NAMES = {
    "simple": "简单摘要",
    "textrank": "TextRank",
    "ollama": "Ollama",
    "openai": "OpenAI",
    "deepseek": "DeepSeek",
    "anthropic": "Anthropic",
    "zhipu": "智谱AI",
}


class SettingsSummarizerSection(ctk.CTkFrame):
    """Summarizer availability section."""

    def __init__(self, master: Any, *, gui: Any, **kwargs: Any) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text=tr("🤖 摘要服务状态"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
        ).pack(anchor="w", pady=(0, 15))

        self.status_frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=(ModernColors.LIGHT_INSET, ModernColors.DARK_INSET),
        )
        self.status_frame.pack(fill="x", pady=5)

    def update_status(self, summarizer_info: Mapping[str, Any]) -> None:
        for widget in self.status_frame.winfo_children():
            widget.destroy()

        for name, info in summarizer_info.items():
            row_frame = ctk.CTkFrame(self.status_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=15, pady=4)
            icon = "✓" if info.available else "✗"
            color = ModernColors.SUCCESS if info.available else ModernColors.ERROR
            display_name = _SUMMARIZER_DISPLAY_NAMES.get(name, name)
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


class SettingsApiKeysSection(ctk.CTkFrame):
    """API key inputs and actions."""

    def __init__(
        self,
        master: Any,
        *,
        gui: Any,
        on_toggle_visibility: Callable[[str], None],
        on_save: Callable[[], None],
        on_clear: Callable[[], None],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui
        self.on_toggle_visibility = on_toggle_visibility
        self.on_save = on_save
        self.on_clear = on_clear
        self.api_key_entries: dict[str, Any] = {}
        self.show_vars: dict[str, Any] = {}
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text=tr("🔑 API 密钥配置"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
        ).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(
            self,
            text=tr("配置 API 密钥后可使用对应的AI摘要服务，密钥将安全地保存在本地"),
            font=ctk.CTkFont(size=12),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack(anchor="w", pady=(0, 15))

        for provider, label_text, placeholder in _API_CONFIGS:
            self._build_provider_row(provider, label_text, placeholder)

        api_btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        api_btn_frame.pack(fill="x", pady=(15, 5))
        ctk.CTkButton(
            api_btn_frame,
            text=tr("💾 保存 API 密钥"),
            width=150,
            height=38,
            corner_radius=8,
            fg_color=ModernColors.SUCCESS,
            command=self.on_save,
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            api_btn_frame,
            text=tr("🗑️ 清除所有密钥"),
            width=150,
            height=38,
            corner_radius=8,
            fg_color=ModernColors.NEUTRAL_BTN,
            hover_color=ModernColors.ERROR,
            command=self.on_clear,
        ).pack(side="left")
        self.status_label = ctk.CTkLabel(
            api_btn_frame, text="", font=ctk.CTkFont(size=12), text_color=ModernColors.SUCCESS
        )
        self.status_label.pack(side="left", padx=20)

    def _build_provider_row(self, provider: str, label_text: str, placeholder: str) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", pady=8)
        ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=14), width=100, anchor="w").pack(
            side="left"
        )

        entry = ctk.CTkEntry(
            frame,
            placeholder_text=placeholder,
            height=38,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            show="•",
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.api_key_entries[provider] = entry

        saved_key = self.gui.user_prefs.get_api_key(provider)
        if saved_key:
            entry.insert(0, saved_key)

        show_var = ctk.BooleanVar(value=False)
        self.show_vars[provider] = show_var
        ctk.CTkCheckBox(
            frame,
            text=tr("显示"),
            variable=show_var,
            width=60,
            font=ctk.CTkFont(size=11),
            command=self._toggle_command(provider),
        ).pack(side="left")

    def _toggle_command(self, provider: str) -> Callable[[], None]:
        def toggle() -> None:
            self.on_toggle_visibility(provider)

        return toggle
