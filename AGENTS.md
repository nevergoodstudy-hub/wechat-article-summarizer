# AGENTS.md - AI 编码助手指引

本文档为 AI 编码助手（如 GitHub Copilot、Cursor、Claude、ChatGPT 等）提供项目上下文和开发指南。

## 📋 项目概览

**项目名称**: 微信公众号文章总结器 (WeChat Article Summarizer)  
**版本**: v2.4.0  
**架构**: DDD + 六边形架构（Clean Architecture）  
**语言**: Python 3.11+  
**框架**: CustomTkinter (GUI), Click (CLI), FastMCP (MCP Server)

**核心功能**:
- 抓取微信公众号文章内容
- AI 摘要生成（支持 OpenAI/Anthropic/DeepSeek/Ollama 等）
- RAG 增强摘要（向量检索）
- GraphRAG 知识图谱分析
- 多格式导出（HTML/Markdown/Word/Obsidian/Notion/OneNote）
- MCP 服务（可被 AI Agent 调用）

## 🏗️ 项目架构

### 目录结构

```
src/wechat_summarizer/
├── domain/                 # 领域层（实体、值对象、领域服务）
│   ├── entities/
│   │   ├── article.py      # Article 实体
│   │   └── summary.py      # Summary 实体
│   ├── value_objects/
│   │   └── article_content.py
│   └── services/
│       └── summary_evaluator.py
│
├── application/            # 应用层（用例、端口、DTO）
│   ├── use_cases/
│   │   ├── fetch_article.py
│   │   ├── summarize_article.py
│   │   └── export_article.py
│   ├── ports/
│   │   ├── inbound/        # 输入端口
│   │   └── outbound/       # 输出端口（接口定义）
│   └── dto/
│
├── infrastructure/         # 基础设施层（适配器实现）
│   ├── adapters/
│   │   ├── scrapers/       # 文章抓取器
│   │   ├── summarizers/    # 摘要器（Simple/LLM/RAG/GraphRAG）
│   │   ├── exporters/      # 导出器
│   │   ├── embedders/      # 向量嵌入器
│   │   ├── vector_stores/  # 向量数据库
│   │   └── knowledge_graph/ # 知识图谱模块
│   ├── config/
│   │   ├── container.py    # 依赖注入容器
│   │   └── settings.py     # 配置管理
│   └── cache/
│
├── presentation/           # 展示层（CLI、GUI）
│   ├── cli/
│   │   └── commands.py
│   └── gui/
│       ├── app.py          # GUI 主应用
│       ├── components/     # UI 组件
│       ├── viewmodels/     # MVVM 视图模型
│       └── styles/         # 样式配置
│
├── mcp/                    # MCP 服务（Model Context Protocol）
│   ├── server.py           # MCP 服务器
│   ├── security.py         # 安全框架
│   └── a2a.py              # A2A 协议支持
│
└── shared/                 # 共享模块
    ├── constants.py
    ├── exceptions.py
    └── progress.py
```

### 依赖关系

```
Presentation Layer (CLI/GUI)
        ↓
Application Layer (Use Cases)
        ↓
Domain Layer (Entities/Services)
        ↑
Infrastructure Layer (Adapters)
```

**依赖规则**:
- 外层可以依赖内层，内层不能依赖外层
- Domain 层不依赖任何其他层
- Application 层定义接口（Ports），Infrastructure 层实现
- 使用依赖注入（Container）解耦

## 🔧 技术栈

### 核心依赖
- `httpx` - HTTP 客户端
- `beautifulsoup4` - HTML 解析
- `pydantic-settings` - 配置管理
- `loguru` - 日志
- `click` - CLI 框架
- `customtkinter` - GUI 框架

### 可选依赖
- `openai`, `anthropic` - AI 摘要
- `chromadb`, `sentence-transformers` - RAG
- `networkx`, `leidenalg`, `igraph` - GraphRAG
- `mcp` - MCP 服务
- `playwright` - 渲染抓取

### 开发依赖
- `pytest`, `pytest-asyncio` - 测试
- `ruff` - 代码检查
- `mypy` - 类型检查
- `pre-commit` - Git 钩子

## 💻 开发指南

### 代码风格

**命名规范**:
- 类名：`PascalCase`
- 函数/方法：`snake_case`
- 常量：`UPPER_SNAKE_CASE`
- 私有属性/方法：`_leading_underscore`

**类型注解**:
```python
from __future__ import annotations
from typing import TYPE_CHECKING

def fetch_article(url: str) -> Article:
    """所有公开函数必须有类型注解和文档字符串"""
    pass
```

**文档字符串**:
```python
def summarize(content: ArticleContent, max_length: int = 500) -> Summary:
    """生成文章摘要
    
    Args:
        content: 文章内容
        max_length: 最大摘要长度
        
    Returns:
        Summary 对象
        
    Raises:
        SummaryError: 摘要生成失败
    """
```

**导入顺序**:
1. 标准库
2. 第三方库
3. 本地模块
4. 相对导入

### 添加新功能

#### 1. 添加新的摘要器

