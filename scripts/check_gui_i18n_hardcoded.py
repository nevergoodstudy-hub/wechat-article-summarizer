#!/usr/bin/env python3
"""Baseline guard for GUI i18n hardcoded user-facing strings."""

from __future__ import annotations

import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

ROOT = Path(__file__).resolve().parents[1]
GUI_SRC = ROOT / "src" / "wechat_summarizer" / "presentation" / "gui"
EN_TRANSLATIONS = GUI_SRC / "translations" / "en.json"

USER_VISIBLE_KEYWORDS: Final[frozenset[str]] = frozenset(
    {
        "text",
        "placeholder_text",
        "title",
        "message",
        "detail",
        "description",
        "tooltip",
        "label",
        "button_text",
    }
)
EXCLUDED_PARTS: Final[frozenset[str]] = frozenset({"translations"})

# These budgets are the current legacy baseline. Lower them as strings are
# migrated to tr(...); the guard prevents new net hardcoding from landing.
MAX_HARDCODED_VISIBLE_STRINGS: Final[int] = 174
MAX_UNTRANSLATABLE_TR_CALLS: Final[int] = 9


@dataclass(frozen=True)
class I18nViolation:
    path: Path
    line: int
    message: str

    def format(self) -> str:
        return f"{self.path.relative_to(ROOT)}:{self.line}: {self.message}"


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _looks_like_visible_english(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 3:
        return False
    if stripped.startswith(("#", ".", "/", "\\", "http://", "https://")):
        return False
    return any(char.isalpha() for char in stripped) and any(char.isspace() for char in stripped)


def _is_user_visible_literal(text: str) -> bool:
    stripped = text.strip()
    return bool(stripped) and (_contains_cjk(stripped) or _looks_like_visible_english(stripped))


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _iter_python_files(gui_src: Path) -> list[Path]:
    return sorted(
        path
        for path in gui_src.rglob("*.py")
        if not any(part in EXCLUDED_PARTS for part in path.relative_to(gui_src).parts)
    )


def scan_gui_i18n(
    *,
    gui_src: Path = GUI_SRC,
    en_translations: Path = EN_TRANSLATIONS,
) -> tuple[list[I18nViolation], list[I18nViolation]]:
    hardcoded: list[I18nViolation] = []
    untranslatable: list[I18nViolation] = []
    translations = json.loads(en_translations.read_text(encoding="utf-8"))

    for path in _iter_python_files(gui_src):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            call_name = _call_name(node.func)
            if call_name == "tr" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if arg.value not in translations:
                        untranslatable.append(
                            I18nViolation(
                                path,
                                arg.lineno,
                                f"tr literal missing from en.json: {arg.value!r}",
                            )
                        )
                elif isinstance(arg, (ast.JoinedStr, ast.BinOp)):
                    untranslatable.append(
                        I18nViolation(path, getattr(arg, "lineno", node.lineno), "dynamic tr(...) key")
                    )

            for keyword in node.keywords:
                if keyword.arg not in USER_VISIBLE_KEYWORDS:
                    continue
                value = keyword.value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    text = value.value
                    if _is_user_visible_literal(text):
                        hardcoded.append(
                            I18nViolation(
                                path,
                                value.lineno,
                                f"hardcoded {keyword.arg}= literal: {text[:80]!r}",
                            )
                        )

    return hardcoded, untranslatable


def check_gui_i18n() -> list[str]:
    hardcoded, untranslatable = scan_gui_i18n()
    failures: list[str] = []
    if len(hardcoded) > MAX_HARDCODED_VISIBLE_STRINGS:
        failures.append(
            "hardcoded GUI string budget exceeded: "
            f"{len(hardcoded)} > {MAX_HARDCODED_VISIBLE_STRINGS}"
        )
    if len(untranslatable) > MAX_UNTRANSLATABLE_TR_CALLS:
        failures.append(
            "untranslatable tr(...) budget exceeded: "
            f"{len(untranslatable)} > {MAX_UNTRANSLATABLE_TR_CALLS}"
        )
    return failures


def main() -> int:
    failures = check_gui_i18n()
    if failures:
        print("[gui-i18n] FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    hardcoded, untranslatable = scan_gui_i18n()
    print(
        "[gui-i18n] PASS "
        f"(hardcoded={len(hardcoded)}/{MAX_HARDCODED_VISIBLE_STRINGS}, "
        f"untranslatable_tr={len(untranslatable)}/{MAX_UNTRANSLATABLE_TR_CALLS})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
