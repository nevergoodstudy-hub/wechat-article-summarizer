"""性能基准测试

使用 pytest-benchmark 进行性能测试。
运行: pytest benchmarks/ --benchmark-only
"""

import pytest

# 跳过如果没有安装 pytest-benchmark
pytest.importorskip("pytest_benchmark")


class TestHtmlParsing:
    """HTML 解析性能测试"""

    SAMPLE_HTML = """
    <html>
    <head><title>测试文章</title></head>
    <body>
        <div id="js_content">
            <p>这是一段测试文本，用于性能基准测试。</p>
            <p>第二段文本内容，包含更多的中文字符。</p>
            <img src="https://example.com/image.jpg" alt="测试图片">
            <p>最后一段文本，用于完成测试。</p>
        </div>
    </body>
    </html>
    """ * 10  # 重复 10 次模拟较大文档

    def test_beautifulsoup_parsing(self, benchmark):
        """测试 BeautifulSoup 解析性能"""
        from bs4 import BeautifulSoup

        def parse():
            soup = BeautifulSoup(self.SAMPLE_HTML, "html.parser")
            return soup.find(id="js_content")

        result = benchmark(parse)
        assert result is not None

    def test_lxml_parsing(self, benchmark):
        """测试 lxml 解析性能"""
        from bs4 import BeautifulSoup

        def parse():
            soup = BeautifulSoup(self.SAMPLE_HTML, "lxml")
            return soup.find(id="js_content")

        result = benchmark(parse)
        assert result is not None


class TestContentExtraction:
    """内容提取性能测试"""

    SAMPLE_HTML = """
    <div id="js_content">
        <p>这是一段很长的测试文本。</p>
        <p>包含多个段落和各种HTML元素。</p>
        <ul><li>列表项1</li><li>列表项2</li></ul>
        <blockquote>引用内容</blockquote>
    </div>
    """ * 50

    def test_article_content_from_html(self, benchmark):
        """测试 ArticleContent 创建性能"""
        from wechat_summarizer.domain.value_objects import ArticleContent

        def extract():
            return ArticleContent.from_html(self.SAMPLE_HTML)

        result = benchmark(extract)
        assert result.text


class TestBleachSanitization:
    """HTML 清洗性能测试"""

    SAMPLE_HTML = """
    <div>
        <p>正常文本</p>
        <script>alert('xss')</script>
        <img src="x" onerror="alert('xss')">
        <a href="javascript:alert('xss')">恶意链接</a>
        <p onclick="alert('xss')">带事件的文本</p>
    </div>
    """ * 20

    def test_bleach_clean(self, benchmark):
        """测试 bleach 清洗性能"""
        import bleach

        ALLOWED_TAGS = ["p", "div", "span", "a", "img", "ul", "li"]
        ALLOWED_ATTRS = {"a": ["href"], "img": ["src", "alt"]}

        def sanitize():
            return bleach.clean(
                self.SAMPLE_HTML,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRS,
                strip=True,
            )

        result = benchmark(sanitize)
        assert "script" not in result
        assert "onclick" not in result


class TestSimpleSummarizer:
    """简单摘要器性能测试"""

    SAMPLE_TEXT = """
    这是一篇测试文章的内容，用于测试摘要生成的性能。
    文章包含多个段落，每个段落都有不同的内容。
    第一段介绍了文章的背景和目的。
    第二段详细描述了主要的观点和论据。
    第三段提供了具体的例子和数据支持。
    第四段总结了文章的主要结论。
    最后，文章对未来的发展进行了展望。
    """ * 10

    def test_simple_summarizer(self, benchmark):
        """测试简单摘要器性能"""
        from wechat_summarizer.infrastructure.adapters.summarizers import SimpleSummarizer

        summarizer = SimpleSummarizer()

        def summarize():
            return summarizer.summarize(self.SAMPLE_TEXT)

        result = benchmark(summarize)
        assert result.content


class TestCacheOperations:
    """缓存操作性能测试"""

    def test_json_serialization(self, benchmark):
        """测试 JSON 序列化性能"""
        import json

        data = {
            "id": "test-123",
            "url": "https://mp.weixin.qq.com/s/test",
            "title": "测试文章标题",
            "content": {
                "html": "<p>测试内容</p>" * 100,
                "text": "测试内容" * 100,
                "images": ["https://example.com/1.jpg"] * 10,
            },
        }

        def serialize():
            return json.dumps(data, ensure_ascii=False)

        result = benchmark(serialize)
        assert result

    def test_json_deserialization(self, benchmark):
        """测试 JSON 反序列化性能"""
        import json

        json_str = json.dumps({
            "id": "test-123",
            "url": "https://mp.weixin.qq.com/s/test",
            "title": "测试文章标题",
            "content": {
                "html": "<p>测试内容</p>" * 100,
                "text": "测试内容" * 100,
                "images": ["https://example.com/1.jpg"] * 10,
            },
        }, ensure_ascii=False)

        def deserialize():
            return json.loads(json_str)

        result = benchmark(deserialize)
        assert result["id"] == "test-123"


class TestUrlValidation:
    """URL 验证性能测试"""

    def test_article_url_creation(self, benchmark):
        """测试 ArticleURL 创建性能"""
        from wechat_summarizer.domain.value_objects import ArticleURL

        def create_url():
            return ArticleURL.from_string("https://mp.weixin.qq.com/s/abcdefghijklmnop")

        result = benchmark(create_url)
        assert result.is_wechat


class TestEvaluationMetrics:
    """评估指标性能测试"""

    ORIGINAL = """
    这是一篇关于人工智能发展的文章。
    人工智能正在改变我们的生活方式。
    机器学习是人工智能的核心技术之一。
    深度学习在图像识别和自然语言处理领域取得了突破性进展。
    """ * 5

    SUMMARY = """
    本文介绍了人工智能的发展，特别是机器学习和深度学习在图像识别和NLP领域的应用。
    """

    @pytest.mark.skipif(
        not _rouge_available(),
        reason="rouge-score not installed"
    )
    def test_rouge_evaluation(self, benchmark):
        """测试 ROUGE 评估性能"""
        from rouge_score import rouge_scorer

        scorer = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=False)

        def evaluate():
            return scorer.score(self.ORIGINAL, self.SUMMARY)

        result = benchmark(evaluate)
        assert "rouge1" in result


def _rouge_available():
    """检查 rouge-score 是否可用"""
    try:
        from rouge_score import rouge_scorer
        return True
    except ImportError:
        return False
