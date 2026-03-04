#!/usr/bin/env python3
"""macOS build script for WeChat Article Summarizer.

Usage:
    python scripts/build_macos.py [--sign] [--dmg]

Requires: PyInstaller, customtkinter, and project dependencies installed.
Optional: Xcode CLI tools for codesign/notarytool; create-dmg for .dmg output.
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
SPEC_FILE = PROJECT_ROOT / "specs" / "wechat_summarizer_macos.spec"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
APP_NAME = "WeChat Article Summarizer"
ENTITLEMENTS = PROJECT_ROOT / "scripts" / "macos" / "entitlements.plist"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print(f"  → {' '.join(cmd)}")
    return subprocess.run(cmd, check=True, **kwargs)


def check_prereqs():
    """Verify we're on macOS and have required tools."""
    if platform.system() != "Darwin":
        print("⚠ This script is designed for macOS. Exiting.")
        sys.exit(1)
    try:
        run(["pyinstaller", "--version"], capture_output=True)
    except FileNotFoundError:
        print("❌ PyInstaller not found. Install: pip install pyinstaller")
        sys.exit(1)


def clean():
    """Remove prior build artifacts."""
    for d in [BUILD_DIR, DIST_DIR / f"{APP_NAME}.app"]:
        if d.exists():
            shutil.rmtree(d)
            print(f"  🗑 Removed {d}")


def build():
    """Run PyInstaller with the macOS spec."""
    print("\n🔨 Building with PyInstaller …")
    run([
        sys.executable, "-m", "PyInstaller",
        str(SPEC_FILE),
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--noconfirm",
    ])
    app_path = DIST_DIR / f"{APP_NAME}.app"
    if not app_path.exists():
        # Onefile fallback — look for standalone binary
        onefile = DIST_DIR / APP_NAME
        if onefile.exists():
            print(f"  ✅ Onefile binary built: {onefile}")
            return onefile
        print("❌ Build failed — no .app or binary produced")
        sys.exit(1)
    print(f"  ✅ App bundle built: {app_path}")
    return app_path


def codesign(app_path: Path, identity: str | None = None):
    """Sign the .app bundle with hardened runtime."""
    identity = identity or os.environ.get("CODESIGN_IDENTITY", "-")
    print(f"\n🔏 Signing with identity: {identity}")
    cmd = [
        "codesign",
        "--force", "--deep", "--options", "runtime",
        "--timestamp",
        "--entitlements", str(ENTITLEMENTS),
        "--sign", identity,
        str(app_path),
    ]
    run(cmd)
    # Verify
    run(["codesign", "--verify", "--deep", "--strict", str(app_path)])
    print("  ✅ Signature verified")


def notarize(app_path: Path):
    """Submit app to Apple notary service (requires APPLE_ID env vars)."""
    apple_id = os.environ.get("APPLE_ID")
    team_id = os.environ.get("APPLE_TEAM_ID")
    password = os.environ.get("APPLE_APP_PASSWORD")
    if not all([apple_id, team_id, password]):
        print("⚠ Skipping notarization — set APPLE_ID, APPLE_TEAM_ID, APPLE_APP_PASSWORD")
        return

    # Zip the .app for submission
    zip_path = app_path.with_suffix(".zip")
    run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(app_path), str(zip_path)])

    print("\n📤 Submitting for notarization …")
    run([
        "xcrun", "notarytool", "submit", str(zip_path),
        "--apple-id", apple_id,
        "--team-id", team_id,
        "--password", password,
        "--wait",
    ])
    # Staple ticket
    run(["xcrun", "stapler", "staple", str(app_path)])
    zip_path.unlink(missing_ok=True)
    print("  ✅ Notarization complete")


def make_dmg(app_path: Path):
    """Create a .dmg installer using create-dmg (if installed)."""
    dmg_path = DIST_DIR / f"{APP_NAME}.dmg"
    if shutil.which("create-dmg"):
        print(f"\n💿 Creating {dmg_path.name} …")
        cmd = [
            "create-dmg",
            "--volname", APP_NAME,
            "--window-size", "600", "400",
            "--icon-size", "100",
            "--app-drop-link", "450", "200",
            "--icon", f"{APP_NAME}.app", "150", "200",
            str(dmg_path),
            str(app_path),
        ]
        run(cmd)
    else:
        print("  ⚠ create-dmg not found; creating .dmg with hdiutil …")
        run(["hdiutil", "create", "-volname", APP_NAME,
             "-srcfolder", str(app_path), "-ov", "-format", "UDZO",
             str(dmg_path)])
    print(f"  ✅ DMG created: {dmg_path}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Build macOS edition")
    parser.add_argument("--sign", action="store_true", help="Codesign the app bundle")
    parser.add_argument("--notarize", action="store_true", help="Submit to Apple notary service")
    parser.add_argument("--dmg", action="store_true", help="Create .dmg installer")
    parser.add_argument("--identity", help="Codesign identity (default: CODESIGN_IDENTITY env or ad-hoc)")
    args = parser.parse_args()

    check_prereqs()
    clean()
    app_path = build()

    if args.sign:
        codesign(app_path, args.identity)

    if args.notarize:
        notarize(app_path)

    if args.dmg:
        make_dmg(app_path)

    # Print SHA256
    target = app_path if app_path.is_file() else None
    if target:
        digest = sha256(target)
        print(f"\n🔑 SHA256: {digest}")

    print("\n🎉 macOS build complete!")


if __name__ == "__main__":
    main()
