# 📰 微信公众号文章总结器

将微信公众号文章抓取后生成摘要，并导出为 HTML / Markdown（支持写入 Obsidian Vault、创建 Notion 页面、写入 OneNote）。

OneNote 导出基于 Microsoft Graph（设备码授权 + 本地 token 缓存）。

## ✨ 功能特性

- 🔗 自动抓取微信公众号文章内容
- 📝 智能生成文章摘要（simple / Ollama / OpenAI / Anthropic / 智谱）
- 🧪 **RAG 增强摘要** - 基于向量检索的智能摘要，提升长文摘要质量
- 🕸️ **GraphRAG 全局摘要** - 基于知识图谱的全局理解，适合复杂长文分析
- 📄 导出为 HTML / Markdown（可选：Obsidian / Notion / OneNote）
- 💾 本地缓存（避免重复抓取）
- ✅ 现代化 GUI 界面（支持深色/浅色主题，MVVM 架构）
- 🆕 **2026年GUI设计趋势重构** - 液态玻璃效果/微交互动画/无障碍支持
- 🆕 **知识图谱查看器** - 支持 GraphRAG 可视化，力导向布局
- ⌨️ 命令行工具支持
- 🤖 **MCP 服务支持** - 可被 AI Agent（Claude/ChatGPT）直接调用

## 🏗️ 架构

采用 **Clean Architecture / Hexagonal** 设计：

```text
src/wechat_summarizer/
├── domain/           # 领域层（实体/值对象/领域服务）
├── application/      # 应用层（用例编排/端口/DTO）
├── infrastructure/   # 基础设施层（抓取器/摘要器/导出器/配置与容器）
├── presentation/     # 展示层（CLI/GUI）
└── shared/           # 共享工具/常量/异常
```

## 🚀 快速开始

### 安装

```bash
# 克隆项目
cd wechat-article-summarizer

# 安装依赖
pip install -e .

# 可选：启用 AI 摘要（OpenAI / Anthropic 等）
pip install -e .[ai]

# 可选：启用 Playwright 渲染抓取
pip install -e .[playwright]
playwright install chromium

# 可选：启用 RAG 增强摘要
pip install -e .[rag]

# 可选：启用 GraphRAG 全局摘要（知识图谱）
pip install -e .[graphrag]
```

### 使用

#### GUI 模式（默认）

```bash
python -m wechat_summarizer
```

#### CLI 模式

推荐安装后直接使用脚本：

```bash
# 帮助
wechat-summarizer --help

# 抓取 +（可选）摘要 +（可选）导出
wechat-summarizer fetch "https://mp.weixin.qq.com/s/xxx" -m simple -e html
wechat-summarizer fetch "https://mp.weixin.qq.com/s/xxx" -m openai -e markdown -o output.md

# 导出到 Obsidian Vault（需要配置 export.obsidian_vault_path）
wechat-summarizer fetch "https://mp.weixin.qq.com/s/xxx" -m simple -e obsidian

# 导出到 Notion（需要配置 export.notion_api_key / export.notion_database_id）
wechat-summarizer fetch "https://mp.weixin.qq.com/s/xxx" -m simple -e notion

# 导出到 OneNote（需要先授权；并配置 export.onenote_*）
wechat-summarizer onenote-auth
wechat-summarizer fetch "https://mp.weixin.qq.com/s/xxx" -m simple -e onenote

# 使用 RAG 增强摘要（需安装 rag 依赖）
wechat-summarizer fetch "https://mp.weixin.qq.com/s/xxx" -m rag-openai -e markdown

# 使用 GraphRAG 全局摘要（需安装 graphrag 依赖）
# Local Search: 基于实体上下文的检索
wechat-summarizer fetch "https://mp.weixin.qq.com/s/xxx" -m graphrag-openai -e markdown
# Global Search: 基于社区摘要的全局分析（适合复杂问题）
wechat-summarizer fetch "https://mp.weixin.qq.com/s/xxx" -m graphrag-openai --global-search

# 兼容旧命令名：process = fetch
wechat-summarizer process "https://mp.weixin.qq.com/s/xxx" -m ollama

# 只查看文章信息（不生成摘要/不导出）
wechat-summarizer info "https://mp.weixin.qq.com/s/xxx"

# 从 CLI 启动 GUI
wechat-summarizer gui
```

也支持模块方式（更便于调试）：

```bash
python -m wechat_summarizer fetch "https://mp.weixin.qq.com/s/xxx"
python -m wechat_summarizer cli fetch "https://mp.weixin.qq.com/s/xxx"  # 兼容旧写法
```

#### MCP 服务模式

启用 MCP 服务后，AI Agent（如 Claude、ChatGPT）可直接调用本工具：

```bash
# 安装 MCP 依赖
pip install -e .[mcp]

# 启动 MCP 服务器 (stdio 模式)
python -m wechat_summarizer.mcp

# HTTP 模式
python -m wechat_summarizer.mcp --transport http
```

**提供的 MCP 工具：**

**基础工具**：
- `fetch_article` - 抓取文章内容
- `summarize_article` - 抓取并摘要文章
- `get_article_info` - 获取文章基本信息
- `batch_summarize` - 批量摘要多篇文章
- `list_available_methods` - 列出可用摘要方法

**🆕 GraphRAG 工具**：
- `graph_analyze` - 知识图谱分析（实体/关系/社区）
- `compare_articles` - 多文章对比分析
- `track_topic` - 主题追踪工具
- `evaluate_summary` - 摘要质量评估

**🔒 管理工具**：
- `get_audit_logs` - 获取审计日志（需管理员权限）

