#!/usr/bin/env python3
"""Unified quality gate entry for local and CI usage."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GateError(RuntimeError):
    pass


def run(cmd: list[str], *, allow_nonzero: set[int] | None = None) -> int:
    allow_nonzero = allow_nonzero or set()
    print(f"\n[quality-gate] >>> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT, check=False)
    if result.returncode != 0 and result.returncode not in allow_nonzero:
        raise GateError(f"Command failed ({result.returncode}): {' '.join(cmd)}")
    return result.returncode


def run_lint() -> None:
    run(["ruff", "check", "src/", "tests/"])
    run(["ruff", "format", "--check", "src/", "tests/"])


def run_mypy() -> None:
    run(["mypy", "src/wechat_summarizer", "--ignore-missing-imports"])


def run_tests() -> None:
    run(
        [
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
    run(["pip-audit", "--desc", "on"])
    run(["bandit", "-r", "src/wechat_summarizer", "-ll"])


def run_security_smoke() -> None:
    """Run focused security smoke tests if they exist.

    pytest exits with code 5 when no tests are collected. We treat that as pass
    for now to keep rollout incremental while still enabling a unified entry.
    """

    rc = run(["pytest", "tests/", "-q", "-k", "ssrf or mcp"], allow_nonzero={5})
    if rc == 5:
        print("[quality-gate] No SSRF/MCP smoke tests collected yet; treated as pass.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unified quality gate runner")
    parser.add_argument(
        "--mode",
        choices=["all", "lint", "mypy", "test", "security", "security-smoke"],
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
        elif args.mode == "test":
            run_tests()
        elif args.mode == "security":
            run_security()
        elif args.mode == "security-smoke":
            run_security_smoke()
        else:
            run_lint()
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
