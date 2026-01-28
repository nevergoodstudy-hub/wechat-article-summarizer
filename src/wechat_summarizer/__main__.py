"""微信公众号文章总结器 - 主入口点

运行模式：
- GUI（默认）：python -m wechat_summarizer
- GUI（显式）：python -m wechat_summarizer gui
- CLI（推荐）：python -m wechat_summarizer <command> [args]
- CLI（兼容旧写法）：python -m wechat_summarizer cli <command> [args]

说明：
- 当提供任何参数且不是 gui/cli 时，默认按 CLI 解析。
- 这样可直接使用 `python -m wechat_summarizer fetch <URL>` 等命令。
"""

import sys

from .shared.utils import setup_logger


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
        # 保留其余参数不做处理
        _run_gui_or_exit()
        return

    # 兼容：显式 cli 前缀
    if mode_or_cmd == "cli":
        sys.argv.pop(1)
        from .presentation.cli import run_cli

        run_cli()
        return

    # 其他情况：按 CLI 命令解析（推荐）
    from .presentation.cli import run_cli

    run_cli()


def _run_gui_or_exit() -> None:
    """启动 GUI；失败时给出 CLI 退路。"""
    try:
        from .presentation.gui import run_gui

        run_gui()
    except ImportError as e:
        print(f"GUI启动失败: {e}")
        print("尝试使用CLI模式: python -m wechat_summarizer --help")
        sys.exit(1)


if __name__ == "__main__":
    main()
