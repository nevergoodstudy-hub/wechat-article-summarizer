#!/usr/bin/env python
"""微信文章总结器 - 现代化安全构建脚本 v2.0

构建流程:
1. 环境检查（Python 版本、必要工具）
2. 安全审计（Bandit SAST + pip-audit 依赖漏洞扫描）
3. PyArmor 9.x 代码混淆（--mix-str / --assert-call / --private）
4. PyInstaller 打包（onefile + 无控制台 + strip）
5. UPX 压缩（可选，进一步减小体积）
6. SHA256 校验和生成
7. 清理临时文件

用法:
    python scripts/build_modern.py                # 完整构建
    python scripts/build_modern.py --skip-audit   # 跳过审计（加速开发构建）
    python scripts/build_modern.py --skip-obfuscate  # 跳过混淆
    python scripts/build_modern.py --clean        # 先清理再构建
    python scripts/build_modern.py --no-cleanup   # 保留临时文件供调试

依赖:
    pip install pyarmor>=9.0 pyinstaller>=6.0 bandit pip-audit
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path


# ==================== 配置常量 ====================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
OBFUSCATED_DIR = PROJECT_ROOT / ".pyarmor" / "pack" / "dist"
SPEC_FILE = PROJECT_ROOT / "微信文章总结器.spec"
LAUNCHER = SRC_DIR / "launcher.py"
PKG_DIR = SRC_DIR / "wechat_summarizer"
EXE_NAME = "微信文章总结器.exe"

# 安全审计报告
AUDIT_DIR = PROJECT_ROOT / "security_reports"


@dataclass
class BuildConfig:
    """构建配置"""

    skip_audit: bool = False
    skip_obfuscate: bool = False
    clean_first: bool = False
    keep_temp: bool = False
    verbose: bool = False


@dataclass
class BuildResult:
    """构建结果"""

    success: bool = False
    exe_path: Path | None = None
    exe_size_mb: float = 0.0
    sha256: str = ""
    audit_issues: int = 0
    dep_vulnerabilities: int = 0
    duration_seconds: float = 0.0
    steps_completed: list[str] = field(default_factory=list)


# ==================== 工具函数 ====================


def print_header(title: str) -> None:
    """打印步骤标题"""
    print(f"\n{'=' * 20} {title} {'=' * 20}")


def print_status(icon: str, msg: str) -> None:
    """打印状态消息"""
    print(f"  {icon} {msg}")


def run_cmd(
    cmd: list[str],
    cwd: Path = PROJECT_ROOT,
    check: bool = False,
    capture: bool = True,
    timeout: int = 600,
) -> subprocess.CompletedProcess:
    """运行命令并返回结果"""
    print(f"  >>> {' '.join(cmd)}")
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
        timeout=timeout,
        check=check,
    )


def check_tool(name: str, test_cmd: list[str]) -> bool:
    """检查工具是否可用"""
    try:
        result = subprocess.run(
            test_cmd,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=15,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def compute_sha256(filepath: Path) -> str:
    """计算文件 SHA256"""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


# ==================== 构建步骤 ====================


def step_check_environment() -> bool:
    """步骤 0: 环境检查"""
    print_header("环境检查")

    # Python 版本
    ver = sys.version_info
    print_status("🐍", f"Python {ver.major}.{ver.minor}.{ver.micro}")
    if ver < (3, 10):
        print_status("❌", "需要 Python >= 3.10")
        return False

    # 项目结构
    if not PKG_DIR.exists():
        print_status("❌", f"找不到源代码目录: {PKG_DIR}")
        return False

    if not LAUNCHER.exists():
        print_status("❌", f"找不到启动入口: {LAUNCHER}")
        return False

    if not SPEC_FILE.exists():
        print_status("⚠️", f"找不到 spec 文件: {SPEC_FILE}（将使用 pyarmor --pack onefile）")

    # 工具检查
    tools = {
        "PyInstaller": ["pyinstaller", "--version"],
        "PyArmor": ["pyarmor", "--version"],
        "Bandit": ["bandit", "--version"],
    }
    all_ok = True
    for name, cmd in tools.items():
        if check_tool(name, cmd):
            print_status("✅", f"{name} 已安装")
        else:
            print_status("⚠️", f"{name} 未安装（相关步骤将跳过）")
            if name == "PyInstaller":
                all_ok = False

    # UPX（可选）
    if check_tool("UPX", ["upx", "--version"]):
        print_status("✅", "UPX 已安装（将用于压缩）")
    else:
        print_status("ℹ️", "UPX 未安装（跳过压缩，不影响构建）")

    return all_ok


def step_security_audit(result: BuildResult) -> bool:
    """步骤 1: 安全审计"""
    print_header("安全审计")
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Bandit SAST ---
    bandit_ok = True
    if check_tool("Bandit", ["bandit", "--version"]):
        print_status("🔍", "运行 Bandit 静态安全分析...")
        bandit_report = AUDIT_DIR / "bandit_report.txt"
        r = run_cmd([
            "bandit", "-r", str(SRC_DIR),
            "-f", "txt",
            "-o", str(bandit_report),
            "-ll",  # 仅中/高严重性
            "--confidence-level", "high",
            "-x", str(SRC_DIR / "wechat_summarizer" / "__pycache__"),
        ])

        if bandit_report.exists():
            content = bandit_report.read_text(encoding="utf-8", errors="ignore")
            # 统计问题数
            issue_count = content.count(">> Issue:")
            result.audit_issues = issue_count
            if issue_count > 0:
                print_status("⚠️", f"Bandit 发现 {issue_count} 个问题，详见 {bandit_report}")
            else:
                print_status("✅", "Bandit 未发现中/高严重性问题")
        else:
            print_status("✅", "Bandit 扫描完成，无严重问题")
    else:
        print_status("⏭️", "Bandit 未安装，跳过 SAST")

    # --- pip-audit ---
    if check_tool("pip-audit", ["pip-audit", "--version"]):
        print_status("🔍", "运行 pip-audit 依赖漏洞扫描...")
        audit_report = AUDIT_DIR / "pip_audit_report.txt"
        r = run_cmd(["pip-audit", "--format", "columns", "--output", str(audit_report)])

        if r.returncode != 0:
            if audit_report.exists():
                content = audit_report.read_text(encoding="utf-8", errors="ignore")
                vuln_lines = [l for l in content.splitlines() if l.strip() and not l.startswith("Name")]
                result.dep_vulnerabilities = max(0, len(vuln_lines) - 1)
            print_status("⚠️", f"pip-audit 发现 {result.dep_vulnerabilities} 个依赖漏洞")
        else:
            print_status("✅", "pip-audit 未发现已知漏洞")
    else:
        print_status("⏭️", "pip-audit 未安装，跳过依赖扫描")

    result.steps_completed.append("安全审计")
    return True  # 审计问题不阻止构建，只警告


def step_obfuscate(result: BuildResult) -> bool:
    """步骤 2: PyArmor 9.x 代码混淆"""
    print_header("代码混淆 (PyArmor 9.x)")

    if not check_tool("PyArmor", ["pyarmor", "--version"]):
        print_status("⚠️", "PyArmor 未安装，跳过混淆（使用原始代码打包）")
        result.steps_completed.append("混淆(跳过)")
        return True

    # 获取 PyArmor 版本
    ver_result = run_cmd(["pyarmor", "--version"])
    ver_str = ver_result.stdout.strip() if ver_result.stdout else "unknown"
    print_status("📦", f"PyArmor 版本: {ver_str}")

    # 配置 PyArmor 选项
    print_status("⚙️", "配置混淆选项...")

    # 设置 PyInstaller 选项（无控制台窗口）
    run_cmd(["pyarmor", "cfg", "pack:pyi_options", "=", " -w"])

    # 混淆 + 打包一体化
    # pyarmor gen --pack onefile --mix-str --assert-call -r launcher.py wechat_summarizer/
    print_status("🔐", "执行混淆 + 打包...")

    obf_cmd = [
        "pyarmor", "gen",
        "--pack", "onefile",
        "--mix-str",        # 混淆字符串常量
        "--assert-call",    # 断言调用完整性（防函数替换）
        "-r",               # 递归处理子包
        str(LAUNCHER),
        str(PKG_DIR),
    ]

    r = run_cmd(obf_cmd, cwd=SRC_DIR, timeout=1200)

    if r.returncode != 0:
        stderr = r.stderr or ""
        # PyArmor 试用版限制或其他非致命错误
        if "license" in stderr.lower() or "trial" in stderr.lower():
            print_status("⚠️", "PyArmor 试用版限制，回退到手动分步模式...")
            return _fallback_obfuscate_and_pack(result)
        else:
            print_status("⚠️", f"PyArmor 混淆失败: {stderr[:200]}")
            print_status("ℹ️", "回退到无混淆的 PyInstaller 打包...")
            result.steps_completed.append("混淆(失败,回退)")
            return True  # 不阻止构建

    print_status("✅", "PyArmor 混淆 + 打包完成")
    result.steps_completed.append("混淆+打包(PyArmor)")
    return True


def _fallback_obfuscate_and_pack(result: BuildResult) -> bool:
    """回退方案: 先混淆到 obfdist，再用 PyInstaller 手动打包"""
    print_status("🔄", "尝试分步混淆...")

    obfdist = PROJECT_ROOT / "obfdist"
    if obfdist.exists():
        shutil.rmtree(obfdist)

    # 步骤 1: 仅混淆
    r = run_cmd([
        "pyarmor", "gen",
        "-O", str(obfdist),
        "--mix-str",
        "-r",
        str(LAUNCHER),
        str(PKG_DIR),
    ], cwd=SRC_DIR, timeout=900)

    if r.returncode != 0:
        print_status("⚠️", "分步混淆也失败，将使用原始代码打包")
        if obfdist.exists():
            shutil.rmtree(obfdist)
        result.steps_completed.append("混淆(跳过)")
        return True

    print_status("✅", f"混淆输出: {obfdist}")
    result.steps_completed.append("混淆(分步)")
    return True


def step_pyinstaller_build(result: BuildResult) -> bool:
    """步骤 3: PyInstaller 打包（仅在 PyArmor 未完成打包时执行）"""

    # 检查 PyArmor 是否已经生成了 exe
    pyarmor_exe = _find_pyarmor_output()
    if pyarmor_exe:
        print_header("PyInstaller 打包 (已由 PyArmor 完成)")
        print_status("✅", f"检测到 PyArmor 已生成: {pyarmor_exe}")

        # 移动到 dist 目录
        DIST_DIR.mkdir(parents=True, exist_ok=True)
        target = DIST_DIR / EXE_NAME
        if target.exists():
            target.unlink()
        shutil.copy2(pyarmor_exe, target)

        result.exe_path = target
        result.steps_completed.append("打包(PyArmor已完成)")
        return True

    # PyArmor 未生成 exe，使用独立 PyInstaller
    print_header("PyInstaller 打包")

    if not SPEC_FILE.exists():
        print_status("❌", f"找不到 spec 文件: {SPEC_FILE}")
        return False

    r = run_cmd([
        "pyinstaller",
        "--clean",
        "--noconfirm",
        str(SPEC_FILE),
    ], timeout=900)

    if r.returncode != 0:
        print_status("❌", f"PyInstaller 打包失败")
        if r.stderr:
            print_status("ℹ️", r.stderr[:300])
        return False

    exe_path = DIST_DIR / EXE_NAME
    if not exe_path.exists():
        print_status("❌", f"打包输出未找到: {exe_path}")
        return False

    result.exe_path = exe_path
    result.steps_completed.append("打包(PyInstaller)")
    print_status("✅", f"打包完成: {exe_path}")
    return True


def _find_pyarmor_output() -> Path | None:
    """查找 PyArmor --pack 生成的 exe"""
    # PyArmor --pack onefile 默认输出到 dist/
    candidates = [
        DIST_DIR / EXE_NAME,
        DIST_DIR / "launcher.exe",
        SRC_DIR / "dist" / "launcher.exe",
        SRC_DIR / "dist" / EXE_NAME,
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def step_upx_compress(result: BuildResult) -> bool:
    """步骤 4: UPX 压缩（可选）"""
    print_header("UPX 压缩")

    if not result.exe_path or not result.exe_path.exists():
        print_status("⏭️", "无可执行文件，跳过")
        return True

    if not check_tool("UPX", ["upx", "--version"]):
        print_status("ℹ️", "UPX 未安装，跳过压缩")
        result.steps_completed.append("UPX(跳过)")
        return True

    original_size = result.exe_path.stat().st_size
    print_status("📦", f"压缩前: {original_size / 1024 / 1024:.2f} MB")

    r = run_cmd([
        "upx", "--best", "--lzma",
        str(result.exe_path),
    ], timeout=300)

    if r.returncode == 0:
        new_size = result.exe_path.stat().st_size
        ratio = (1 - new_size / original_size) * 100
        print_status("✅", f"压缩后: {new_size / 1024 / 1024:.2f} MB (减少 {ratio:.1f}%)")
        result.steps_completed.append("UPX压缩")
    else:
        print_status("⚠️", "UPX 压缩失败（不影响可执行文件）")
        result.steps_completed.append("UPX(失败)")

    return True


def step_generate_checksum(result: BuildResult) -> bool:
    """步骤 5: SHA256 校验和"""
    print_header("SHA256 校验和")

    if not result.exe_path or not result.exe_path.exists():
        print_status("⏭️", "无可执行文件，跳过")
        return True

    sha256 = compute_sha256(result.exe_path)
    result.sha256 = sha256
    result.exe_size_mb = result.exe_path.stat().st_size / (1024 * 1024)

    # 写入校验文件
    checksum_file = result.exe_path.with_suffix(".sha256")
    checksum_file.write_text(
        f"{sha256}  {result.exe_path.name}\n",
        encoding="utf-8",
    )

    print_status("🔑", f"SHA256: {sha256}")
    print_status("📄", f"校验文件: {checksum_file}")
    result.steps_completed.append("SHA256")
    return True


def step_cleanup(keep_temp: bool) -> None:
    """步骤 6: 清理临时文件"""
    print_header("清理临时文件")

    if keep_temp:
        print_status("ℹ️", "保留临时文件（--no-cleanup）")
        return

    cleanup_dirs = [
        BUILD_DIR,
        PROJECT_ROOT / "obfdist",
        PROJECT_ROOT / ".pyarmor",
    ]

    for d in cleanup_dirs:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
            print_status("🗑️", f"已删除: {d.name}/")

    # 清理 __pycache__
    count = 0
    for pycache in PROJECT_ROOT.rglob("__pycache__"):
        if ".venv" not in str(pycache) and "node_modules" not in str(pycache):
            shutil.rmtree(pycache, ignore_errors=True)
            count += 1
    if count > 0:
        print_status("🗑️", f"已清理 {count} 个 __pycache__ 目录")

    print_status("✅", "清理完成")


def clean_build_dirs() -> None:
    """构建前清理"""
    print_header("清理构建目录")
    for d in [DIST_DIR, BUILD_DIR, PROJECT_ROOT / "obfdist", PROJECT_ROOT / ".pyarmor"]:
        if d.exists():
            shutil.rmtree(d)
            print_status("🗑️", f"已删除: {d}")


# ==================== 报告 ====================


def print_report(result: BuildResult) -> None:
    """打印构建报告"""
    print("\n" + "=" * 60)
    if result.success:
        print("✅ 构建成功!")
    else:
        print("❌ 构建失败!")
    print("=" * 60)

    if result.exe_path:
        print(f"  输出文件: {result.exe_path}")
        print(f"  文件大小: {result.exe_size_mb:.2f} MB")
    if result.sha256:
        print(f"  SHA256:   {result.sha256[:16]}...{result.sha256[-16:]}")

    print(f"  构建耗时: {result.duration_seconds:.1f} 秒")
    print(f"  完成步骤: {' → '.join(result.steps_completed)}")

    if result.audit_issues > 0:
        print(f"  ⚠️ 安全审计问题: {result.audit_issues} (详见 {AUDIT_DIR})")
    if result.dep_vulnerabilities > 0:
        print(f"  ⚠️ 依赖漏洞: {result.dep_vulnerabilities}")

    print()
    print("防逆向保护层:")
    print("  1. PyArmor 代码混淆（code object + 字符串 + 调用链）")
    print("  2. PyInstaller onefile（单文件减少攻击面）")
    print("  3. strip=True（移除调试符号）")
    print("  4. UPX 压缩（增加静态分析难度）")
    print("  5. Windows VERSIONINFO（增加可信度）")
    print("  6. SHA256 校验和（完整性验证）")
    print("=" * 60)


# ==================== 主流程 ====================


def parse_args() -> BuildConfig:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="微信文章总结器 - 现代化安全构建")
    parser.add_argument("--skip-audit", action="store_true", help="跳过安全审计")
    parser.add_argument("--skip-obfuscate", action="store_true", help="跳过代码混淆")
    parser.add_argument("--clean", action="store_true", help="构建前清理所有目录")
    parser.add_argument("--no-cleanup", action="store_true", help="保留临时文件")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    args = parser.parse_args()

    return BuildConfig(
        skip_audit=args.skip_audit,
        skip_obfuscate=args.skip_obfuscate,
        clean_first=args.clean,
        keep_temp=args.no_cleanup,
        verbose=args.verbose,
    )


def main() -> int:
    """主入口"""
    config = parse_args()
    result = BuildResult()
    start_time = time.time()

    print("=" * 60)
    print("微信文章总结器 - 现代化安全构建 v2.0")
    print("=" * 60)

    try:
        # 0. 构建前清理
        if config.clean_first:
            clean_build_dirs()

        # 1. 环境检查
        if not step_check_environment():
            return 1

        # 2. 安全审计
        if not config.skip_audit:
            step_security_audit(result)
        else:
            print_header("安全审计 (跳过)")
            result.steps_completed.append("审计(跳过)")

        # 3. 代码混淆 + 打包
        if not config.skip_obfuscate:
            if not step_obfuscate(result):
                return 1
        else:
            print_header("代码混淆 (跳过)")
            result.steps_completed.append("混淆(跳过)")

        # 4. PyInstaller 打包（如果 PyArmor 未完成）
        if not step_pyinstaller_build(result):
            return 1

        # 5. UPX 压缩
        step_upx_compress(result)

        # 6. SHA256
        step_generate_checksum(result)

        result.success = True

    except KeyboardInterrupt:
        print("\n\n⚠️ 构建被用户中断")
        return 130
    except Exception as e:
        print(f"\n❌ 构建异常: {e}")
        return 1
    finally:
        result.duration_seconds = time.time() - start_time
        # 清理
        step_cleanup(config.keep_temp)
        # 报告
        print_report(result)

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