```python
# 1. 定义端口接口（如果不存在）
# application/ports/outbound/summarizer_port.py
class SummarizerPort(Protocol):
    def summarize(self, content: ArticleContent) -> Summary:
        ...

# 2. 实现适配器
# infrastructure/adapters/summarizers/my_summarizer.py
class MySummarizer:
    @property
    def name(self) -> str:
        return "my-summarizer"
    
    @property
    def method(self) -> SummaryMethod:
        return SummaryMethod.AI
    
    def summarize(self, content: ArticleContent) -> Summary:
        # 实现逻辑
        return Summary(...)

# 3. 注册到容器
# infrastructure/config/container.py
def _create_summarizers(self) -> dict[str, SummarizerPort]:
    summarizers = {}
    # ... 其他摘要器
    summarizers["my-summarizer"] = MySummarizer()
    return summarizers
```

#### 2. 添加新的导出格式

```python
# 1. 实现导出器
# infrastructure/adapters/exporters/my_exporter.py
class MyExporter:
    def export(self, article: Article, output_path: Path) -> Path:
        # 实现导出逻辑
        return output_path

# 2. 注册到容器
# infrastructure/config/container.py
```

#### 3. 添加新的 MCP 工具

```python
# mcp/server.py
def _register_tools(mcp_instance: FastMCP) -> None:
    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def my_tool(param: str) -> dict[str, Any]:
        """工具描述"""
        try:
            # 实现逻辑
            return {"success": True, "result": "..."}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### 测试策略

**测试目录结构**:
```
tests/
├── test_domain/           # 领域层测试
├── test_application/      # 应用层测试
├── test_infrastructure/   # 基础设施层测试
├── test_presentation/     # 展示层测试
└── conftest.py           # 共享 fixtures
```

**测试标记**:
```python
@pytest.mark.unit          # 单元测试
@pytest.mark.integration   # 集成测试
@pytest.mark.slow          # 慢速测试

# 运行测试
pytest -m unit             # 只运行单元测试
pytest -m "not slow"       # 跳过慢速测试
```

**测试覆盖率**:
```bash
pytest --cov=src/wechat_summarizer --cov-report=html
```

### 配置管理

**配置文件**: `.env`
```env
# OpenAI
WECHAT_SUMMARIZER_OPENAI__API_KEY=sk-xxx
WECHAT_SUMMARIZER_OPENAI__MODEL=gpt-4o-mini

# 导出
WECHAT_SUMMARIZER_EXPORT__DEFAULT_OUTPUT_DIR=./output
```

**访问配置**:
```python
from wechat_summarizer.infrastructure.config import get_settings

settings = get_settings()
api_key = settings.openai.api_key
```

## 🔒 安全规范

### 敏感信息处理
- 使用 `SecretStr` 存储密钥
- 日志自动脱敏
- 不在代码中硬编码密钥

### SSRF 防护
- URL 验证（协议、长度、内网地址过滤）
- 使用 `SafeURLValidator`

### MCP 安全
- 工具权限控制（READ/WRITE/ADMIN）
- 审计日志记录
- 速率限制（令牌桶算法）

## 🚀 部署指南

### 安装依赖
```bash
# 基础安装
pip install -e .

# 带 AI 摘要
pip install -e .[ai]

# 完整安装
pip install -e .[full]
```

### 运行方式

**GUI 模式**:
```bash
python -m wechat_summarizer
```

**CLI 模式**:
```bash
wechat-summarizer fetch "URL" -m openai -e markdown
```

**MCP 服务**:
```bash
python -m wechat_summarizer.mcp
```

### 打包发布
```bash
# 构建
python -m build

# 发布到 PyPI
python -m twine upload dist/*
```

## ❓ 常见问题

### Q1: 如何添加新的 LLM 支持？

实现 `BaseLLMSummarizer` 子类：
```python
class MyLLMSummarizer(BaseLLMSummarizer):
    def _call_llm(self, prompt: str) -> str:
        # 调用你的 LLM API
        pass
```

### Q2: 如何扩展 GUI 功能？

1. 在 `presentation/gui/components/` 创建新组件
2. 在 `presentation/gui/viewmodels/` 创建 ViewModel
3. 在 `app.py` 中集成

### Q3: 如何调试 MCP 服务？

```bash
# 启用调试日志
export LOG_LEVEL=DEBUG
python -m wechat_summarizer.mcp

# 查看审计日志
python -c "from wechat_summarizer.mcp.security import get_security_manager; \
           print(get_security_manager().audit_logger.get_recent_logs())"
```

### Q4: 测试失败怎么办？

1. 确保安装了测试依赖：`pip install -e .[dev]`
2. 检查环境变量配置
3. 运行单个测试：`pytest tests/test_xxx.py::test_function -v`

## 📚 参考资源

- [项目仓库](https://github.com/your-org/wechat-summarizer)
- [架构文档](./docs/ARCHITECTURE.md)
- [API 文档](https://your-org.github.io/wechat-summarizer/)
- [GUI 重构指南](./docs/GUI_REFACTORING.md)
- [插件开发指南](./docs/PLUGIN_DEVELOPMENT.md)

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支：`git checkout -b feature/xxx`
3. 提交代码：`git commit -am 'Add xxx'`
4. 推送分支：`git push origin feature/xxx`
5. 提交 Pull Request

**代码审查清单**:
- [ ] 代码符合项目风格规范
- [ ] 添加了必要的测试
- [ ] 更新了文档
- [ ] 通过了所有测试
- [ ] 没有引入安全问题

---

**文档版本**: v1.0  
**最后更新**: 2026-01-27  
**维护者**: AI Assistant
