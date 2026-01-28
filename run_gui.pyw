#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
微信文章总结器 GUI 启动器
使用 pythonw.exe 运行此文件可实现无控制台窗口后台运行
"""

import sys
import os

# 设置项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, "src")

if src_path not in sys.path:
    sys.path.insert(0, src_path)

if __name__ == "__main__":
    try:
        from wechat_summarizer.presentation.gui import run_gui
        run_gui()
    except Exception as e:
        # 后台运行时，错误写入日志文件
        log_path = os.path.join(project_root, "error.log")
        with open(log_path, "a", encoding="utf-8") as f:
            import traceback
            from datetime import datetime
            f.write(f"\n[{datetime.now()}] 启动错误:\n")
            f.write(traceback.format_exc())
            f.write("\n")
