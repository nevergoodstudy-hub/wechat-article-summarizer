"""Composition tests for split single-process GUI ViewModel helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from wechat_summarizer.domain.entities import Article, Summary
from wechat_summarizer.domain.entities.summary import SummaryMethod
from wechat_summarizer.domain.value_objects import ArticleContent, ArticleURL
from wechat_summarizer.presentation.gui.viewmodels import (
    ArticleDisplayModel,
    SummaryDisplayModel,
)
from wechat_summarizer.presentation.gui.viewmodels import (
    SingleProcessViewModel as PackageSingleProcessViewModel,
)
from wechat_summarizer.presentation.gui.viewmodels import (
    single_process_viewmodel as viewmodel_module,
)
from wechat_summarizer.presentation.gui.viewmodels.single_process_availability import (
    get_available_exporters,
    get_available_summarizers,
)
from wechat_summarizer.presentation.gui.viewmodels.single_process_mapping import (
    convert_article,
    convert_summary,
)
from wechat_summarizer.presentation.gui.viewmodels.single_process_models import (
    ArticleDisplayModel as SplitArticleDisplayModel,
)
from wechat_summarizer.presentation.gui.viewmodels.single_process_models import (
    SummaryDisplayModel as SplitSummaryDisplayModel,
)
from wechat_summarizer.presentation.gui.viewmodels.single_process_viewmodel import (
    ArticleDisplayModel as CompatArticleDisplayModel,
)
from wechat_summarizer.presentation.gui.viewmodels.single_process_viewmodel import (
    SingleProcessViewModel,
)
from wechat_summarizer.presentation.gui.viewmodels.single_process_viewmodel import (
    SummaryDisplayModel as CompatSummaryDisplayModel,
)


@pytest.mark.unit
def test_single_process_viewmodel_keeps_compatibility_exports() -> None:
    assert PackageSingleProcessViewModel is SingleProcessViewModel
    assert viewmodel_module.ArticleDisplayModel is SplitArticleDisplayModel
    assert viewmodel_module.SummaryDisplayModel is SplitSummaryDisplayModel
    assert ArticleDisplayModel is SplitArticleDisplayModel
    assert SummaryDisplayModel is SplitSummaryDisplayModel
    assert CompatArticleDisplayModel is SplitArticleDisplayModel
    assert CompatSummaryDisplayModel is SplitSummaryDisplayModel


@pytest.mark.unit
def test_single_process_mapping_preserves_article_display_conversion() -> None:
    content = ArticleContent(
        html="<p>body</p>",
        text="x" * 510,
    )
    article = Article(
        url=ArticleURL("https://mp.weixin.qq.com/s/example"),
        title="标题",
        author=None,
        account_name=None,
        publish_time=datetime(2026, 1, 2, 3, 4),
        content=content,
    )

    display = convert_article(article)

    assert display.url == "https://mp.weixin.qq.com/s/example"
    assert display.title == "标题"
    assert display.author == ""
    assert display.account_name == ""
    assert display.publish_time == "2026-01-02 03:04"
    assert display.content_preview == ("x" * 500) + "..."
    assert display.word_count == 510
    assert SingleProcessViewModel._convert_article(article) == display


@pytest.mark.unit
def test_single_process_mapping_preserves_summary_display_conversion() -> None:
    summary = Summary(
        content="摘要正文",
        method=SummaryMethod.OPENAI,
        model_name="gpt-test",
        key_points=("point-a", "point-b"),
        tags=("tag-a",),
        created_at=datetime(2026, 1, 2, 3, 4, 5),
    )

    display = convert_summary(summary)

    assert display.content == "摘要正文"
    assert display.key_points == ["point-a", "point-b"]
    assert display.tags == ["tag-a"]
    assert display.method == "openai"
    assert display.model_name == "gpt-test"
    assert display.generated_at == "2026-01-02 03:04:05"
    assert SingleProcessViewModel._convert_summary(summary) == display


@pytest.mark.unit
def test_single_process_availability_preserves_order_and_reasons() -> None:
    container = SimpleNamespace(
        summarizers={"simple": object(), "openai": object()},
        exporters={"html": object(), "onenote": object()},
    )

    assert get_available_summarizers(container) == [
        ("simple", True, ""),
        ("ollama", False, "Ollama 服务不可用"),
        ("openai", True, ""),
        ("anthropic", False, "缺少 ANTHROPIC_API_KEY"),
        ("zhipu", False, "缺少 ZHIPU_API_KEY"),
    ]
    assert get_available_exporters(container) == [
        ("html", True, ""),
        ("markdown", False, "未知原因"),
        ("obsidian", False, "缺少 OBSIDIAN_VAULT_PATH"),
        ("notion", False, "缺少 NOTION_API_KEY 或 DATABASE_ID"),
        ("onenote", True, ""),
        ("zip", False, "未知原因"),
    ]


@pytest.mark.unit
def test_single_process_viewmodel_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/viewmodels/single_process_viewmodel.py",
        repo_root / "src/wechat_summarizer/presentation/gui/viewmodels/single_process_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/viewmodels/single_process_mapping.py",
        repo_root
        / "src/wechat_summarizer/presentation/gui/viewmodels/single_process_availability.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target
