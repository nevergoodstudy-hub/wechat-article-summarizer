# 🚀 项目深度迭代改进路线图

> 基于代码审查与开源社区最佳实践分析（2026年1月）

---

## 📊 当前项目评估

### ✅ 优势
- **架构设计优秀**：采用 Clean Architecture + DDD，层次分明
- **可扩展性强**：端口-适配器模式，易于添加新的抓取器/摘要器/导出器
- **代码质量高**：类型注解完善、异常处理规范、日志记录完整
- **功能丰富**：支持多种 AI 摘要、多种导出格式、批量处理

### ✅ 已完成改进（2026年1月）
- ✅ MCP 服务支持 - 已实现 `mcp-server` CLI 命令
- ✅ MapReduce 分块摘要器 - 支持超长文本处理
- ✅ 插件系统 - 支持通过 entry_points 加载第三方插件
- ✅ 摘要质量评估增强 - 幻觉检测、信息密度、BERTScore 支持

### ⚠️ 待改进空间
- GUI 代码较为庞大（233KB）
- RAG 增强摘要（待实现）

---

## 🎯 迭代改进计划

### 第一阶段：MCP 服务支持 ⭐⭐⭐⭐⭐ ✅ 已完成

**背景**：<cite index="23-18,23-19,23-20">MCP (Model Context Protocol) 是专为 LLM 交互设计的标准化协议，让应用可以安全地向 LLM 提供数据和功能</cite>。

**实现方案**：

```python
# src/wechat_summarizer/mcp/server.py
from mcp import FastMCP

mcp = FastMCP("WeChat Article Summarizer")

@mcp.tool
async def fetch_article(url: str) -> dict:
    """抓取微信公众号文章"""
    container = get_container()
    article = container.fetch_use_case.execute(url)
    return {
        "title": article.title,
        "author": article.author,
        "content": article.content_text,
        "word_count": article.word_count,
    }

@mcp.tool
async def summarize_article(url: str, method: str = "simple") -> dict:
    """抓取并摘要文章"""
    container = get_container()
    article = container.fetch_use_case.execute(url)
    summary = container.summarize_use_case.execute(article, method=method)
    return {
        "title": article.title,
        "summary": summary.content,
        "key_points": list(summary.key_points),
        "tags": list(summary.tags),
    }

@mcp.resource("article://{url}")
async def get_article_resource(url: str) -> str:
    """作为资源提供文章内容"""
    container = get_container()
    article = container.fetch_use_case.execute(url)
    return article.content_text
```

**依赖添加**：
```toml
# pyproject.toml
[project.optional-dependencies]
mcp = ["mcp>=1.2.0"]
```

**价值**：
- 可被 Claude、ChatGPT 等 AI Agent 直接调用
- 支持 Cursor、VS Code 等 IDE 集成
- 符合未来 AI 工具生态发展方向

---

### 第二阶段：增强摘要策略 ⭐⭐⭐⭐ ✅ MapReduce 已完成

**问题**：当前摘要策略对长文本效果有限。

**改进方案 1：MapReduce 分块摘要**

<cite index="13-5,13-6,13-7">MapReduce 方法将文档分块、分别摘要、再合并总结，这反映了人类阅读长文本的方式</cite>。

```python
# src/wechat_summarizer/infrastructure/adapters/summarizers/mapreduce.py
class MapReduceSummarizer(BaseSummarizer):
    """MapReduce 分块摘要器"""
    
    def __init__(self, base_summarizer: SummarizerPort, chunk_size: int = 4000):
        self._base = base_summarizer
        self._chunk_size = chunk_size
    
    def summarize(self, content: ArticleContent, ...) -> Summary:
        text = content.text
        
        # 1. Map: 分块并摘要
        chunks = self._semantic_chunk(text, self._chunk_size)
        chunk_summaries = [
            self._base.summarize(ArticleContent.from_text(chunk))
            for chunk in chunks
        ]
        
        # 2. Reduce: 合并摘要
        combined = "\n".join(s.content for s in chunk_summaries)
        final_summary = self._base.summarize(ArticleContent.from_text(combined))
        
        return final_summary
    
    def _semantic_chunk(self, text: str, max_size: int) -> list[str]:
        """语义分块（按段落边界）"""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            if current_size + len(para) > max_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_size = 0
            current_chunk.append(para)
            current_size += len(para)
        
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        
        return chunks
```

**改进方案 2：RAG 增强摘要**

