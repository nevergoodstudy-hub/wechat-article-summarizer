#!/usr/bin/env python3
"""Linux build script for WeChat Article Summarizer.

Usage:
    python scripts/build_linux.py [--appimage]

Requires: PyInstaller, customtkinter, project deps, python3-tk.
Optional: linuxdeploy + appimagetool for AppImage output.
"""

import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPEC_FILE = PROJECT_ROOT / "specs" / "wechat_summarizer_linux.spec"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
APP_NAME = "wechat-article-summarizer"
DISPLAY_NAME = "WeChat Article Summarizer"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print(f"  → {' '.join(cmd)}")
    return subprocess.run(cmd, check=True, **kwargs)


def check_prereqs():
    if platform.system() != "Linux":
        print("⚠ This script is designed for Linux. Exiting.")
        sys.exit(1)
    # Check tkinter
    try:
        import tkinter  # noqa: F401
    except ImportError:
        print("❌ tkinter not found. Install: sudo apt install python3-tk")
        sys.exit(1)
    # Check PyInstaller
    try:
        run(["pyinstaller", "--version"], capture_output=True)
    except FileNotFoundError:
        print("❌ PyInstaller not found. Install: pip install pyinstaller")
        sys.exit(1)


def clean():
    for d in [BUILD_DIR, DIST_DIR / APP_NAME]:
        if isinstance(d, Path) and d.exists():
            if d.is_dir():
                shutil.rmtree(d)
            else:
                d.unlink()
            print(f"  🗑 Removed {d}")


def build():
    print("\n🔨 Building with PyInstaller …")
    run([
        sys.executable, "-m", "PyInstaller",
        str(SPEC_FILE),
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--noconfirm",
    ])
    binary = DIST_DIR / APP_NAME
    if not binary.exists():
        print("❌ Build failed — binary not found")
        sys.exit(1)
    # Make executable
    binary.chmod(0o755)
    print(f"  ✅ Binary built: {binary}  ({binary.stat().st_size / (1<<20):.1f} MB)")
    return binary


def create_desktop_file() -> Path:
    """Generate a .desktop file for AppImage or system install."""
    desktop = DIST_DIR / f"{APP_NAME}.desktop"
    desktop.write_text(f"""[Desktop Entry]
Type=Application
Name={DISPLAY_NAME}
Comment=WeChat article fetcher, summarizer, and exporter
Exec={APP_NAME}
Icon={APP_NAME}
Categories=Utility;Network;
Terminal=false
StartupWMClass={APP_NAME}
""")
    print(f"  ✅ Desktop file: {desktop}")
    return desktop


def create_appimage(binary: Path):
    """Build an AppImage using linuxdeploy."""
    linuxdeploy = shutil.which("linuxdeploy-x86_64.AppImage") or shutil.which("linuxdeploy")
    if not linuxdeploy:
        print("  ⚠ linuxdeploy not found — skipping AppImage")
        print("    Download: https://github.com/linuxdeploy/linuxdeploy/releases")
        return

    appdir = BUILD_DIR / "AppDir"
    if appdir.exists():
        shutil.rmtree(appdir)
    appdir.mkdir(parents=True)

    # Structure: AppDir/usr/bin/<binary>
    usr_bin = appdir / "usr" / "bin"
    usr_bin.mkdir(parents=True)
    shutil.copy2(binary, usr_bin / APP_NAME)

    desktop = create_desktop_file()
    shutil.copy2(desktop, appdir / f"{APP_NAME}.desktop")

    # Placeholder icon (256×256 PNG required)
    icon_dir = appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps"
    icon_dir.mkdir(parents=True, exist_ok=True)
    icon_src = PROJECT_ROOT / "assets" / "icons" / "app.png"
    if icon_src.exists():
        shutil.copy2(icon_src, icon_dir / f"{APP_NAME}.png")
    else:
        # Create a minimal placeholder
        (icon_dir / f"{APP_NAME}.png").touch()

    print("\n📦 Building AppImage …")
    env = os.environ.copy()
    env["OUTPUT"] = str(DIST_DIR / f"{DISPLAY_NAME}-x86_64.AppImage")
    run([linuxdeploy, "--appdir", str(appdir), "--output", "appimage"], env=env)
    print(f"  ✅ AppImage: {env['OUTPUT']}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Build Linux edition")
    parser.add_argument("--appimage", action="store_true", help="Also create AppImage")
    args = parser.parse_args()

    check_prereqs()
    clean()
    binary = build()

    if args.appimage:
        create_appimage(binary)

    digest = sha256(binary)
    print(f"\n🔑 SHA256: {digest}")
    print("\n🎉 Linux build complete!")


if __name__ == "__main__":
    main()
