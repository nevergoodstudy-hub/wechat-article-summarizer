"""Modern GUI shell composed from focused mixins."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ...infrastructure.config import get_settings
from ...shared.constants import GUI_MIN_SIZE, GUI_WINDOW_TITLE
from .app_actions import GUIActionsMixin
from .app_bootstrap import GUIBootstrapMixin
from .app_navigation import GUINavigationMixin
from .app_runtime import GUIRuntimeMixin
from .ctk_compat import CTK_AVAILABLE, ctk
from .event_bus import GUIEventBus
from .main_window import MainWindow
from .startup import register_startup_tasks, run_startup_sequence
from .styles.typography import ChineseFonts
from .utils.i18n import set_language
from .widgets.helpers import ExporterInfo, SummarizerInfo, UserPreferences
from .widgets.splash_screen import SplashScreen

if TYPE_CHECKING:
    from ...domain.entities import Article
    from ...infrastructure.config import AppSettings, Container


class WechatSummarizerGUI(
    GUIBootstrapMixin,
    GUINavigationMixin,
    GUIActionsMixin,
    GUIRuntimeMixin,
):
    """微信公众号文章总结器 GUI。"""

    PAGE_HOME = "home"
    PAGE_SINGLE = "single"
    PAGE_BATCH = "batch"
    PAGE_HISTORY = "history"
    PAGE_SETTINGS = "settings"

    def __init__(self, container: Container, settings: AppSettings):
        if not CTK_AVAILABLE:
            raise ImportError("customtkinter未安装，请运行 pip install customtkinter")

        self.settings = settings
        self.user_prefs = UserPreferences()
        set_language(self.user_prefs.language)

        self._chinese_font = ChineseFonts.get_best_font()
        self._appearance_mode = "dark"
        ctk.set_appearance_mode(self._appearance_mode)
        ctk.set_default_color_theme("dark-blue")

        self.root = ctk.CTk()
        self.root.title(GUI_WINDOW_TITLE)
        self.root.geometry("1280x800")
        self.root.minsize(*GUI_MIN_SIZE)
        self.root.withdraw()

        splash = SplashScreen(self.root)

        self.container = container
        self.main_viewmodel = cast(Any, None)
        self.current_article: Article | None = None
        self.batch_urls: list[str] = []
        self.batch_results: list[Article] = []
        self._current_page = self.PAGE_HOME
        self._page_frames: dict[str, object] = {}
        self._summarizer_info: dict[str, SummarizerInfo] = {}
        self._exporter_info: dict[str, ExporterInfo] = {}
        self._log_handler = cast(Any, None)
        self._log_handler_id = cast(Any, None)
        self._animation_running = False
        self._pulse_animation_id = None
        self._pulse_phase = 0

        self._batch_processing_active = False
        self._batch_export_active = False
        self._single_processing_active = False

        self._tips_data: list[str] = []
        self._current_tip_index = 0
        self._tip_auto_switch_id = None

        self.event_bus = GUIEventBus()

        register_startup_tasks(self, splash)
        run_startup_sequence(self, splash)
        self._check_memory_on_startup()

    def run(self) -> None:
        self.root.mainloop()


def run_gui(*, raise_on_error: bool = False) -> None:
    """Launch the GUI through the thin `MainWindow` coordinator."""
    if not CTK_AVAILABLE:
        message = "customtkinter未安装，请运行: pip install customtkinter"
        if raise_on_error:
            raise ImportError(message)
        print(f"错误: {message}")
        raise SystemExit(1)

    window = MainWindow(WechatSummarizerGUI, settings=get_settings())
    window.run()


if __name__ == "__main__":
    run_gui()
