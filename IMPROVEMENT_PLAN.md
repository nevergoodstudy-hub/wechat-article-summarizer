# 微信公众号文章总结器 - 改进开发计划

> 基于项目代码全面审查，按照 DDD/六边形架构规范、Python 最佳实践、安全规范制定

---

## 📊 项目现状评估

### ✅ 优点
- **架构设计优秀**：采用 DDD + 六边形架构，层次分明
- **依赖注入良好**：Container 模式实现依赖管理
- **类型标注完整**：使用 Python 3.10+ 类型提示
- **配置管理规范**：Pydantic Settings 统一管理配置
- **多适配器支持**：抓取器、摘要器、导出器均支持多实现

### ⚠️ 待改进项
- 测试覆盖不完整（部分测试文件存在字段不一致）
- 异步支持不完善（定义了接口但未完全实现）
- 安全防护需加强（输入验证、敏感信息保护）
- 错误处理需细化（部分异常信息可优化）
- 缓存机制可增强（缺少过期策略）

---

## 🔧 改进开发计划

### 阶段一：代码质量与安全修复（优先级：高）

#### 1.1 修复测试文件字段不一致问题
**位置**: `tests/conftest.py`, `tests/test_entities.py`

**问题**: 
- `conftest.py` 中 `sample_summary` fixture 使用了不存在的 `token_usage` 字段
- `test_entities.py` 中测试用例也使用了 `token_usage` 而非正确的 `input_tokens`/`output_tokens`
- `SummaryStyle.BULLET_POINTS` 测试断言与实际枚举值 `bullet` 不匹配

**修复方案**:
```python
# conftest.py - 修正 sample_summary
@pytest.fixture
def sample_summary() -> Summary:
    return Summary(
        content="这是一篇关于人工智能如何改变生活的测试文章摘要。",
        key_points=("人工智能正在改变生活方式", "文章包含多个测试段落"),
        tags=("AI", "测试", "科技"),
        method=SummaryMethod.SIMPLE,
        style=SummaryStyle.CONCISE,
        model_name="simple",
        input_tokens=0,  # 修正字段名
        output_tokens=0,  # 修正字段名
        created_at=datetime.now(),
    )

# test_entities.py - 修正断言
assert SummaryStyle.BULLET_POINTS.value == "bullet"  # 而非 "bullet_points"
```

#### 1.2 增强输入验证与安全防护
**位置**: `domain/value_objects/url.py`, `application/use_cases/*.py`

**改进方案**:
```python
# url.py - 增加 URL 安全验证
@dataclass(frozen=True)
class ArticleURL:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise InvalidURLError("URL不能为空")
        
        # 新增：长度限制
        if len(self.value) > 2048:
            raise InvalidURLError("URL长度超出限制")
        
        parsed = urlparse(self.value)
        if not parsed.scheme or not parsed.netloc:
            raise InvalidURLError(f"无效的URL格式: {self.value}")
        
        # 新增：协议白名单
        if parsed.scheme not in ("http", "https"):
            raise InvalidURLError(f"不支持的协议: {parsed.scheme}")
        
        # 新增：防止 SSRF 攻击 - 禁止内网地址
        if self._is_private_ip(parsed.netloc):
            raise InvalidURLError("不允许访问内网地址")
```

#### 1.3 敏感信息保护增强
**位置**: `infrastructure/config/settings.py`

**改进方案**:
```python
# 使用 SecretStr 保护 API 密钥
from pydantic import SecretStr

class OpenAISettings(BaseSettings):
    api_key: SecretStr = Field(default=SecretStr(""), description="API密钥")
    # ...

# 日志脱敏处理
def _mask_sensitive(value: str, visible_chars: int = 4) -> str:
    if len(value) <= visible_chars * 2:
        return "***"
    return value[:visible_chars] + "***" + value[-visible_chars:]
```

---

### 阶段二：测试覆盖完善（优先级：高）

#### 2.1 补充缺失的单元测试
**需要新增的测试文件**:
- `tests/test_use_cases.py` - 用例层测试
- `tests/test_scrapers.py` - 抓取器适配器测试
- `tests/test_summarizers.py` - 摘要器适配器测试
- `tests/test_container.py` - 依赖注入容器测试

