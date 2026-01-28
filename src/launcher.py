"""PyInstaller 启动入口 - 使用绝对导入"""
import sys

# 确保使用绝对导入
from wechat_summarizer.shared.utils import setup_logger


def main() -> None:
    """主入口函数"""
    setup_logger()

    # 无参数：默认 GUI
    if len(sys.argv) <= 1:
        _run_gui_or_exit()
        return

    mode_or_cmd = sys.argv[1]

    # 显式 GUI
    if mode_or_cmd == "gui":
        _run_gui_or_exit()
        return

    # 兼容：显式 cli 前缀
    if mode_or_cmd == "cli":
        sys.argv.pop(1)
        from wechat_summarizer.presentation.cli import run_cli
        run_cli()
        return

    # 其他情况：按 CLI 命令解析
    from wechat_summarizer.presentation.cli import run_cli
    run_cli()


def _run_gui_or_exit() -> None:
    """启动 GUI；失败时给出 CLI 退路。"""
    try:
        from wechat_summarizer.presentation.gui import run_gui
        run_gui()
    except ImportError as e:
        print(f"GUI启动失败: {e}")
        print("尝试使用CLI模式: wechat-summarizer --help")
        sys.exit(1)


if __name__ == "__main__":
    main()
