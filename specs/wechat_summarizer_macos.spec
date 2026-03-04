# -*- mode: python ; coding: utf-8 -*-
"""
WeChat Article Summarizer — macOS PyInstaller spec
- Windowed bootloader (console=False)
- Excludes Windows-only hiddenimports
- Produces .app bundle in dist/
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).resolve()
SRC_DIR = PROJECT_ROOT.parent / "src"

# Data files to include (translations, etc.)
datas = [
    (
        str(SRC_DIR / "wechat_summarizer" / "presentation" / "gui" / "translations"),
        "wechat_summarizer/presentation/gui/translations",
    ),
]

# Hidden imports (macOS-safe)
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
    # System utils
    "platformdirs",
    "loguru",
    # Encodings safety on macOS
    "encodings",
    "encodings.utf_8",
]

block_cipher = None

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
        # Exclude heavy/unused libs
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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WeChat Article Summarizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,  # windowed app bundle
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,  # set in CI script
    entitlements_file=str(PROJECT_ROOT.parent / 'scripts' / 'macos' / 'entitlements.plist'),
    icon=None,  # optionally add .icns: PROJECT_ROOT.parent / 'assets' / 'icons' / 'app.icns'
)
