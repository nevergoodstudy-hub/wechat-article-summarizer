#!/usr/bin/env python3
"""Check Clean Architecture import boundaries.

This guard intentionally starts with the highest-signal boundaries:
- domain must not import outer application/infrastructure/presentation/mcp/features/shared modules
- application must not import infrastructure/presentation/mcp/features modules
- MCP tool/resource modules must not import infrastructure adapters or containers;
  mcp/server.py remains the MCP composition root.
- Presentation must not import infrastructure, except for explicitly listed
  legacy files being migrated in later slices.

It uses Python AST imports instead of text search so comments and docstrings do
not create false positives.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src" / "wechat_summarizer"


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    source_layer: str
    imported_module: str

    def format(self) -> str:
        relative = self.path.relative_to(ROOT).as_posix()
        return (
            f"{relative}:{self.line}: {self.source_layer} layer must not import "
            f"{self.imported_module}"
        )


FORBIDDEN_PREFIXES: dict[str, tuple[str, ...]] = {
    "domain": (
        "wechat_summarizer.application",
        "wechat_summarizer.features",
        "wechat_summarizer.infrastructure",
        "wechat_summarizer.mcp",
        "wechat_summarizer.presentation",
        "wechat_summarizer.shared",
    ),
    "application": (
        "wechat_summarizer.features",
        "wechat_summarizer.infrastructure",
        "wechat_summarizer.mcp",
        "wechat_summarizer.presentation",
    ),
    "mcp_tooling": (
        "wechat_summarizer.infrastructure",
        "wechat_summarizer.presentation",
    ),
    "presentation": ("wechat_summarizer.infrastructure",),
}

MCP_TOOLING_PARTS = {"toolsets", "resources"}
PRESENTATION_INFRASTRUCTURE_ALLOWLIST: set[tuple[str, str]] = set()


def _source_layer(path: Path) -> str | None:
    try:
        relative = path.relative_to(SRC_ROOT)
    except ValueError:
        return None

    if not relative.parts:
        return None

    layer = relative.parts[0]
    if layer == "mcp" and len(relative.parts) > 1 and relative.parts[1] in MCP_TOOLING_PARTS:
        return "mcp_tooling"

    return layer if layer in FORBIDDEN_PREFIXES else None


def _absolute_module(current_package: str, module: str | None, level: int) -> str:
    if level == 0:
        return module or ""

    package_parts = current_package.split(".") if current_package else []
    keep = max(len(package_parts) - level + 1, 0)
    prefix = package_parts[:keep]
    if module:
        prefix.extend(module.split("."))
    return ".".join(part for part in prefix if part)


def _package_for_path(path: Path) -> str:
    relative = path.relative_to(SRC_ROOT).with_suffix("")
    parts = ["wechat_summarizer", *relative.parts]
    parts.pop()
    return ".".join(parts)


def _iter_imports(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    current_package = _package_for_path(path)
    imports: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            module = _absolute_module(current_package, node.module, node.level)
            if module:
                imports.append((node.lineno, module))

    return imports


def check_boundaries(paths: list[Path] | None = None) -> list[Violation]:
    """Return architecture boundary violations."""
    files = paths or sorted(SRC_ROOT.rglob("*.py"))
    violations: list[Violation] = []

    for path in files:
        source_layer = _source_layer(path)
        if source_layer is None:
            continue

        forbidden = FORBIDDEN_PREFIXES[source_layer]
        for line, imported_module in _iter_imports(path):
            if any(
                imported_module == prefix or imported_module.startswith(prefix + ".")
                for prefix in forbidden
            ) and not _is_allowlisted(path, imported_module):
                violations.append(
                    Violation(
                        path=path,
                        line=line,
                        source_layer=source_layer,
                        imported_module=imported_module,
                    )
                )

    return violations


def _is_allowlisted(path: Path, imported_module: str) -> bool:
    try:
        relative = path.relative_to(SRC_ROOT).as_posix()
    except ValueError:
        return False

    return (relative, imported_module) in PRESENTATION_INFRASTRUCTURE_ALLOWLIST


def main() -> int:
    violations = check_boundaries()
    if not violations:
        print("[architecture] PASS")
        return 0

    print("[architecture] FAIL")
    for violation in violations:
        print(violation.format())
    return 1


if __name__ == "__main__":
    sys.exit(main())
