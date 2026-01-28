# 架构设计文档

## 概述

微信公众号文章总结器采用 **DDD（领域驱动设计）+ 六边形架构（Hexagonal Architecture）** 设计模式，实现了高内聚、低耦合的代码组织。

## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                        │
│  ┌─────────────────┐               ┌─────────────────────────┐  │
│  │   CLI (Click)   │               │   GUI (CustomTkinter)   │  │
│  │                 │               │   ┌─────────────────┐   │  │
│  │  - fetch        │               │   │   ViewModels    │   │  │
│  │  - batch        │               │   │   (MVVM)        │   │  │
│  │  - cache-clean  │               │   └─────────────────┘   │  │
│  └────────┬────────┘               └───────────┬─────────────┘  │
│           │                                    │                 │
└───────────┼────────────────────────────────────┼─────────────────┘
            │                                    │
            ▼                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      Use Cases                             │  │
│  │  - FetchArticleUseCase                                     │  │
│  │  - SummarizeArticleUseCase                                 │  │
│  │  - ExportArticleUseCase                                    │  │
│  │  - BatchProcessUseCase                                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                        Ports                               │  │
│  │  Inbound:  ArticleService, BatchService                    │  │
│  │  Outbound: ScraperPort, SummarizerPort, ExporterPort, ...  │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
            │                                    ▲
            ▼                                    │
┌─────────────────────────────────────────────────────────────────┐
│                         Domain Layer                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐ │
│  │    Entities    │  │ Value Objects  │  │  Domain Services   │ │
│  │  - Article     │  │  - ArticleURL  │  │  - ArticleProcessor│ │
│  │  - Summary     │  │  - ArticleContent│ │  - QualityEvaluator│ │
│  │  - Source      │  │                │  │                    │ │
│  └────────────────┘  └────────────────┘  └────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
            ▲                                    │
            │                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Infrastructure Layer                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                       Adapters                             │  │
│  │  Scrapers:     WechatHttpxScraper, ZhihuScraper, ...      │  │
│  │  Summarizers:  SimpleSummarizer, OpenAISummarizer, ...    │  │
│  │  Exporters:    HtmlExporter, MarkdownExporter, ...        │  │
│  │  Storage:      LocalJsonStorage                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Config & Container                      │  │
│  │  - AppSettings (Pydantic Settings)                         │  │
│  │  - Container (Dependency Injection)                        │  │
│  │  - Paths (Windows/macOS/Linux 标准路径)                    │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

## 分层说明

### 1. 表现层 (Presentation Layer)

负责与用户交互，包括 CLI 和 GUI 两种界面。

**目录结构：**
```
presentation/
├── cli/
│   ├── app.py          # Click 命令定义
│   └── __init__.py
└── gui/
    ├── app.py          # GUI 主入口
    ├── viewmodels/     # MVVM 视图模型
    ├── views/          # 视图组件
    ├── widgets/        # 自定义控件
    └── utils/          # GUI 工具（Windows 集成、主题管理）
```

**关键点：**
- GUI 采用 MVVM 模式，视图模型与视图分离
- 依赖 Application 层的用例，不直接访问 Infrastructure

### 2. 应用层 (Application Layer)

编排业务流程，协调领域对象和基础设施。

**目录结构：**
```
application/
├── dto/                # 数据传输对象
├── ports/
│   ├── inbound/        # 入站端口（服务接口）
│   └── outbound/       # 出站端口（抓取器、摘要器等接口）
├── use_cases/          # 用例实现
└── viewmodels/         # 可选：跨展示层的视图模型
```

**关键用例：**
- `FetchArticleUseCase` - 抓取文章
- `SummarizeArticleUseCase` - 生成摘要
- `ExportArticleUseCase` - 导出文章
- `BatchProcessUseCase` - 批量处理

### 3. 领域层 (Domain Layer)

包含核心业务逻辑，完全独立于框架和基础设施。

**目录结构：**
```
domain/
├── entities/           # 实体
│   ├── article.py      # 文章实体
│   ├── summary.py      # 摘要实体
│   └── source.py       # 来源实体
├── value_objects/      # 值对象
│   ├── url.py          # URL 值对象
│   └── content.py      # 内容值对象
├── services/           # 领域服务
└── events/             # 领域事件
```

**设计原则：**
- 实体有唯一标识，可变
- 值对象无标识，不可变
- 领域逻辑封装在实体和领域服务中

### 4. 基础设施层 (Infrastructure Layer)

实现技术细节，如网络请求、数据存储、外部 API 调用。

**目录结构：**
```
infrastructure/
├── adapters/
│   ├── scrapers/       # 抓取器实现
│   ├── summarizers/    # 摘要器实现
│   ├── exporters/      # 导出器实现
│   └── storage/        # 存储实现
├── config/
│   ├── settings.py     # 配置管理
│   ├── container.py    # 依赖注入容器
│   └── paths.py        # 路径管理
└── observability/      # 可观测性（指标、追踪）
```

### 5. 共享层 (Shared Layer)

跨层共用的工具和常量。

**目录结构：**
```
shared/
├── constants.py        # 全局常量
├── exceptions.py       # 异常定义（含错误码）
└── utils/
    ├── logger.py       # 日志配置
    ├── retry.py        # 重试工具
    └── text.py         # 文本处理工具
```

## 依赖注入

使用 `Container` 类管理所有依赖：

```python
from wechat_summarizer.infrastructure.config import get_container

container = get_container()

# 获取用例
fetch_use_case = container.fetch_use_case
summarize_use_case = container.summarize_use_case

# 获取适配器
scrapers = container.scrapers
summarizers = container.summarizers
```

## 错误处理

统一使用错误码枚举：

```python
from wechat_summarizer.shared.exceptions import ErrorCode, ScraperError

# 抛出带错误码的异常
raise ScraperError(
    "抓取失败",
    error_code=ErrorCode.SCRAPER_TIMEOUT,
    details={"url": url, "timeout": 30},
)
```

## 配置管理

使用 Pydantic Settings，支持环境变量和 .env 文件：

```python
from wechat_summarizer.infrastructure.config import get_settings

settings = get_settings()

# 访问配置
api_key = settings.openai.api_key.get_secret_value()
output_dir = settings.export.default_output_dir
```

## 扩展指南

### 添加新的抓取器

1. 在 `infrastructure/adapters/scrapers/` 创建新文件
2. 实现 `ScraperPort` 接口
3. 在 `Container._create_scrapers()` 中注册

### 添加新的摘要器

1. 在 `infrastructure/adapters/summarizers/` 创建新文件
2. 实现 `SummarizerPort` 接口
3. 在 `Container._create_summarizers()` 中注册

### 添加新的导出器

1. 在 `infrastructure/adapters/exporters/` 创建新文件
2. 实现 `ExporterPort` 接口
3. 在 `Container._create_exporters()` 中注册

## 测试策略

- **单元测试**：测试领域层和应用层逻辑
- **集成测试**：测试适配器与外部服务的集成
- **端到端测试**：测试完整的用户流程

```bash
# 运行所有测试
pytest tests/

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/
```