**安全特性**：
- ✅ 工具权限控制（只读/读写/管理员）
- ✅ 审计日志（记录所有调用）
- ✅ 速率限制（令牌桶算法）
- ✅ 参数脱敏（敏感信息过滤）

**A2A 协议支持**：
- 🤝 Agent Card 能力发现
- 🤝 任务管理与协作
- 🤝 跨 Agent 任务委托

## ⚙️ 配置

创建 `.env` 文件配置环境变量：

缓存说明：抓取结果默认缓存在用户目录 `.wechat_summarizer/cache`（如需清理可手动删除该目录）。

推荐使用带前缀的嵌套变量（与 Pydantic Settings 完全一致）：

```env
# OpenAI（可选，用于 AI 总结）
WECHAT_SUMMARIZER_OPENAI__API_KEY=sk-xxx
WECHAT_SUMMARIZER_OPENAI__BASE_URL=https://api.openai.com/v1
WECHAT_SUMMARIZER_OPENAI__MODEL=gpt-4o-mini

# Anthropic（可选）
WECHAT_SUMMARIZER_ANTHROPIC__API_KEY=sk-ant-xxx
WECHAT_SUMMARIZER_ANTHROPIC__MODEL=claude-3-haiku-20240307

# 智谱（可选）
WECHAT_SUMMARIZER_ZHIPU__API_KEY=xxx
WECHAT_SUMMARIZER_ZHIPU__MODEL=glm-4-flash

# 导出
WECHAT_SUMMARIZER_EXPORT__DEFAULT_OUTPUT_DIR=./output
WECHAT_SUMMARIZER_EXPORT__OBSIDIAN_VAULT_PATH=/path/to/your/vault
WECHAT_SUMMARIZER_EXPORT__NOTION_API_KEY=secret_xxx
WECHAT_SUMMARIZER_EXPORT__NOTION_DATABASE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# OneNote（Microsoft Graph）
# 说明：Notebook 必须已存在；Section 不存在会自动创建。
# 第一次使用需要：wechat-summarizer onenote-auth
WECHAT_SUMMARIZER_EXPORT__ONENOTE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
WECHAT_SUMMARIZER_EXPORT__ONENOTE_TENANT=common
WECHAT_SUMMARIZER_EXPORT__ONENOTE_NOTEBOOK=MyNotebook
WECHAT_SUMMARIZER_EXPORT__ONENOTE_SECTION=WeChat Summaries

# 抓取器
WECHAT_SUMMARIZER_SCRAPER__MAX_RETRIES=3
WECHAT_SUMMARIZER_SCRAPER__USE_PLAYWRIGHT=false
```

兼容旧变量名（项目也支持，但不推荐新项目继续用）：

```env
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
OUTPUT_DIR=./output
```

## 📦 依赖

- Python 3.10+
- httpx - HTTP 客户端
- beautifulsoup4 - HTML 解析
- customtkinter - 现代 GUI
- click - CLI 框架
- pydantic-settings - 配置管理
- loguru - 日志
- psutil - 性能监控

### RAG 增强摘要可选依赖

- chromadb - 向量数据库（持久化存储）
- sentence-transformers - 本地嵌入模型

### GraphRAG 可选依赖

- networkx - 图数据结构与算法
- igraph - 高性能图分析库
- leidenalg - Leiden 社区检测算法

## 📋 文档

### 🌟 新手入门
- **[🚀 新手教程](./docs/GETTING_STARTED.md)** - 从零开始，手把手教你使用本工具

### 📚 开发文档
- **[AGENTS.md](./AGENTS.md)** - 🤖 **AI 编码助手指引** (新增)
- [docs/ITERATION_ROADMAP.md](./docs/ITERATION_ROADMAP.md) - 🚀 **迭代改进路线图**
- [IMPROVEMENT_PLAN.md](./IMPROVEMENT_PLAN.md) - 项目改进开发计划
- [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) - 安全审查报告
- [docs/CONTRIBUTING.md](./docs/CONTRIBUTING.md) - 贡献指南
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) - 架构文档
- [docs/GUI_REFACTORING.md](./docs/GUI_REFACTORING.md) - GUI 重构指南

### 🎨 GUI 现代化重构 (2026趋势)

本项目GUI已全面升级，采用最新设计趋势：

**视觉系统**：
- 💧 液态玻璃效果 (Liquid Glass) - 半透明模糊背景
- 🎨 动态渐变色系统 - 支持线性/径向渐变动画
- 🎴 现代卡片组件 - 4级阴影深度 + hover微动画
- 📝 字体系统 - Inter/思源黑体 + 8级字阶

**组件库**：
- 🔘 ModernButton - Ripple水波纹/Loading状态/4种变体
- 📋 VirtualList - 10万+数据量/只渲染可见区域/60fps
- 📢 Toast/Notification - 堆叠管理/自动消失
- 📀 DataGrid - 虚拟滚动/列排序/行选择
- 📊 ContextMenu - 右键菜单/智能位置

**性能优化**：
- ⚡ 组件懒加载 (LazyLoader) - 路由级代码分割
- 📊 性能监控 (PerformanceMonitor) - FPS/内存/CPU实时追踪
- 🔄 滚动节流 - 16ms/60fps

**无障碍支持**：
- ⌨️ 键盘导航 - Tab顺序/焦点轮廓/SkipLinks
- 🔍 设置缩放 - 80%-200%字体缩放
- 🌓 高对比度模式 - WCAG AA/AAA级刹色对比度
- 🌐 RTL布局支持 - 阿拉伯语/希伯来语

## 📝 更新日志

详细变更请查看 [CHANGELOG.md](./CHANGELOG.md)。

## 📜 许可证

MIT License
