#!/usr/bin/env python
"""安全构建脚本

该脚本执行以下步骤：
1. 运行安全审计 (Bandit)
2. 使用 PyArmor 混淆代码
3. 使用 PyInstaller 打包
4. 清理临时文件
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
OBFUSCATED_DIR = PROJECT_ROOT / "obfuscated_src"

# 需要混淆的关键模块
SENSITIVE_MODULES = [
    "wechat_summarizer/infrastructure/config/settings.py",
    "wechat_summarizer/infrastructure/adapters/summarizers",
    "wechat_summarizer/shared/utils/security.py",
]


def run_command(cmd: list[str], cwd: Path = PROJECT_ROOT) -> bool:
    """运行命令并返回是否成功"""
    print(f"\n>>> Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode == 0


def clean_build_dirs():
    """清理构建目录"""
    print("\n=== 清理构建目录 ===")
    for dir_path in [DIST_DIR, BUILD_DIR, OBFUSCATED_DIR]:
        if dir_path.exists():
            print(f"删除: {dir_path}")
            shutil.rmtree(dir_path)


def run_security_audit() -> bool:
    """运行安全审计"""
    print("\n=== 运行安全审计 (Bandit) ===")
    audit_file = PROJECT_ROOT / "security_audit.txt"
    
    # 运行 Bandit
    result = subprocess.run(
        ["bandit", "-r", str(SRC_DIR), "-f", "txt", "-o", str(audit_file), "-ll"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    
    # 检查是否有高/中严重性问题
    if audit_file.exists():
        content = audit_file.read_text(encoding="utf-8")
        if "High:" in content or "Medium:" in content:
            print("⚠️ 发现中高严重性安全问题，请查看 security_audit.txt")
            # 不阻止构建，只是警告
    
    print("✅ 安全审计完成")
    return True


def obfuscate_code() -> bool:
    """使用 PyArmor 混淆代码"""
    print("\n=== 代码混淆 (PyArmor) ===")
    
    # 创建输出目录
    OBFUSCATED_DIR.mkdir(parents=True, exist_ok=True)
    
    # 复制源代码到混淆目录
    src_copy = OBFUSCATED_DIR / "src"
    if src_copy.exists():
        shutil.rmtree(src_copy)
    shutil.copytree(SRC_DIR, src_copy)
    
    # PyArmor 8.x 新命令格式
    # 使用 gen 命令生成混淆代码
    try:
        result = subprocess.run(
            [
                "pyarmor", "gen",
                "--output", str(OBFUSCATED_DIR / "dist"),
                "--recursive",
                str(src_copy / "wechat_summarizer"),
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            print(f"⚠️ PyArmor 混淆警告: {result.stderr}")
            # 试用版可能有限制，使用原始代码继续
            print("使用原始代码继续构建...")
            return True
            
        print("✅ 代码混淆完成")
        return True
        
    except FileNotFoundError:
        print("⚠️ PyArmor 未安装或不可用，跳过混淆")
        return True


def build_with_pyinstaller() -> bool:
    """使用 PyInstaller 构建"""
    print("\n=== 构建可执行文件 (PyInstaller) ===")
    
    spec_file = PROJECT_ROOT / "微信文章总结器.spec"
    
    # 检查 spec 文件是否存在
    if not spec_file.exists():
        print("❌ 找不到 spec 文件")
        return False
    
    # 运行 PyInstaller
    if not run_command(["pyinstaller", "--clean", "--noconfirm", str(spec_file)]):
        print("❌ PyInstaller 构建失败")
        return False
    
    print("✅ 构建完成")
    return True


def verify_build():
    """验证构建结果"""
    print("\n=== 验证构建结果 ===")
    
    exe_path = DIST_DIR / "微信文章总结器.exe"
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"✅ 可执行文件: {exe_path}")
        print(f"   大小: {size_mb:.2f} MB")
        return True
    else:
        print("❌ 可执行文件未找到")
        return False


def cleanup():
    """清理临时文件"""
    print("\n=== 清理临时文件 ===")
    
    # 清理 PyInstaller build 目录
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print(f"已删除: {BUILD_DIR}")
    
    # 清理混淆临时目录
    if OBFUSCATED_DIR.exists():
        shutil.rmtree(OBFUSCATED_DIR)
        print(f"已删除: {OBFUSCATED_DIR}")
    
    # 清理 __pycache__ 目录
    for pycache in PROJECT_ROOT.rglob("__pycache__"):
        if ".venv" not in str(pycache):
            shutil.rmtree(pycache, ignore_errors=True)
    
    # 清理 .pyc 文件
    for pyc in PROJECT_ROOT.rglob("*.pyc"):
        if ".venv" not in str(pyc):
            pyc.unlink()
    
    print("✅ 清理完成")


def main():
    """主函数"""
    print("=" * 60)
    print("微信文章总结器 - 安全构建")
    print("=" * 60)
    
    # 检查是否在正确的目录
    if not (SRC_DIR / "wechat_summarizer").exists():
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 询问是否清理
    if "--clean" in sys.argv:
        clean_build_dirs()
    
    # 步骤执行
    steps = [
        ("安全审计", run_security_audit),
        ("代码混淆", obfuscate_code),
        ("PyInstaller 打包", build_with_pyinstaller),
        ("验证构建", verify_build),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{'='*20} {step_name} {'='*20}")
        if not step_func():
            print(f"\n❌ 构建在 '{step_name}' 步骤失败")
            sys.exit(1)
    
    # 清理（除非指定保留）
    if "--no-cleanup" not in sys.argv:
        cleanup()
    
    print("\n" + "=" * 60)
    print("✅ 构建成功完成!")
    print(f"   输出: {DIST_DIR / '微信文章总结器.exe'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
