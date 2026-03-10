#!/usr/bin/env python3
"""检查 domain 层是否越界依赖外层模块。"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOMAIN_DIR = REPO_ROOT / "src" / "wechat_summarizer" / "domain"
FORBIDDEN_ABSOLUTE_PREFIXES = (
    "wechat_summarizer.infrastructure",
    "wechat_summarizer.presentation",
    "wechat_summarizer.mcp",
)
FORBIDDEN_RELATIVE_PREFIXES = ("infrastructure", "presentation", "mcp")


def _is_forbidden_import(node: ast.ImportFrom | ast.Import) -> str | None:
    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.name.startswith(FORBIDDEN_ABSOLUTE_PREFIXES):
                return alias.name
        return None

    module = node.module or ""
    if module.startswith(FORBIDDEN_ABSOLUTE_PREFIXES):
        return module
    if not module and node.level > 0:
        for alias in node.names:
            if alias.name.startswith(FORBIDDEN_RELATIVE_PREFIXES):
                return f"{'.' * node.level}{alias.name}"
    if node.level > 0 and module.startswith(FORBIDDEN_RELATIVE_PREFIXES):
        return f"{'.' * node.level}{module}"
    return None


def find_domain_boundary_violations(domain_dir: Path = DOMAIN_DIR) -> list[str]:
    """返回 domain 目录下的所有越界导入。"""
    violations: list[str] = []

    for py_file in domain_dir.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                forbidden = _is_forbidden_import(node)
                if forbidden is None:
                    continue
                relative_path = py_file.relative_to(REPO_ROOT)
                violations.append(f"{relative_path}:{node.lineno}: {forbidden}")

    return violations


def main() -> int:
    violations = find_domain_boundary_violations()
    if violations:
        print("Domain boundary violations found:")
        for violation in violations:
            print(f"  {violation}")
        return 1

    print("No domain boundary violations found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
