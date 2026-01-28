# -*- mode: python ; coding: utf-8 -*-
"""
微信文章总结器 - PyInstaller 打包配置
版本: 2.4.0
更新日期: 2026-01-28
"""

import os
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(SPECPATH)
SRC_DIR = PROJECT_ROOT / "src"

block_cipher = None

# 需要包含的数据文件
datas = [
    # 翻译文件
    (str(SRC_DIR / "wechat_summarizer" / "presentation" / "gui" / "translations"), 
     "wechat_summarizer/presentation/gui/translations"),
]

# 隐藏导入 - 确保动态导入的模块被包含
hiddenimports = [
    # GUI组件
    'customtkinter',
    'PIL',
    'PIL._tkinter_finder',
    
    # 网络请求
    'httpx',
    'httpx._transports.default',
    'httpx._transports.asgi',
    'httpx._transports.wsgi',
    
    # HTML解析
    'bs4',
    'lxml',
    'lxml.etree',
    'lxml._elementpath',
    
    # 配置
    'pydantic',
    'pydantic_settings',
    'pydantic.deprecated.decorator',
    
    # 导出
    'markdownify',
    'docx',
    'html2docx',
    'py7zr',
    
    # 系统
    'psutil',
    'platformdirs',
    'loguru',
    
    # Windows特性
    'pywinstyles',
    'comtypes',
    
    # AI (可选)
    'openai',
    'anthropic',
    'tiktoken',
    
    # 编码
    'encodings',
    'encodings.utf_8',
    'encodings.gbk',
    'encodings.gb2312',
    'encodings.cp936',
]

# 分析
a = Analysis(
    [str(SRC_DIR / "launcher.py")],
    pathex=[str(SRC_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小体积
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tensorflow',
        'torch',
        'pytest',
        'unittest',
        '_pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ 归档
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='微信文章总结器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标: 'assets/icon.ico'
    version=None,  # 可以添加版本信息
)
