#!/usr/bin/env python3
"""Check that tests use pytest tmp_path for filesystem side effects."""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS_ROOT = ROOT / "tests"

FORBIDDEN_TEMPFILE_NAMES = {
    "NamedTemporaryFile",
    "TemporaryDirectory",
    "SpooledTemporaryFile",
    "mkdtemp",
    "mkstemp",
}


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    message: str

    def format(self) -> str:
        return f"{self.path.relative_to(ROOT).as_posix()}:{self.line}: {self.message}"


class FilesystemIsolationVisitor(ast.NodeVisitor):
    """Detect test patterns that bypass pytest tmp_path isolation."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.violations: list[Violation] = []
        self._tempfile_aliases: set[str] = set()
        self._tempfile_functions: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "tempfile":
                self._tempfile_aliases.add(alias.asname or alias.name)
                self.violations.append(
                    Violation(
                        self.path,
                        node.lineno,
                        "use pytest tmp_path instead of importing tempfile in tests",
                    )
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "tempfile":
            for alias in node.names:
                imported_name = alias.asname or alias.name
                self._tempfile_functions.add(imported_name)
                self.violations.append(
                    Violation(
                        self.path,
                        node.lineno,
                        "use pytest tmp_path instead of importing tempfile helpers in tests",
                    )
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if _is_path_home_call(node):
            self.violations.append(
                Violation(
                    self.path,
                    node.lineno,
                    "patch home-dependent code to tmp_path instead of calling Path.home() directly",
                )
            )

        if _is_unscoped_click_isolated_filesystem(node):
            self.violations.append(
                Violation(
                    self.path,
                    node.lineno,
                    "pass tmp_path via temp_dir when using CliRunner.isolated_filesystem()",
                )
            )

        called_name = _called_name(node.func)
        if called_name in self._tempfile_functions:
            self.violations.append(
                Violation(
                    self.path,
                    node.lineno,
                    f"use tmp_path instead of tempfile.{called_name}()",
                )
            )
        elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if (
                node.func.value.id in self._tempfile_aliases
                and node.func.attr in FORBIDDEN_TEMPFILE_NAMES
            ):
                self.violations.append(
                    Violation(
                        self.path,
                        node.lineno,
                        f"use tmp_path instead of tempfile.{node.func.attr}()",
                    )
                )

        self.generic_visit(node)


def _called_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    return None


def _is_path_home_call(node: ast.Call) -> bool:
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "home"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "Path"
    )


def _is_unscoped_click_isolated_filesystem(node: ast.Call) -> bool:
    if not (isinstance(node.func, ast.Attribute) and node.func.attr == "isolated_filesystem"):
        return False
    return not node.args and not any(keyword.arg == "temp_dir" for keyword in node.keywords)


def check_tests(paths: list[Path] | None = None) -> list[Violation]:
    files = paths or sorted(TESTS_ROOT.rglob("*.py"))
    violations: list[Violation] = []

    for path in files:
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        visitor = FilesystemIsolationVisitor(path)
        visitor.visit(tree)
        violations.extend(visitor.violations)

    return violations


def main() -> int:
    violations = check_tests()
    if not violations:
        print("[test-filesystem-isolation] PASS")
        return 0

    print("[test-filesystem-isolation] FAIL")
    for violation in violations:
        print(violation.format())
    return 1


if __name__ == "__main__":
    sys.exit(main())
