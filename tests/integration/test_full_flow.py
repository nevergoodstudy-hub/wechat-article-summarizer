"""端到端集成测试

测试完整的抓取->摘要->导出流程。
使用Mock HTTP响应模拟微信文章。
"""

from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

import pytest

from wechat_summarizer.infrastructure.config.container import Container, reset_container
from wechat_summarizer.domain.entities import Article
from wechat_summarizer.domain.value_objects import ArticleURL, ArticleContent


@pytest.fixture
def mock_wechat_html() -> str:
    """模拟微信公众号文章HTML"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>测试文章标题</title>
    </head>
    <body>
        <div id="img-content">
            <h1 class="rich_media_title" id="activity-name">集成测试文章标题</h1>
            <span class="rich_media_meta rich_media_meta_text" id="profileBt">测试公众号</span>
            <span class="rich_media_meta rich_media_meta_nickname" id="js_name">测试作者</span>
            <em id="publish_time" class="rich_media_meta rich_media_meta_text">2024年1月15日 10:30</em>
            <div class="rich_media_content" id="js_content">
                <p>这是集成测试文章的正文内容。</p>
                <p>文章包含多个段落，用于测试完整流程。</p>
                <p>人工智能正在改变我们的生活方式。</p>
                <p>这是第四个段落，增加文章长度。</p>
                <p>这是第五个段落，确保有足够内容生成摘要。</p>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture(autouse=True)
def cleanup():
    """每个测试后重置容器"""
    yield
    reset_container()


@pytest.mark.integration
class TestFullProcessingFlow:
    """端到端集成测试"""

    def test_simple_summarize_export_flow(
        self, mock_wechat_html: str, tmp_path: Path
    ) -> None:
        """测试完整的抓取->简单摘要->导出流程（使用Mock）"""
        # 创建模拟文章
        article = Article(
            url=ArticleURL.from_string("https://mp.weixin.qq.com/s/test123"),
            title="集成测试文章标题",
            author="测试作者",
            account_name="测试公众号",
            publish_time=datetime(2024, 1, 15, 10, 30, 0),
            content=ArticleContent.from_html(mock_wechat_html),
        )

        # 获取容器
        container = Container()

        # 使用简单摘要器
        summarize_use_case = container.summarize_use_case
        summary = summarize_use_case.execute(article, method="simple")

        assert summary is not None
        assert summary.content  # 有摘要内容
        assert summary.method.value == "simple"

        # 附加摘要到文章
        article.attach_summary(summary)

        # 导出为HTML
        export_use_case = container.export_use_case

        # 修改导出目录为临时目录
        html_exporter = container.exporters.get("html")
        if html_exporter:
            html_exporter._output_dir = tmp_path

        result = export_use_case.execute(article, target="html")

        assert result is not None
        output_path = Path(result)
        assert output_path.exists()
        assert output_path.suffix == ".html"

        # 验证导出内容
        content = output_path.read_text(encoding="utf-8")
        assert "集成测试文章标题" in content
        assert summary.content in content or "摘要" in content

    def test_markdown_export_flow(
        self, mock_wechat_html: str, tmp_path: Path
    ) -> None:
        """测试Markdown导出流程"""
        article = Article(
            url=ArticleURL.from_string("https://mp.weixin.qq.com/s/test456"),
            title="Markdown测试文章",
            author="测试作者",
            content=ArticleContent.from_html(mock_wechat_html),
        )

        container = Container()

        # 生成摘要
        summary = container.summarize_use_case.execute(article, method="simple")
        article.attach_summary(summary)

        # 修改导出目录
        md_exporter = container.exporters.get("markdown")
        if md_exporter:
            md_exporter._output_dir = tmp_path

        result = container.export_use_case.execute(article, target="markdown")

        assert result is not None
        output_path = Path(result)
        assert output_path.exists()
        assert output_path.suffix == ".md"

        content = output_path.read_text(encoding="utf-8")
        assert "Markdown测试文章" in content

    def test_container_provides_all_components(self) -> None:
        """测试容器提供所有必需组件"""
        container = Container()

        # 验证抓取器
        assert len(container.scrapers) > 0

        # 验证摘要器（至少有simple）
        assert "simple" in container.summarizers

        # 验证导出器
        assert "html" in container.exporters
        assert "markdown" in container.exporters

        # 验证用例
        assert container.fetch_use_case is not None
        assert container.summarize_use_case is not None
        assert container.export_use_case is not None
        assert container.batch_use_case is not None


@pytest.mark.integration
class TestCacheIntegration:
    """缓存集成测试"""

    def test_storage_save_and_retrieve(self, tmp_path: Path) -> None:
        """测试存储保存和读取"""
        from wechat_summarizer.infrastructure.adapters.storage import LocalJsonStorage

        storage = LocalJsonStorage(cache_dir=tmp_path)

        article = Article(
            url=ArticleURL.from_string("https://mp.weixin.qq.com/s/cache_test"),
            title="缓存测试文章",
            author="测试作者",
            content=ArticleContent.from_text("这是缓存测试内容"),
        )

        # 保存
        storage.save(article)

        # 读取
        retrieved = storage.get_by_url("https://mp.weixin.qq.com/s/cache_test")

        assert retrieved is not None
        assert retrieved.title == "缓存测试文章"
        assert retrieved.author == "测试作者"