<cite index="12-3,12-4">RAG 通过在源内容中检索相关片段来增强摘要，减少幻觉并确保事实一致性</cite>。

```python
# src/wechat_summarizer/infrastructure/adapters/summarizers/rag_enhanced.py
class RAGEnhancedSummarizer(BaseSummarizer):
    """RAG 增强摘要器"""
    
    def __init__(self, base_summarizer: SummarizerPort, embedder: EmbedderPort):
        self._base = base_summarizer
        self._embedder = embedder
    
    def summarize(self, content: ArticleContent, query: str = None, ...) -> Summary:
        # 1. 分块并嵌入
        chunks = self._chunk_text(content.text)
        embeddings = self._embedder.embed(chunks)
        
        # 2. 检索相关片段
        if query:
            query_embedding = self._embedder.embed([query])[0]
            relevant_chunks = self._retrieve_top_k(chunks, embeddings, query_embedding, k=5)
        else:
            # 无查询时，选择代表性片段
            relevant_chunks = self._select_representative(chunks, embeddings)
        
        # 3. 基于检索内容生成摘要
        context = "\n".join(relevant_chunks)
        return self._base.summarize(ArticleContent.from_text(context))
```

---

### 第三阶段：摘要质量评估增强 ⭐⭐⭐⭐ ✅ 已完成

**当前状态**：已有 ROUGE 和 LLM-as-Judge 评估。

**改进方案：添加更多评估维度**

<cite index="15-3,15-4,15-5">可以检测幻觉失败（摘要中有原文没有的信息）、矛盾失败、信息缺失失败</cite>。

```python
# 扩展 EvaluationResult
@dataclass
class EnhancedEvaluationResult(EvaluationResult):
    """增强评估结果"""
    
    # 事实一致性检查
    hallucination_score: float | None = None  # 幻觉检测分数
    contradiction_count: int = 0              # 矛盾数量
    
    # 信息覆盖检查
    key_facts_coverage: float | None = None   # 关键事实覆盖率
    missing_facts: list[str] | None = None    # 缺失的关键事实
    
    # BERTScore 语义相似度
    bert_precision: float | None = None
    bert_recall: float | None = None
    bert_f1: float | None = None


class EnhancedSummaryEvaluator(SummaryEvaluator):
    """增强摘要评估器"""
    
    def evaluate_factual_consistency(self, original: str, summary: str) -> float:
        """事实一致性评估 - 使用 NLI 模型"""
        # 使用 entailment 模型检查摘要中的陈述是否被原文支持
        pass
    
    def detect_hallucinations(self, original: str, summary: str) -> list[str]:
        """幻觉检测 - 找出摘要中原文没有的事实"""
        pass
```

---

### 第四阶段：插件系统 ⭐⭐⭐ ✅ 已完成

**目标**：允许用户自定义抓取器、摘要器、导出器。

```python
# src/wechat_summarizer/infrastructure/plugins/loader.py
from importlib.metadata import entry_points

class PluginLoader:
    """插件加载器"""
    
    def load_scrapers(self) -> list[ScraperPort]:
        """从 entry_points 加载抓取器插件"""
        eps = entry_points(group="wechat_summarizer.scrapers")
        return [ep.load()() for ep in eps]
    
    def load_summarizers(self) -> dict[str, SummarizerPort]:
        """从 entry_points 加载摘要器插件"""
        eps = entry_points(group="wechat_summarizer.summarizers")
        return {ep.name: ep.load()() for ep in eps}
    
    def load_exporters(self) -> dict[str, ExporterPort]:
        """从 entry_points 加载导出器插件"""
        eps = entry_points(group="wechat_summarizer.exporters")
        return {ep.name: ep.load()() for ep in eps}
```

**插件示例 (第三方包)**：
```toml
# pyproject.toml (第三方插件)
[project.entry-points."wechat_summarizer.scrapers"]
bilibili = "my_plugin:BilibiliScraper"

[project.entry-points."wechat_summarizer.summarizers"]
custom_llm = "my_plugin:CustomLLMSummarizer"
```

---

### 第五阶段：性能优化 ⭐⭐⭐

**1. HTTP 连接池优化**

```python
# 改进 http_client_pool.py
class GlobalHttpClientPool:
    """全局 HTTP 连接池"""
    
    _instance: httpx.AsyncClient | None = None
    _lock = asyncio.Lock()
    
    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        async with cls._lock:
            if cls._instance is None:
                cls._instance = httpx.AsyncClient(
                    limits=httpx.Limits(
                        max_connections=100,
                        max_keepalive_connections=20,
                    ),
                    timeout=30.0,
                )
            return cls._instance
```

