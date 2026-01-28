from pathlib import Path

from wechat_summarizer.domain.entities import Article
from wechat_summarizer.domain.value_objects import ArticleContent, ArticleURL
from wechat_summarizer.infrastructure.adapters.exporters.obsidian import ObsidianExporter


def test_obsidian_exporter_writes_markdown(tmp_path: Path) -> None:
    exporter = ObsidianExporter(vault_path=str(tmp_path))

    article = Article(
        url=ArticleURL.from_string("https://mp.weixin.qq.com/s/xxx"),
        title="Test",
        content=ArticleContent.from_text("hello"),
    )

    out = Path(exporter.export(article))
    assert out.suffix == ".md"
    assert out.exists()
