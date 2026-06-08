#!/usr/bin/env python3
"""Unified quality gate entry for local and CI usage."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PIP_AUDIT_CACHE = ROOT / ".cache" / "pip-audit"


class GateError(RuntimeError):
    pass


def run(cmd: list[str], *, allow_nonzero: set[int] | None = None) -> int:
    allow_nonzero = allow_nonzero or set()
    print(f"\n[quality-gate] >>> {' '.join(cmd)}")
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(SRC) if not existing_pythonpath else os.pathsep.join([str(SRC), existing_pythonpath])
    )
    result = subprocess.run(cmd, cwd=ROOT, env=env, check=False)
    if result.returncode != 0 and result.returncode not in allow_nonzero:
        raise GateError(f"Command failed ({result.returncode}): {' '.join(cmd)}")
    return result.returncode


def run_lint() -> None:
    run([sys.executable, "-m", "ruff", "check", "src/", "tests/"])
    run([sys.executable, "-m", "ruff", "format", "--check", "src/", "tests/"])


def run_mypy() -> None:
    run([sys.executable, "-m", "mypy", "src/wechat_summarizer", "--ignore-missing-imports"])


def run_architecture() -> None:
    run([sys.executable, "scripts/check_architecture_boundaries.py"])
    run([sys.executable, "scripts/check_domain_boundary.py"])
    run([sys.executable, "scripts/check_http_fetch_security.py"])
    run([sys.executable, "scripts/check_test_filesystem_isolation.py"])
    run([sys.executable, "scripts/check_ci_python_matrix.py"])
    run([sys.executable, "scripts/check_mypy_core_strictness.py"])


def run_test_executability() -> None:
    run([sys.executable, "scripts/check_test_executability.py", "--min-ratio", "0.90"])


def run_tests() -> None:
    run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "--cov=src/wechat_summarizer",
            "--cov-report=xml",
            "--cov-report=term",
            "--timeout=90",
            "-v",
        ]
    )


def run_security() -> None:
    run(
        [
            sys.executable,
            "-m",
            "pip_audit",
            ".",
            "--desc",
            "on",
            "--progress-spinner",
            "off",
            "--cache-dir",
            str(PIP_AUDIT_CACHE),
        ]
    )
    run([sys.executable, "-m", "bandit", "-r", "src/wechat_summarizer", "-ll"])


def run_security_smoke() -> None:
    """Run focused security smoke tests if they exist.

    pytest exits with code 5 when no tests are collected. We treat that as pass
    for now to keep rollout incremental while still enabling a unified entry.
    """

    rc = run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "-k", "ssrf or mcp"], allow_nonzero={5}
    )
    if rc == 5:
        print("[quality-gate] No SSRF/MCP smoke tests collected yet; treated as pass.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unified quality gate runner")
    parser.add_argument(
        "--mode",
        choices=["all", "lint", "mypy", "architecture", "test", "security", "security-smoke"],
        default="all",
        help="Which gate to run",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if args.mode == "lint":
            run_lint()
        elif args.mode == "mypy":
            run_mypy()
        elif args.mode == "architecture":
            run_architecture()
            run_test_executability()
        elif args.mode == "test":
            run_tests()
        elif args.mode == "security":
            run_security()
        elif args.mode == "security-smoke":
            run_security_smoke()
        else:
            run_lint()
            run_architecture()
            run_test_executability()
            run_mypy()
            run_tests()
            run_security_smoke()
        print("\n[quality-gate] PASS")
        return 0
    except GateError as exc:
        print(f"\n[quality-gate] FAIL: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