**2. 并行批量处理**

```python
# 改进 async_batch_process.py
async def process_batch_parallel(
    urls: list[str],
    max_concurrency: int = 5,
) -> list[Article]:
    """并行批量处理"""
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def process_one(url: str) -> Article:
        async with semaphore:
            return await fetch_article_async(url)
    
    tasks = [process_one(url) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

**3. 缓存优化**

```python
# 添加内存缓存 + 磁盘缓存两级缓存
class TwoLevelCache:
    """两级缓存：内存 LRU + 磁盘持久化"""
    
    def __init__(self, memory_size: int = 100, disk_path: Path = None):
        self._memory = LRUCache(memory_size)
        self._disk = DiskCache(disk_path) if disk_path else None
    
    def get(self, key: str) -> Any | None:
        # 先查内存
        if key in self._memory:
            return self._memory[key]
        # 再查磁盘
        if self._disk and key in self._disk:
            value = self._disk[key]
            self._memory[key] = value  # 提升到内存
            return value
        return None
```

---

### 第六阶段：GUI 重构 ⭐⭐⭐

**问题**：`gui/app.py` 达到 233KB，难以维护。

**改进方案：组件化拆分**

```
src/wechat_summarizer/presentation/gui/
├── __init__.py
├── app.py                    # 主应用入口（精简）
├── components/               # UI 组件
│   ├── __init__.py
│   ├── url_input.py         # URL 输入组件
│   ├── article_preview.py   # 文章预览组件
│   ├── summary_panel.py     # 摘要面板
│   ├── export_dialog.py     # 导出对话框
│   └── settings_panel.py    # 设置面板
├── viewmodels/              # 视图模型（已有）
├── utils/                   # 工具（已有）
└── styles/                  # 样式定义
    ├── __init__.py
    ├── colors.py
    └── fonts.py
```

---

### 第七阶段：可观测性增强 ⭐⭐

**1. OpenTelemetry 集成**

```python
# src/wechat_summarizer/infrastructure/observability/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

tracer = trace.get_tracer(__name__)

def trace_use_case(func):
    """用例追踪装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        with tracer.start_as_current_span(func.__name__) as span:
            span.set_attribute("args", str(args))
            try:
                result = func(*args, **kwargs)
                span.set_status(StatusCode.OK)
                return result
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                raise
    return wrapper
```

**2. Prometheus 指标**

```python
# src/wechat_summarizer/infrastructure/observability/metrics.py
from prometheus_client import Counter, Histogram

# 请求计数器
ARTICLES_FETCHED = Counter(
    "articles_fetched_total",
    "Total articles fetched",
    ["source", "status"]
)

# 延迟直方图
FETCH_LATENCY = Histogram(
    "fetch_latency_seconds",
    "Article fetch latency",
    ["scraper"]
)

SUMMARY_LATENCY = Histogram(
    "summary_latency_seconds",
    "Summary generation latency",
    ["method"]
)
```

---

## 📋 实施优先级

| 阶段 | 功能 | 优先级 | 工作量 | 价值 |
|-----|-----|-------|-------|-----|
| 1 | MCP 服务支持 | 🔴 高 | 中 | 非常高 |
| 2 | 增强摘要策略 | 🔴 高 | 高 | 高 |
| 3 | 质量评估增强 | 🟡 中 | 中 | 高 |
| 4 | 插件系统 | 🟡 中 | 中 | 中 |
| 5 | 性能优化 | 🟡 中 | 中 | 中 |
| 6 | GUI 重构 | 🟢 低 | 高 | 中 |
| 7 | 可观测性增强 | 🟢 低 | 低 | 中 |

---

## 🔗 参考资源

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP](https://github.com/jlowin/fastmcp) - 简化 MCP 服务开发
- [RAG Summarization Best Practices](https://galileo.ai/blog/llm-summarization-strategies)
- [LLM Evaluation for Summarization](https://github.com/athina-ai/ariadne)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)

---

## 📝 下一步行动

1. **立即可做**：添加 MCP 服务支持（第一阶段）
2. **短期目标**：实现 MapReduce 分块摘要
3. **中期目标**：完善插件系统和性能优化
4. **长期目标**：GUI 重构和可观测性完善
