# 贡献指南

感谢您对微信公众号文章总结器项目的关注！本文档将帮助您了解如何为项目做出贡献。

## 开发环境设置

### 1. 克隆项目

```bash
git clone https://github.com/your-username/wechat-article-summarizer.git
cd wechat-article-summarizer
```

### 2. 创建虚拟环境

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. 安装开发依赖

```bash
pip install -e .[dev]
```

### 4. 配置 pre-commit

```bash
pre-commit install
```

## 代码规范

### 代码风格

- 使用 **ruff** 进行代码格式化和 lint
- 使用 **mypy** 进行类型检查
- 遵循 PEP 8 规范
- 所有公共函数和类必须有 docstring

### 运行代码检查

```bash
# 格式化代码
ruff format .

# 检查代码质量
ruff check .

# 类型检查
mypy src/
```

## 测试规范

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行单元测试
pytest tests/ -m unit

# 运行集成测试
pytest tests/ -m integration

# 带覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

### 测试要求

- 所有新功能必须包含单元测试
- 测试覆盖率应保持在 80% 以上
- 测试文件命名格式：`test_<module>.py`
- 测试函数命名格式：`test_<function>_<scenario>`

## 提交规范

使用约定式提交（Conventional Commits）格式：

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Type 类型

- **feat**: 新功能
- **fix**: Bug 修复
- **docs**: 文档更新
- **style**: 代码格式（不影响代码运行的变动）
- **refactor**: 代码重构
- **perf**: 性能优化
- **test**: 测试相关
- **chore**: 构建过程或辅助工具的变动

### 示例

```
feat(scraper): 添加通用网页抓取器

- 支持任意 HTTP/HTTPS 网页抓取
- 使用启发式算法提取正文内容
- 支持异步抓取

Closes #123
```

## 架构说明

项目采用 **DDD + 六边形架构**：

```
src/wechat_summarizer/
├── domain/           # 领域层（实体/值对象/领域服务）
├── application/      # 应用层（用例编排/端口/DTO）
├── infrastructure/   # 基础设施层（抓取器/摘要器/导出器）
├── presentation/     # 展示层（CLI/GUI）
└── shared/           # 共享工具/常量/异常
```

### 添加新功能的步骤

1. **定义领域模型**（如需要）在 `domain/` 下
2. **定义端口接口** 在 `application/ports/`
3. **实现适配器** 在 `infrastructure/adapters/`
4. **创建/更新用例** 在 `application/use_cases/`
5. **更新展示层** 在 `presentation/`
6. **编写测试** 在 `tests/`

## Pull Request 流程

1. Fork 项目并创建新分支
2. 实现功能并编写测试
3. 确保所有测试通过
4. 提交 PR 并填写描述模板
5. 等待代码审查

## 问题反馈

- 使用 GitHub Issues 报告 Bug
- 提交 Issue 前请先搜索是否已存在相同问题
- 提供详细的复现步骤和环境信息

## 许可证

本项目采用 MIT 许可证，贡献的代码也将遵循此许可证。
