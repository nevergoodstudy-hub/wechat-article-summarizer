# -*- mode: python ; coding: utf-8 -*-
"""
WeChat Article Summarizer — Linux PyInstaller spec
- Windowed bootloader (console=False)
- Excludes Windows-only / macOS-only hiddenimports
- Single onefile executable
"""

from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).resolve()
SRC_DIR = PROJECT_ROOT.parent / "src"

datas = [
    (
        str(SRC_DIR / "wechat_summarizer" / "presentation" / "gui" / "translations"),
        "wechat_summarizer/presentation/gui/translations",
    ),
]

hiddenimports = [
    # GUI
    "customtkinter",
    "PIL",
    "PIL._tkinter_finder",
    # Networking
    "httpx",
    "httpx._transports.default",
    "httpx._transports.asgi",
    "httpx._transports.wsgi",
    # HTML parsing
    "bs4",
    "lxml",
    "lxml.etree",
    "lxml._elementpath",
    # Config
    "pydantic",
    "pydantic_settings",
    "pydantic.deprecated.decorator",
    # Export
    "markdownify",
    "docx",
    "html2docx",
    "py7zr",
    # System
    "platformdirs",
    "loguru",
    # Encodings
    "encodings",
    "encodings.utf_8",
]

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
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "tensorflow",
        "torch",
        "pytest",
        "unittest",
        "_pytest",
        # Windows-only
        "pywinstyles",
        "comtypes",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='wechat-article-summarizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # strip works fine on Linux ELF
    upx=True,
    runtime_tmpdir=None,
    console=False,  # windowed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    icon=None,
)
