from pathlib import Path

from wechat_summarizer.domain.entities import Article
from wechat_summarizer.domain.value_objects import ArticleContent, ArticleURL
from wechat_summarizer.infrastructure.adapters.storage.local_json import LocalJsonStorage


def test_local_json_storage_save_and_get_by_url(tmp_path: Path) -> None:
    storage = LocalJsonStorage(cache_dir=str(tmp_path))

    url = ArticleURL.from_string("https://mp.weixin.qq.com/s/abc")
    article = Article(
        url=url,
        title="t",
        content=ArticleContent.from_text("hello"),
    )

    storage.save(article)

    assert storage.exists(str(url))

    got = storage.get_by_url(str(url))
    assert got is not None
    assert got.title == "t"
    assert "hello" in got.content_text


def test_local_json_storage_list_recent(tmp_path: Path) -> None:
    storage = LocalJsonStorage(cache_dir=str(tmp_path))

    for i in range(3):
        url = ArticleURL.from_string(f"https://mp.weixin.qq.com/s/{i}")
        article = Article(url=url, title=f"t{i}", content=ArticleContent.from_text("x"))
        storage.save(article)

    recent = storage.list_recent(limit=2)
    assert len(recent) == 2