**测试覆盖目标**:
```python
# test_use_cases.py 示例
class TestFetchArticleUseCase:
    @pytest.mark.unit
    def test_execute_with_valid_url(self, mock_scraper, mock_storage):
        """测试正常抓取流程"""
        use_case = FetchArticleUseCase([mock_scraper], storage=mock_storage)
        article = use_case.execute("https://mp.weixin.qq.com/s/test")
        assert article.title == "测试文章标题"
        mock_scraper.scrape.assert_called_once()

    @pytest.mark.unit
    def test_execute_with_cache_hit(self, mock_scraper, mock_storage, sample_article):
        """测试缓存命中"""
        mock_storage.get_by_url.return_value = sample_article
        use_case = FetchArticleUseCase([mock_scraper], storage=mock_storage)
        article = use_case.execute("https://mp.weixin.qq.com/s/test")
        mock_scraper.scrape.assert_not_called()  # 不应调用抓取器

    @pytest.mark.unit
    def test_execute_with_invalid_url(self, mock_scraper):
        """测试无效 URL"""
        use_case = FetchArticleUseCase([mock_scraper])
        with pytest.raises(UseCaseError, match="无效的URL"):
            use_case.execute("invalid-url")
```

#### 2.2 集成测试
**新增文件**: `tests/integration/test_full_flow.py`

```python
@pytest.mark.integration
@pytest.mark.slow
class TestFullProcessingFlow:
    """端到端集成测试"""
    
    def test_fetch_summarize_export_flow(self, tmp_path):
        """测试完整的抓取->摘要->导出流程"""
        # 使用 mock 服务器模拟微信文章
        pass
```

---

### 阶段三：异步支持完善（优先级：中）

#### 3.1 实现异步用例
**位置**: `application/use_cases/`

**问题**: 当前定义了 `AsyncScraperPort`、`AsyncSummarizerPort` 接口，但用例层未实现异步版本

**改进方案**:
```python
# application/use_cases/fetch_article.py
class AsyncFetchArticleUseCase:
    """异步抓取文章用例"""
    
    def __init__(self, scrapers: list[AsyncScraperPort], storage: StoragePort | None = None):
        self._scrapers = scrapers
        self._storage = storage

    async def execute(self, url: str, preferred_scraper: str | None = None) -> Article:
        """异步执行抓取"""
        article_url = ArticleURL.from_string(url)
        
        # 缓存检查
        if self._storage is not None:
            cached = self._storage.get_by_url(str(article_url))
            if cached:
                return cached
        
        # 异步抓取
        for scraper in self._scrapers:
            if scraper.can_handle(article_url):
                try:
                    article = await scraper.scrape_async(article_url)
                    if self._storage:
                        self._storage.save(article)
                    return article
                except ScraperError:
                    continue
        
        raise UseCaseError(f"没有可用的抓取器能处理URL: {url}")
```

#### 3.2 实现异步抓取器
**位置**: `infrastructure/adapters/scrapers/wechat_httpx.py`

```python
class WechatHttpxScraper(BaseScraper):
    # ... 现有代码 ...
    
    async def scrape_async(self, url: ArticleURL) -> Article:
        """异步抓取微信公众号文章"""
        headers = {
            "User-Agent": self._choose_user_agent(),
            # ...
        }
        
        async with httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=True,
            proxy=self._proxy,
        ) as client:
            response = await client.get(str(url), headers=headers)
            response.raise_for_status()
            return self._parse_html(response.text, url)
```

---

### 阶段四：缓存机制增强（优先级：中）

#### 4.1 缓存过期策略
**位置**: `infrastructure/adapters/storage/local_json.py`

