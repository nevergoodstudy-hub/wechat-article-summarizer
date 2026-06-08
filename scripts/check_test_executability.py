#!/usr/bin/env python3
"""Check the default test suite executability ratio."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--min-ratio",
        type=float,
        default=0.90,
        help="Minimum default executable test ratio. Default: 0.90",
    )
    return parser.parse_args()


def _collect_count(extra_args: list[str] | None = None) -> int:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "--collect-only",
            "-q",
            *(extra_args or []),
        ],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode not in {0, 5}:
        print(result.stdout)
        raise SystemExit(result.returncode)

    collected = 0
    for line in result.stdout.splitlines():
        if " tests collected (" in line and " deselected)" in line:
            prefix = line.split(" tests collected (", 1)[0]
            collected = int(prefix.rsplit("/", 1)[0].rsplit(maxsplit=1)[-1])
        elif " tests collected" in line:
            collected = int(line.split(" tests collected", 1)[0].rsplit(maxsplit=1)[-1])

    return collected


def main() -> int:
    args = parse_args()
    collected = _collect_count()
    executable = _collect_count(["-m", "not integration"])

    if collected == 0:
        print("[test-executability] FAIL: no tests collected")
        return 1

    skipped = collected - executable
    ratio = executable / collected
    print(
        "[test-executability] "
        f"executable={executable} collected={collected} skipped={skipped} ratio={ratio:.1%}"
    )

    if ratio < args.min_ratio:
        print(
            f"[test-executability] FAIL: ratio {ratio:.1%} is below required {args.min_ratio:.1%}"
        )
        return 1

    print("[test-executability] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
