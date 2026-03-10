"""测试环境导入优先级回归测试。"""

from __future__ import annotations

from pathlib import Path

import wechat_summarizer


def test_imports_repository_source_tree() -> None:
    """pytest 应优先导入当前仓库 src 下的源码。"""
    package_init = Path(wechat_summarizer.__file__).resolve()
    repo_src_dir = Path(__file__).resolve().parents[1] / "src"

    assert repo_src_dir in package_init.parents
