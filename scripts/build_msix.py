#!/usr/bin/env python
"""MSIX打包脚本 - 用于Microsoft应用商店发布

用法:
    python scripts/build_msix.py                    # 完整构建
    python scripts/build_msix.py --skip-build      # 仅创建包（假设EXE已存在）
    python scripts/build_msix.py --clean            # 清理后构建

前置要求:
1. 安装Windows SDK (包含makeappx.exe)
2. 安装代码签名证书 (用于正式发布)
3. Python 3.10+

构建流程:
1. 验证环境 (Python版本, Windows SDK)
2. 使用PyInstaller构建EXE
3. 创建Assets目录并生成所需图标
4. 复制EXE到MSIX目录
5. 使用makeappx创建MSIX包
6. (可选) 使用signtool签名

参考文档:
- https://learn.microsoft.com/zh-cn/windows/msix/
- https://learn.microsoft.com/zh-cn/windows/win32/appxpkg/make-appx-pack-manually
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ==================== 配置常量 ====================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
MSIX_DIR = PROJECT_ROOT / "msix"
ASSETS_DIR = MSIX_DIR / "Assets"
BUILD_DIR = PROJECT_ROOT / "build"

# 打包配置
APP_NAME = "WeChatArticleSummarizer"
EXE_NAME = f"{APP_NAME}.exe"
VERSION = os.environ.get("MSIX_VERSION", "2.4.2.0")
PUBLISHER = os.environ.get("MSIX_PUBLISHER", "CN=WeChatSummarizer")
PACKAGE_NAME = os.environ.get("MSIX_IDENTITY_NAME", "WeChatSummarizer")

# 需要复制到MSIX的资源
RESOURCES = [
    # 翻译文件
    ("src/wechat_summarizer/presentation/gui/translations", "translations"),
]


def print_header(title: str) -> None:
    print(f"\n{'=' * 20} {title} {'=' * 20}")


def print_status(icon: str, msg: str) -> None:
    text = f"  {icon} {msg}"
    try:
        print(text)
    except UnicodeEncodeError:
        safe = text.encode("gbk", errors="replace").decode("gbk", errors="replace")
        print(safe)


def run_cmd(cmd: list[str], cwd: Path = PROJECT_ROOT, check: bool = True) -> subprocess.CompletedProcess:
    print(f"  >>> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  [ERROR] Command failed: {result.stderr}")
        sys.exit(1)
    return result


def check_environment() -> bool:
    """检查构建环境"""
    print_header("环境检查")

    # Python版本检查
    py_version = sys.version_info
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 10):
        print_status("❌", f"Python 3.10+ required, got {py_version.major}.{py_version.minor}")
        return False
    print_status("✓", f"Python {py_version.major}.{py_version.minor}.{py_version.micro}")

    # Windows SDK检查
    sdk_paths = [
        Path(r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64"),
        Path(r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22000.0\x64"),
        Path(r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64"),
    ]

    makeappx = None
    for sdk_path in sdk_paths:
        candidate = sdk_path / "makeappx.exe"
        if candidate.exists():
            makeappx = candidate
            break

    if makeappx:
        print_status("✓", f"Windows SDK found: {makeappx.parent.name}")
    else:
        print_status("⚠", "Windows SDK not found - MSIX creation may fail")
        print_status("ℹ", "Install Windows SDK from: https://developer.microsoft.com/windows/downloads/windows-sdk/")

    return True


def build_exe() -> Path:
    """使用PyInstaller构建EXE"""
    print_header("构建EXE")

    # 使用现有的PyInstaller配置
    spec_file = PROJECT_ROOT / "微信文章总结器.spec"

    if not spec_file.exists():
        print_status("❌", f"Spec file not found: {spec_file}")
        sys.exit(1)

    print_status("ℹ", "Using PyInstaller spec: 微信文章总结器.spec")

    # 运行PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]

    run_cmd(cmd)

    # 查找生成的EXE
    exe_path = DIST_DIR / EXE_NAME

    if not exe_path.exists():
        # 尝试其他可能的名称
        for f in DIST_DIR.glob("*.exe"):
            if "wechat" in f.name.lower():
                exe_path = f
                break

    if not exe_path.exists():
        print_status("❌", f"EXE not found in {DIST_DIR}")
        sys.exit(1)

    print_status("✓", f"EXE built: {exe_path}")
    return exe_path


def _update_manifest_identity(manifest_path: Path) -> None:
    """更新 Manifest 中的 Identity 信息。"""
    tree = ET.parse(manifest_path)
    root = tree.getroot()

    identity = root.find("{http://schemas.microsoft.com/appx/manifest/foundation/windows10}Identity")
    if identity is None:
        print_status("❌", "AppxManifest.xml missing Identity node")
        sys.exit(1)

    identity.set("Name", PACKAGE_NAME)
    identity.set("Publisher", PUBLISHER)
    identity.set("Version", VERSION)

    tree.write(manifest_path, encoding="utf-8", xml_declaration=True)


def _extract_manifest_asset_paths(manifest_path: Path) -> list[Path]:
    """提取 Manifest 中声明的全部资源路径。"""
    tree = ET.parse(manifest_path)
    root = tree.getroot()

    asset_attrs = {
        "Logo",
        "Square150x150Logo",
        "Square44x44Logo",
        "Wide310x150Logo",
        "Square71x71Logo",
        "Square310x310Logo",
        "Image",
    }

    assets: list[Path] = []
    for element in root.iter():
        for attr_name, attr_value in element.attrib.items():
            if attr_name in asset_attrs and attr_value:
                normalized = attr_value.replace("\\", "/")
                assets.append(Path(normalized))

    return assets


def create_assets(strict: bool = False) -> None:
    """创建 Assets 目录并校验必需图标。"""
    print_header("创建Assets目录")

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    required_icons = [
        "StoreLogo.png",
        "Square44x44Logo.png",
        "Square71x71Logo.png",
        "Square150x150Logo.png",
        "Wide310x150Logo.png",
        "Square310x310Logo.png",
        "SplashScreen.png",
    ]

    icon_source_dir = PROJECT_ROOT / "assets" / "icons"
    missing_icons: list[str] = []

    for icon_name in required_icons:
        dest = ASSETS_DIR / icon_name
        if dest.exists():
            print_status("✓", f"{icon_name} exists")
            continue

        if icon_source_dir.exists():
            source = icon_source_dir / icon_name
            if source.exists():
                shutil.copy2(source, dest)
                print_status("✓", f"Copied {icon_name}")
                continue

        missing_icons.append(icon_name)
        print_status("⚠", f"{icon_name} not found")

    if missing_icons and strict:
        print_status("❌", f"Strict mode: missing required assets: {', '.join(missing_icons)}")
        sys.exit(1)


def prepare_msix_directory(exe_path: Path, strict: bool = False) -> None:
    """准备 MSIX 目录结构并校验 Manifest 资产一致性。"""
    print_header("准备MSIX目录")

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)

    dest_exe = BUILD_DIR / EXE_NAME
    shutil.copy2(exe_path, dest_exe)
    print_status("✓", f"Copied {EXE_NAME}")

    if ASSETS_DIR.exists():
        dest_assets = BUILD_DIR / "Assets"
        shutil.copytree(ASSETS_DIR, dest_assets)
        print_status("✓", "Copied Assets")

    manifest_src = MSIX_DIR / "AppxManifest.xml"
    manifest_dest = BUILD_DIR / "AppxManifest.xml"
    shutil.copy2(manifest_src, manifest_dest)
    _update_manifest_identity(manifest_dest)
    print_status("✓", "Copied AppxManifest.xml")

    missing_manifest_assets: list[str] = []
    for rel_path in _extract_manifest_asset_paths(manifest_dest):
        expected = BUILD_DIR / rel_path
        if not expected.exists():
            missing_manifest_assets.append(rel_path.as_posix())

    if missing_manifest_assets:
        print_status("❌", "Manifest references missing assets:")
        for missing in missing_manifest_assets:
            print_status("•", missing)
        if strict:
            sys.exit(1)

    for src_pattern, dest_name in RESOURCES:
        src_dir = PROJECT_ROOT / src_pattern
        if src_dir.exists():
            dest_dir = BUILD_DIR / dest_name
            shutil.copytree(src_dir, dest_dir)
            print_status("✓", f"Copied {src_pattern}")


def create_msix_package() -> Path:
    """创建MSIX包"""
    print_header("创建MSIX包")

    # 查找makeappx.exe
    makeappx_paths = [
        Path(r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\makeappx.exe"),
        Path(r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22000.0\x64\makeappx.exe"),
        Path(r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\makeappx.exe"),
    ]

    makeappx = None
    for path in makeappx_paths:
        if path.exists():
            makeappx = path
            break

    if not makeappx:
        print_status("❌", "makeappx.exe not found")
        print_status("ℹ", "Please install Windows SDK")
        sys.exit(1)

    # 输出MSIX路径
    msix_output = DIST_DIR / f"{PACKAGE_NAME}_{VERSION}_x64.msix"

    # 删除旧的MSIX
    if msix_output.exists():
        msix_output.unlink()

    # 创建MSIX
    cmd = [
        str(makeappx),
        "pack",
        "/d", str(BUILD_DIR),
        "/p", str(msix_output),
        "/nv",  # 非verbose
        "/o",   # 覆盖输出
    ]

    run_cmd(cmd)

    if msix_output.exists():
        size_mb = msix_output.stat().st_size / (1024 * 1024)
        print_status("✓", f"MSIX created: {msix_output}")
        print_status("ℹ", f"Size: {size_mb:.2f} MB")
        return msix_output
    else:
        print_status("❌", "MSIX creation failed")
        sys.exit(1)


def sign_package(msix_path: Path) -> bool:
    """签名MSIX包（可选）"""
    print_header("签名MSIX包")

    # 查找signtool.exe
    signtool_paths = [
        Path(r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"),
        Path(r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22000.0\x64\signtool.exe"),
    ]

    signtool = None
    for path in signtool_paths:
        if path.exists():
            signtool = path
            break

    if not signtool:
        print_status("⚠", "signtool.exe not found - skipping signature")
        print_status("ℹ", "For Microsoft Store submission, you need:")
        print_status("ℹ", "  1. Microsoft Partner Center account")
        print_status("ℹ", "  2. Code signing certificate")
        return False

    # 检查是否有签名证书
    cert_path = PROJECT_ROOT / "cert.pfx"
    cert_password = os.environ.get("CERT_PASSWORD", "")

    if not cert_path.exists():
        print_status("⚠", "Signing certificate not found - skipping signature")
        print_status("ℹ", f"Place your certificate at: {cert_path}")
        print_status("ℹ", "For testing, you can create a self-signed certificate:")
        print_status("ℹ", "  New-SelfSignedCertificate -Type Custom -Subject 'CN=WeChatSummarizer' -KeyUsage DigitalSignature -FriendlyName 'WeChatSummarizer' -CertStoreLocation 'Cert:\\CurrentUser\\My'")
        return False

    # 签名
    cmd = [
        str(signtool),
        "sign",
        "/fd", "SHA256",
        "/a",  # auto select cert
        str(msix_path),
    ]

    # 使用证书文件
    if cert_password:
        cmd.extend(["/f", str(cert_path), "/p", cert_password])
    else:
        cmd.append("/a")

    result = run_cmd(cmd, check=False)

    if result.returncode == 0:
        print_status("✓", "Package signed successfully")
        return True
    else:
        print_status("⚠", f"Signing failed: {result.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Build MSIX package for Microsoft Store")
    parser.add_argument("--skip-build", action="store_true", help="Skip EXE build")
    parser.add_argument("--clean", action="store_true", help="Clean before build")
    parser.add_argument("--sign", action="store_true", help="Sign the package")
    parser.add_argument(
        "--store",
        action="store_true",
        help="Strict mode for Partner Center submission (fail on missing assets)",
    )
    args = parser.parse_args()

    print(f"MSIX Build Script - {APP_NAME} v{VERSION}")
    print(f"Project: {PROJECT_ROOT}")

    # 环境检查
    if not check_environment():
        sys.exit(1)

    # 清理
    if args.clean:
        print_header("清理")
        if BUILD_DIR.exists():
            shutil.rmtree(BUILD_DIR)
        if DIST_DIR.exists():
            for f in DIST_DIR.glob("*.msix"):
                f.unlink()
        print_status("✓", "Cleaned")

    # 构建EXE
    exe_path = None
    if args.skip_build:
        # 查找现有EXE
        for f in DIST_DIR.glob("*.exe"):
            if "wechat" in f.name.lower():
                exe_path = f
                break

        if not exe_path:
            print_status("❌", "No existing EXE found")
            sys.exit(1)
        print_status("✓", f"Using existing EXE: {exe_path}")
    else:
        exe_path = build_exe()

    # 创建Assets
    create_assets(strict=args.store)

    # 准备目录
    prepare_msix_directory(exe_path, strict=args.store)

    # 创建MSIX
    msix_path = create_msix_package()

    # 签名
    if args.sign:
        sign_package(msix_path)

    print_header("完成!")
    print_status("✓", f"MSIX package: {msix_path}")
    print_status("ℹ", "To install locally (for testing):")
    print_status("ℹ", f"  Add-AppxPackage -Path {msix_path}")
    print_status("ℹ", "")
    print_status("ℹ", "To submit to Microsoft Store:")
    print_status("ℹ", "  1. Go to Microsoft Partner Center")
    print_status("ℹ", "  2. Create a new submission")
    print_status("ℹ", "  3. Upload the MSIX package")
    print_status("ℹ", "  4. Complete certification process")


if __name__ == "__main__":
    main()
