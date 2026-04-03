"""GUI 启动流程编排。

将 `app.py` 中较长的启动任务定义拆分到独立模块，
让主应用类聚焦在状态与交互逻辑。
"""

from __future__ import annotations

from typing import Any

from .widgets.splash_screen import SplashScreen


def register_startup_tasks(gui: Any, splash: SplashScreen) -> None:
    """注册启动阶段任务到 SplashScreen。"""

    def task_apply_window_style() -> None:
        gui._apply_window_style()

    def task_init_container() -> None:
        gui._init_container_and_viewmodel()

    def task_detect_summarizers() -> None:
        gui._detect_summarizers()

    def task_detect_exporters() -> None:
        gui._detect_exporters()

    def task_build_ui() -> None:
        gui._build_ui()

    def task_setup_logging() -> None:
        gui._setup_log_handler()

    def task_init_system() -> None:
        gui._init_system_settings()

    def task_show_home() -> None:
        gui._show_page(gui.PAGE_HOME)

    splash.add_task("正在应用窗口样式", 1, task_apply_window_style, "配置 Windows 11 风格")
    splash.add_task("正在初始化容器", 2, task_init_container, "加载依赖注入框架")
    splash.add_task(
        "正在检测摘要服务", 5, task_detect_summarizers, "检测 Ollama、OpenAI 等服务状态"
    )
    splash.add_task("正在检测导出器", 2, task_detect_exporters, "检测 Word、PDF 导出支持")
    splash.add_task("正在构建用户界面", 4, task_build_ui, "创建页面和控件")
    splash.add_task("正在配置日志系统", 1, task_setup_logging, "设置日志输出")
    splash.add_task("正在初始化系统", 2, task_init_system, "加载用户偏好设置")
    splash.add_task("正在准备主页", 1, task_show_home, "切换到主页视图")


def run_startup_sequence(gui: Any, splash: SplashScreen) -> None:
    """执行启动任务并在完成后显示主窗口。"""
    splash.show()
    success = splash.run_tasks()

    if success:
        splash.set_complete("启动完成！")
    else:
        splash.set_complete("启动完成（部分服务不可用）")

    splash.close(delay_ms=400)
    gui.root.after(450, gui._show_main_window)
