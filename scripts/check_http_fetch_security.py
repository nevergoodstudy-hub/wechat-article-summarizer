#!/usr/bin/env python3
"""Check that user-controlled outbound fetches use SSRF-safe helpers."""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src" / "wechat_summarizer"
CHECK_ROOTS = (
    SRC_ROOT / "infrastructure" / "adapters" / "scrapers",
    SRC_ROOT / "infrastructure" / "adapters" / "exporters",
)

ALLOWED_HTTPX_CLIENT_FILES = {
    "infrastructure/adapters/exporters/notion.py",
    "infrastructure/adapters/exporters/onenote.py",
}


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    message: str

    def format(self) -> str:
        return f"{self.path.relative_to(ROOT).as_posix()}:{self.line}: {self.message}"


class HttpFetchSecurityVisitor(ast.NodeVisitor):
    """Detect direct httpx clients in user-content fetch surfaces."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.violations: list[Violation] = []
        self._httpx_aliases: set[str] = {"httpx"}

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "httpx":
                self._httpx_aliases.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if _is_httpx_client_call(node, self._httpx_aliases):
            self.violations.append(
                Violation(
                    self.path,
                    node.lineno,
                    "use safe_fetch/safe_fetch_sync instead of direct httpx client fetches",
                )
            )
        elif _is_httpx_top_level_fetch(node, self._httpx_aliases):
            self.violations.append(
                Violation(
                    self.path,
                    node.lineno,
                    "use safe_fetch/safe_fetch_sync instead of top-level httpx fetches",
                )
            )

        self.generic_visit(node)


def _is_httpx_client_call(node: ast.Call, httpx_aliases: set[str]) -> bool:
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr in {"Client", "AsyncClient"}
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in httpx_aliases
    )


def _is_httpx_top_level_fetch(node: ast.Call, httpx_aliases: set[str]) -> bool:
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr in {"get", "post", "put", "patch", "delete", "request"}
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in httpx_aliases
    )


def _iter_files(paths: list[Path] | None = None) -> list[Path]:
    if paths is not None:
        return paths
    files: list[Path] = []
    for root in CHECK_ROOTS:
        files.extend(root.rglob("*.py"))
    return sorted(files)


def check_http_fetch_security(paths: list[Path] | None = None) -> list[Violation]:
    violations: list[Violation] = []

    for path in _iter_files(paths):
        if "__pycache__" in path.parts:
            continue
        try:
            relative = path.relative_to(SRC_ROOT).as_posix()
        except ValueError:
            relative = ""
        if relative in ALLOWED_HTTPX_CLIENT_FILES:
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        visitor = HttpFetchSecurityVisitor(path)
        visitor.visit(tree)
        violations.extend(visitor.violations)

    return violations


def main() -> int:
    violations = check_http_fetch_security()
    if not violations:
        print("[http-fetch-security] PASS")
        return 0

    print("[http-fetch-security] FAIL")
    for violation in violations:
        print(violation.format())
    return 1


if __name__ == "__main__":
    sys.exit(main())