**改进方案**:
```python
@dataclass
class CacheConfig:
    max_age_hours: int = 24 * 7  # 默认7天
    max_entries: int = 1000
    cleanup_interval_hours: int = 24

class LocalJsonStorage:
    def __init__(self, cache_dir: Path | None = None, config: CacheConfig | None = None):
        self._cache_dir = cache_dir or (Path.home() / CONFIG_DIR_NAME / CACHE_DIR_NAME)
        self._config = config or CacheConfig()
        self._cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_by_url(self, url: str) -> Article | None:
        """获取缓存，检查是否过期"""
        cache_file = self._get_cache_file(url)
        if not cache_file.exists():
            return None
        
        # 检查缓存是否过期
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime > timedelta(hours=self._config.max_age_hours):
            cache_file.unlink()  # 删除过期缓存
            return None
        
        # ... 加载缓存 ...
    
    def cleanup_expired(self) -> int:
        """清理过期缓存，返回清理数量"""
        cleaned = 0
        for cache_file in self._cache_dir.glob("*.json"):
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - mtime > timedelta(hours=self._config.max_age_hours):
                cache_file.unlink()
                cleaned += 1
        return cleaned
```

#### 4.2 新增 CLI 缓存管理命令
**位置**: `presentation/cli/app.py`

```python
@cli.command(name="cache-clean")
@click.option("--all", "clean_all", is_flag=True, help="清理所有缓存")
@click.option("--expired", is_flag=True, help="仅清理过期缓存")
def cache_clean(clean_all: bool, expired: bool):
    """清理本地缓存"""
    container = get_container()
    storage = container.storage
    
    if storage is None:
        console.print("[yellow]缓存存储不可用[/yellow]")
        return
    
    if clean_all:
        count = storage.clear_all()
        console.print(f"[green]已清理 {count} 条缓存[/green]")
    elif expired:
        count = storage.cleanup_expired()
        console.print(f"[green]已清理 {count} 条过期缓存[/green]")

@cli.command(name="cache-stats")
def cache_stats():
    """显示缓存统计信息"""
    # 显示缓存数量、大小、最近使用等信息
```

---

### 阶段五：功能增强（优先级：中）

#### 5.1 支持更多文章来源
**新增文件**: `infrastructure/adapters/scrapers/generic_httpx.py`

```python
class GenericHttpxScraper(BaseScraper):
    """通用网页抓取器 - 支持任意网页"""
    
    @property
    def name(self) -> str:
        return "generic_httpx"
    
    def can_handle(self, url: ArticleURL) -> bool:
        # 支持所有 HTTP/HTTPS URL
        return url.scheme in ("http", "https")
    
    def scrape(self, url: ArticleURL) -> Article:
        """抓取通用网页"""
        # 使用 readability 算法提取正文
        # 使用 newspaper3k 或 trafilatura 库
        pass
```

#### 5.2 摘要质量评估
**新增文件**: `domain/services/quality_evaluator.py`

```python
@dataclass
class QualityScore:
    """摘要质量评分"""
    completeness: float  # 完整性 0-1
    conciseness: float   # 简洁性 0-1
    coherence: float     # 连贯性 0-1
    overall: float       # 总分 0-1

class SummaryQualityEvaluator:
    """摘要质量评估器"""
    
    def evaluate(self, article: Article, summary: Summary) -> QualityScore:
        """评估摘要质量"""
        completeness = self._evaluate_completeness(article.content_text, summary.content)
        conciseness = self._evaluate_conciseness(summary.content)
        coherence = self._evaluate_coherence(summary.content)
        
        return QualityScore(
            completeness=completeness,
            conciseness=conciseness,
            coherence=coherence,
            overall=(completeness + conciseness + coherence) / 3,
        )
```

