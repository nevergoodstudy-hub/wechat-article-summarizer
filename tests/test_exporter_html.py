from pathlib import Path

from wechat_summarizer.domain.entities import Article
from wechat_summarizer.domain.value_objects import ArticleContent, ArticleURL
from wechat_summarizer.infrastructure.adapters.exporters.html import HtmlExporter


def test_html_exporter_writes_file(tmp_path: Path) -> None:
    article = Article(
        url=ArticleURL.from_string("https://mp.weixin.qq.com/s/xxx"),
        title='A/B:C*?"<>|',
        content=ArticleContent.from_text("hello"),
    )

    exporter = HtmlExporter(output_dir=str(tmp_path))
    out_path = Path(exporter.export(article))

    assert out_path.suffix == ".html"
    assert out_path.exists()
