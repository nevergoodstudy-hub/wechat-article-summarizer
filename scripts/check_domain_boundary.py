#!/usr/bin/env python3
"""Check the domain layer import boundary.

The domain layer is the center of the Clean/Hexagonal Architecture. It must
not depend on outer project layers; cross-layer collaboration belongs behind
application ports or other inward-facing abstractions.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src" / "wechat_summarizer"
DOMAIN_ROOT = SRC_ROOT / "domain"

FORBIDDEN_PROJECT_PREFIXES = (
    "wechat_summarizer.application",
    "wechat_summarizer.features",
    "wechat_summarizer.infrastructure",
    "wechat_summarizer.mcp",
    "wechat_summarizer.presentation",
    "wechat_summarizer.shared",
)


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    imported_module: str

    def format(self) -> str:
        try:
            relative = self.path.relative_to(ROOT).as_posix()
        except ValueError:
            relative = self.path.as_posix()
        return f"{relative}:{self.line}: domain layer must not import {self.imported_module}"


def _package_for_path(path: Path) -> str:
    relative = path.relative_to(SRC_ROOT).with_suffix("")
    parts = ["wechat_summarizer", *relative.parts]
    parts.pop()
    return ".".join(parts)


def _absolute_module(current_package: str, module: str | None, level: int) -> str:
    if level == 0:
        return module or ""

    package_parts = current_package.split(".") if current_package else []
    keep = max(len(package_parts) - level + 1, 0)
    prefix = package_parts[:keep]
    if module:
        prefix.extend(module.split("."))
    return ".".join(part for part in prefix if part)


def _iter_imports(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    current_package = _package_for_path(path)
    imports: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = _absolute_module(current_package, node.module, node.level)
            if module:
                imports.append((node.lineno, module))

    return imports


def _is_forbidden_domain_import(imported_module: str) -> bool:
    return any(
        imported_module == prefix or imported_module.startswith(prefix + ".")
        for prefix in FORBIDDEN_PROJECT_PREFIXES
    )


def check_domain_boundary(paths: list[Path] | None = None) -> list[Violation]:
    """Return domain-layer import boundary violations."""
    files = paths or sorted(DOMAIN_ROOT.rglob("*.py"))
    violations: list[Violation] = []

    for path in files:
        if "__pycache__" in path.parts:
            continue
        for line, imported_module in _iter_imports(path):
            if _is_forbidden_domain_import(imported_module):
                violations.append(Violation(path=path, line=line, imported_module=imported_module))

    return violations


def main() -> int:
    violations = check_domain_boundary()
    if not violations:
        print("[domain-boundary] PASS")
        return 0

    print("[domain-boundary] FAIL")
    for violation in violations:
        print(violation.format())
    return 1


if __name__ == "__main__":
    sys.exit(main())