#### 5.3 批量处理并发优化
**位置**: `application/use_cases/batch_process.py`

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class BatchProcessUseCase:
    async def execute_async(
        self,
        urls: list[str],
        method: str = "simple",
        max_concurrent: int = 5,
    ) -> list[BatchResult]:
        """异步并发批量处理"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_one(url: str) -> BatchResult:
            async with semaphore:
                try:
                    article = await self._fetch_async(url)
                    summary = await self._summarize_async(article, method)
                    article.attach_summary(summary)
                    return BatchResult(url=url, article=article, success=True)
                except Exception as e:
                    return BatchResult(url=url, error=str(e), success=False)
        
        tasks = [process_one(url) for url in urls]
        return await asyncio.gather(*tasks)
```

---

### 阶段六：可观测性增强（优先级：低）

#### 6.1 结构化日志
**位置**: `shared/utils/logger.py`

```python
import json
from loguru import logger

def setup_logger(
    level: str = "INFO",
    json_format: bool = False,
    log_file: str | None = None,
) -> None:
    """配置日志"""
    logger.remove()
    
    if json_format:
        # 结构化 JSON 日志（便于日志收集系统）
        format_str = "{message}"
        logger.add(
            sys.stderr,
            format=format_str,
            level=level,
            serialize=True,
        )
    else:
        # 人类可读格式
        format_str = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
        logger.add(sys.stderr, format=format_str, level=level)
    
    if log_file:
        logger.add(
            log_file,
            rotation="10 MB",
            retention="7 days",
            compression="gz",
        )
```

#### 6.2 指标收集（可选）
```python
# 用于监控的指标
@dataclass
class ProcessingMetrics:
    articles_fetched: int = 0
    articles_failed: int = 0
    summaries_generated: int = 0
    total_tokens_used: int = 0
    avg_processing_time_ms: float = 0
```

---

### 阶段七：文档与开发体验（优先级：低）

#### 7.1 API 文档生成
- 使用 `mkdocs` + `mkdocstrings` 自动生成 API 文档
- 添加使用示例和架构说明

#### 7.2 开发者指南
**新增文件**: `docs/CONTRIBUTING.md`

```markdown
# 贡献指南

## 开发环境设置
pip install -e .[dev]
pre-commit install

## 代码规范
- 使用 ruff 进行代码格式化和 lint
- 使用 mypy 进行类型检查
- 所有新功能必须包含单元测试

## 提交规范
- feat: 新功能
- fix: Bug 修复
- docs: 文档更新
- refactor: 代码重构
```

---

## 📅 实施优先级

| 阶段 | 内容 | 优先级 | 预估工时 |
|------|------|--------|----------|
| 一 | 代码质量与安全修复 | 🔴 高 | 2-3天 |
| 二 | 测试覆盖完善 | 🔴 高 | 3-4天 |
| 三 | 异步支持完善 | 🟡 中 | 2-3天 |
| 四 | 缓存机制增强 | 🟡 中 | 1-2天 |
| 五 | 功能增强 | 🟡 中 | 3-5天 |
| 六 | 可观测性增强 | 🟢 低 | 1-2天 |
| 七 | 文档与开发体验 | 🟢 低 | 1-2天 |

---

## 🔒 安全审查清单

### 已通过
- [x] 使用参数化配置，无硬编码密钥
- [x] 异常处理完整，不泄露敏感堆栈
- [x] URL 基本验证
- [x] API 密钥使用 SecretStr 保护 ✅ (2026-01-16 已完成)
- [x] 添加 SSRF 防护（内网地址过滤）✅ (2026-01-16 已完成)
- [x] 日志脱敏处理 ✅ (2026-01-16 已完成)
- [x] 输入长度限制 ✅ (2026-01-16 已完成)

### 需改进
- [ ] 添加速率限制（防滥用）

---

## 📈 实施进度

| 阶段 | 内容 | 状态 | 完成日期 |
|------|------|------|----------|
| 一 | 代码质量与安全修复 | ✅ 已完成 | 2026-01-16 |
| 二 | 测试覆盖完善 | ✅ 已完成 | 2026-01-16 |
| 三 | 异步支持完善 | ✅ 已完成 | 2026-01-16 |
| 四 | 缓存机制增强 | ✅ 已完成 | 2026-01-16 |
| 五 | 功能增强 | ✅ 已完成 | 2026-01-16 |
| 六 | 可观测性增强 | ✅ 已完成 | 2026-01-16 |
| 七 | 文档与开发体验 | ✅ 已完成 | 2026-01-16 |

---

*文档生成时间: 2026-01-16*
*最后更新: 2026-01-16 - 全部7个阶段已完成*
