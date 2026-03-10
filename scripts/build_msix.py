#!/usr/bin/env python
"""MSIX 预发布打包脚本。

目标：
1. 以 `src/launcher.py` 作为唯一 PyInstaller 入口，避免依赖失效的旧 spec 文件。
2. 统一 EXE 名称、Manifest 可执行文件名与资产命名。
3. 在仓库缺少正式商店图标时自动生成占位 PNG/ICO，保证打包链路可验证。
4. 在满足 Windows SDK / PyInstaller / （可选）证书前提下输出可提交前检查的 `.msix`。
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
MSIX_DIR = PROJECT_ROOT / "msix"
MANIFEST_TEMPLATE = MSIX_DIR / "AppxManifest.xml"
LAUNCHER = SRC_DIR / "launcher.py"
START_SILENT_VBS = PROJECT_ROOT / "start_silent.vbs"

PYINSTALLER_BUILD_DIR = BUILD_DIR / "pyinstaller"
MSIX_STAGE_DIR = BUILD_DIR / "msix_package"
MSIX_ASSET_CACHE_DIR = BUILD_DIR / "msix_assets"

APP_NAME = "WeChatArticleSummarizer"
APP_EXECUTABLE = f"{APP_NAME}.exe"
PACKAGE_NAME = "WeChatSummarizer"
PUBLISHER = "CN=WeChatSummarizer"
DISPLAY_NAME = "WeChat Article Summarizer"
PUBLISHER_DISPLAY_NAME = "WeChatSummarizer"
DESCRIPTION = (
    "A desktop application for fetching WeChat and web articles, generating AI summaries, "
    "and exporting results to multiple formats."
)
ARCHITECTURE = "x64"

TRANSLATIONS_DIR = (
    SRC_DIR / "wechat_summarizer" / "presentation" / "gui" / "translations"
)

REQUIRED_ASSETS: dict[str, tuple[int, int]] = {
    "StoreLogo.png": (50, 50),
    "Square44x44Logo.png": (44, 44),
    "Square71x71Logo.png": (71, 71),
    "Square150x150Logo.png": (150, 150),
    "Wide310x150Logo.png": (310, 150),
    "Square310x310Logo.png": (310, 310),
    "SplashScreen.png": (620, 300),
}


def print_header(title: str) -> None:
    print(f"\n{'=' * 20} {title} {'=' * 20}")


def print_status(icon: str, message: str) -> None:
    print(f"  {icon} {message}")


def run_cmd(
    cmd: list[str],
    *,
    cwd: Path = PROJECT_ROOT,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    print(f"  >>> {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode != 0:
        if result.stdout.strip():
            print(result.stdout)
        if result.stderr.strip():
            print(result.stderr)
        raise RuntimeError(f"Command failed with exit code {result.returncode}")
    return result


def read_project_version() -> str:
    content = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"\s*$', content, re.MULTILINE)
    if not match:
        raise RuntimeError("Could not find project.version in pyproject.toml")
    return normalize_msix_version(match.group(1))


def normalize_msix_version(raw_version: str) -> str:
    parts = [int(part) for part in re.findall(r"\d+", raw_version)]
    if not parts:
        raise RuntimeError(f"Invalid project version: {raw_version!r}")
    while len(parts) < 4:
        parts.append(0)
    normalized = parts[:4]
    if any(part < 0 or part > 65535 for part in normalized):
        raise RuntimeError(f"MSIX version parts must be in [0, 65535], got {normalized}")
    return ".".join(str(part) for part in normalized)


def find_windows_sdk_tool(tool_name: str) -> Path | None:
    found = shutil.which(tool_name)
    if found:
        return Path(found)

    sdk_root = Path(r"C:\Program Files (x86)\Windows Kits\10\bin")
    if not sdk_root.exists():
        return None

    candidates = sorted(sdk_root.glob(f"*/x64/{tool_name}"), reverse=True)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def check_pyinstaller() -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode == 0


def copy_or_generate_assets(destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    custom_assets_dir = MSIX_DIR / "Assets"
    legacy_icon = PROJECT_ROOT / "assets" / "icons" / "app.ico"

    from PIL import Image, ImageDraw, ImageFont

    def generate_placeholder_png(path: Path, size: tuple[int, int], label: str) -> None:
        width, height = size
        image = Image.new("RGBA", size, (7, 193, 96, 255))
        draw = ImageDraw.Draw(image)
        border = max(2, min(width, height) // 24)
        draw.rounded_rectangle(
            (border, border, width - border, height - border),
            radius=max(6, min(width, height) // 10),
            outline=(255, 255, 255, 230),
            width=max(1, min(width, height) // 22),
        )

        font = ImageFont.load_default()
        bbox = draw.multiline_textbbox((0, 0), label, font=font, align="center")
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) / 2
        y = (height - text_height) / 2
        draw.multiline_text(
            (x, y),
            label,
            fill=(255, 255, 255, 255),
            font=font,
            align="center",
            spacing=4,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)

    for asset_name, size in REQUIRED_ASSETS.items():
        source = custom_assets_dir / asset_name
        destination_path = destination / asset_name
        if source.exists():
            shutil.copy2(source, destination_path)
            print_status("✓", f"Using branded asset: {asset_name}")
            continue

        if asset_name == "SplashScreen.png":
            label = "WeChat Article\nSummarizer"
        elif size[0] <= 71:
            label = "WS"
        else:
            label = "WeChat\nSummarizer"
        generate_placeholder_png(destination_path, size, label)
        print_status("⚠", f"Generated placeholder asset: {asset_name}")

    icon_path = destination / "app.ico"
    if (custom_assets_dir / "app.ico").exists():
        shutil.copy2(custom_assets_dir / "app.ico", icon_path)
        print_status("✓", "Using branded app.ico")
    elif legacy_icon.exists():
        shutil.copy2(legacy_icon, icon_path)
        print_status("✓", "Using legacy assets/icons/app.ico")
    else:
        with Image.open(destination / "Square310x310Logo.png") as square_logo:
            square_logo.save(
                icon_path,
                format="ICO",
                sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
            )
        print_status("⚠", "Generated placeholder app.ico")

    return icon_path


def render_manifest(version: str) -> str:
    template = MANIFEST_TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "__PACKAGE_NAME__": PACKAGE_NAME,
        "__PUBLISHER__": PUBLISHER,
        "__VERSION__": version,
        "__DISPLAY_NAME__": DISPLAY_NAME,
        "__PUBLISHER_DISPLAY_NAME__": PUBLISHER_DISPLAY_NAME,
        "__DESCRIPTION__": DESCRIPTION,
        "__APP_EXECUTABLE__": APP_EXECUTABLE,
    }
    for placeholder, replacement in replacements.items():
        template = template.replace(placeholder, replacement)
    if "__" in template:
        raise RuntimeError("Manifest template still contains unreplaced placeholders")
    return template


def locate_existing_exe() -> Path | None:
    candidates = [
        DIST_DIR / APP_EXECUTABLE,
        DIST_DIR / "launcher.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    for candidate in DIST_DIR.glob("*.exe"):
        if candidate.exists():
            return candidate
    return None


def build_exe(icon_path: Path) -> Path:
    print_header("构建 EXE")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    PYINSTALLER_BUILD_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        APP_NAME,
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(PYINSTALLER_BUILD_DIR / "work"),
        "--specpath",
        str(PYINSTALLER_BUILD_DIR / "spec"),
        "--paths",
        str(SRC_DIR),
        "--add-data",
        f"{TRANSLATIONS_DIR}{os.pathsep}wechat_summarizer/presentation/gui/translations",
    ]

    if START_SILENT_VBS.exists():
        cmd.extend(["--add-data", f"{START_SILENT_VBS}{os.pathsep}."])
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])

    cmd.append(str(LAUNCHER))
    run_cmd(cmd)

    exe_path = DIST_DIR / APP_EXECUTABLE
    if not exe_path.exists():
        raise RuntimeError(f"PyInstaller did not create the expected executable: {exe_path}")
    print_status("✓", f"Built executable: {exe_path}")
    return exe_path


def prepare_msix_layout(exe_path: Path, version: str) -> Path:
    print_header("准备 MSIX 目录")
    if MSIX_STAGE_DIR.exists():
        shutil.rmtree(MSIX_STAGE_DIR)
    MSIX_STAGE_DIR.mkdir(parents=True)

    staged_exe = MSIX_STAGE_DIR / APP_EXECUTABLE
    shutil.copy2(exe_path, staged_exe)
    print_status("✓", f"Staged executable: {staged_exe.name}")

    staged_assets = MSIX_STAGE_DIR / "Assets"
    copy_or_generate_assets(staged_assets)

    manifest_output = MSIX_STAGE_DIR / "AppxManifest.xml"
    manifest_output.write_text(render_manifest(version), encoding="utf-8")
    print_status("✓", "Rendered AppxManifest.xml")

    return MSIX_STAGE_DIR


def create_msix_package(makeappx: Path, version: str) -> Path:
    print_header("创建 MSIX 包")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    msix_output = DIST_DIR / f"{PACKAGE_NAME}_{version}_{ARCHITECTURE}.msix"
    if msix_output.exists():
        msix_output.unlink()

    run_cmd(
        [
            str(makeappx),
            "pack",
            "/d",
            str(MSIX_STAGE_DIR),
            "/p",
            str(msix_output),
            "/o",
        ]
    )

    if not msix_output.exists():
        raise RuntimeError("makeappx completed without producing an MSIX file")

    size_mb = msix_output.stat().st_size / (1024 * 1024)
    print_status("✓", f"Created {msix_output.name} ({size_mb:.2f} MB)")
    return msix_output


def sign_package(msix_path: Path, signtool: Path | None, cert_path: Path, password_env: str) -> bool:
    print_header("签名 MSIX 包")
    if signtool is None:
        print_status("⚠", "signtool.exe not found; skipping signature")
        return False
    if not cert_path.exists():
        print_status("⚠", f"Certificate not found: {cert_path}")
        return False

    cmd = [
        str(signtool),
        "sign",
        "/fd",
        "SHA256",
        "/f",
        str(cert_path),
    ]

    password = os.environ.get(password_env, "")
    if password:
        cmd.extend(["/p", password])

    cmd.append(str(msix_path))
    result = run_cmd(cmd, check=False)
    if result.returncode != 0:
        if result.stdout.strip():
            print(result.stdout)
        if result.stderr.strip():
            print(result.stderr)
        print_status("⚠", "Package signing failed")
        return False

    print_status("✓", "Package signed successfully")
    return True


def clean_outputs() -> None:
    print_header("清理旧产物")
    for path in [PYINSTALLER_BUILD_DIR, MSIX_STAGE_DIR, MSIX_ASSET_CACHE_DIR]:
        if path.exists():
            shutil.rmtree(path)
            print_status("✓", f"Removed {path}")
    if DIST_DIR.exists():
        for msix_file in DIST_DIR.glob("*.msix"):
            msix_file.unlink()
            print_status("✓", f"Removed {msix_file}")


def check_environment(*, require_pyinstaller: bool) -> tuple[Path, Path | None]:
    print_header("环境检查")
    if sys.platform != "win32":
        raise RuntimeError("MSIX packaging is only supported on Windows")
    if not LAUNCHER.exists():
        raise RuntimeError(f"Launcher entrypoint not found: {LAUNCHER}")
    if not MANIFEST_TEMPLATE.exists():
        raise RuntimeError(f"Manifest template not found: {MANIFEST_TEMPLATE}")
    if not TRANSLATIONS_DIR.exists():
        raise RuntimeError(f"Translations directory not found: {TRANSLATIONS_DIR}")

    makeappx = find_windows_sdk_tool("makeappx.exe")
    if makeappx is None:
        raise RuntimeError("makeappx.exe not found; install the Windows SDK")
    print_status("✓", f"Found makeappx.exe: {makeappx}")

    signtool = find_windows_sdk_tool("signtool.exe")
    if signtool is None:
        print_status("⚠", "signtool.exe not found; unsigned packages can still be built")
    else:
        print_status("✓", f"Found signtool.exe: {signtool}")

    if require_pyinstaller:
        if not check_pyinstaller():
            raise RuntimeError("PyInstaller is not available in the current Python environment")
        print_status("✓", "PyInstaller is available")

    MSIX_ASSET_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    copy_or_generate_assets(MSIX_ASSET_CACHE_DIR)
    rendered_manifest = render_manifest(read_project_version())
    if APP_EXECUTABLE not in rendered_manifest:
        raise RuntimeError("Rendered manifest does not reference the expected executable name")
    print_status("✓", "Manifest template rendered successfully")
    return makeappx, signtool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an MSIX package for Microsoft Store validation")
    parser.add_argument("--skip-build", action="store_true", help="Reuse an existing EXE from dist/")
    parser.add_argument("--clean", action="store_true", help="Delete old build artifacts before packaging")
    parser.add_argument("--sign", action="store_true", help="Sign the generated MSIX package if a certificate is available")
    parser.add_argument(
        "--cert-path",
        default=str(PROJECT_ROOT / "cert.pfx"),
        help="Path to the .pfx certificate used for optional signing",
    )
    parser.add_argument(
        "--cert-password-env",
        default="CERT_PASSWORD",
        help="Environment variable that stores the .pfx password",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only validate prerequisites, generated assets, and manifest rendering",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    version = read_project_version()

    print(f"MSIX Build Script - {APP_NAME} v{version}")
    print(f"Project: {PROJECT_ROOT}")

    try:
        if args.clean:
            clean_outputs()

        makeappx, signtool = check_environment(require_pyinstaller=not args.skip_build)

        if args.check:
            print_header("检查完成")
            print_status("✓", "MSIX prerequisites and metadata are aligned")
            return 0

        if args.skip_build:
            exe_path = locate_existing_exe()
            if exe_path is None:
                raise RuntimeError("No existing executable found in dist/; remove --skip-build or build first")
            print_status("✓", f"Using existing executable: {exe_path}")
        else:
            icon_path = MSIX_ASSET_CACHE_DIR / "app.ico"
            exe_path = build_exe(icon_path)

        prepare_msix_layout(exe_path, version)
        msix_path = create_msix_package(makeappx, version)

        if args.sign:
            sign_package(
                msix_path,
                signtool,
                Path(args.cert_path),
                args.cert_password_env,
            )

        print_header("完成")
        print_status("✓", f"MSIX package: {msix_path}")
        print_status("ℹ", "Replace __PACKAGE_NAME__/__PUBLISHER__ values with your Partner Center identity before Store submission.")
        print_status("ℹ", "If you have real Store artwork, place it under msix/Assets/ to override the generated placeholders.")
        print_status("ℹ", f"Install locally for testing: Add-AppxPackage -Path {msix_path}")
        return 0
    except Exception as exc:
        print_status("❌", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
