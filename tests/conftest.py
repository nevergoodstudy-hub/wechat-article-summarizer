"""测试夹具和共享配置

提供测试中常用的夹具：
- 示例 Article、Summary 实体
- Mock 存储、抓取器、摘要器
- 临时目录和文件
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock
from uuid import uuid4

from wechat_summarizer.shared.utils import utc_now

import pytest

from wechat_summarizer.domain.entities import Article, Summary
from wechat_summarizer.domain.entities.summary import SummaryMethod, SummaryStyle
from wechat_summarizer.domain.value_objects import ArticleContent, ArticleURL

if TYPE_CHECKING:
    from collections.abc import Generator


# ============== 基础夹具 ==============


@pytest.fixture
def sample_wechat_url() -> ArticleURL:
    """示例微信公众号文章 URL"""
    return ArticleURL.from_string("https://mp.weixin.qq.com/s/test123456")


@pytest.fixture
def sample_content() -> ArticleContent:
    """示例文章内容"""
    html = """
    <div id="js_content">
        <p>这是一篇测试文章的正文内容。</p>
        <p>文章包含多个段落，用于测试摘要功能。</p>
        <p>人工智能正在改变我们的生活方式。</p>
        <img data-src="https://example.com/image1.jpg" />
    </div>
    """
    return ArticleContent.from_html(html)


@pytest.fixture
def sample_article(sample_wechat_url: ArticleURL, sample_content: ArticleContent) -> Article:
    """示例文章实体"""
    return Article(
        id=uuid4(),
        url=sample_wechat_url,
        title="测试文章标题",
        author="测试作者",
        account_name="测试公众号",
        publish_time=datetime(2024, 1, 15, 10, 30, 0),
        content=sample_content,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_summary() -> Summary:
    """示例摘要实体"""
    return Summary(
        content="这是一篇关于人工智能如何改变生活的测试文章摘要。",
        key_points=(
            "人工智能正在改变生活方式",
            "文章包含多个测试段落",
        ),
        tags=("AI", "测试", "科技"),
        method=SummaryMethod.SIMPLE,
        style=SummaryStyle.CONCISE,
        model_name="simple",
        input_tokens=0,
        output_tokens=0,
        created_at=utc_now(),
    )


@pytest.fixture
def article_with_summary(sample_article: Article, sample_summary: Summary) -> Article:
    """带摘要的文章实体"""
    sample_article.attach_summary(sample_summary)
    return sample_article


# ============== Mock 夹具 ==============


@pytest.fixture
def mock_storage() -> Mock:
    """Mock 存储适配器"""
    storage = Mock()
    storage.save.return_value = None
    storage.get.return_value = None
    storage.get_by_url.return_value = None
    storage.exists.return_value = False
    storage.list_recent.return_value = []
    storage.delete.return_value = True
    return storage


@pytest.fixture
def mock_scraper(sample_article: Article) -> Mock:
    """Mock 抓取器适配器"""
    scraper = Mock()
    scraper.name = "mock_scraper"
    scraper.can_handle.return_value = True
    scraper.scrape.return_value = sample_article
    return scraper


@pytest.fixture
def mock_summarizer(sample_summary: Summary) -> Mock:
    """Mock 摘要器适配器"""
    summarizer = Mock()
    summarizer.name = "mock_summarizer"
    summarizer.method = SummaryMethod.SIMPLE
    summarizer.is_available.return_value = True
    summarizer.summarize.return_value = sample_summary
    return summarizer


@pytest.fixture
def mock_exporter(tmp_path: Path) -> Mock:
    """Mock 导出器适配器"""
    exporter = Mock()
    exporter.name = "mock_exporter"
    exporter.target = "mock"
    exporter.is_available.return_value = True
    output_file = tmp_path / "exported.html"
    exporter.export.return_value = str(output_file)
    return exporter


# ============== 文件系统夹具 ==============


@pytest.fixture
def output_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """临时输出目录"""
    output = tmp_path / "output"
    output.mkdir(parents=True, exist_ok=True)
    yield output


@pytest.fixture
def cache_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """临时缓存目录"""
    cache = tmp_path / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    yield cache


# ============== HTTP 响应夹具 ==============


@pytest.fixture
def wechat_html_response() -> str:
    """模拟微信公众号文章 HTML 响应"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>测试文章</title>
    </head>
    <body>
        <div id="img-content">
            <h1 class="rich_media_title" id="activity-name">测试文章标题</h1>
            <span class="rich_media_meta rich_media_meta_text" id="profileBt">测试公众号</span>
            <span class="rich_media_meta rich_media_meta_nickname" id="js_name">测试作者</span>
            <em id="publish_time" class="rich_media_meta rich_media_meta_text">2024年1月15日 10:30</em>
            <div class="rich_media_content" id="js_content">
                <p>这是文章正文内容。</p>
                <p>包含多个段落用于测试。</p>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def ai_summary_response() -> str:
    """模拟 AI 摘要 API 响应"""
    return """
## 摘要
这是一篇关于测试的文章，主要介绍了测试相关内容。

## 关键要点
- 测试是软件开发的重要环节
- 自动化测试可以提高效率

## 标签
测试, 软件开发, 自动化
"""
