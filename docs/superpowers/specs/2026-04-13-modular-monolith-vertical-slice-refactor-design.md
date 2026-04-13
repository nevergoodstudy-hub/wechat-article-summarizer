# 2026-04-13 架构重构设计：模块化单体 + 垂直切片 + 薄组合根

## 1. 背景

当前项目同时承载：

- GUI 桌面入口
- CLI 入口
- MCP Server 入口
- 多类基础设施适配器（Scraper / Summarizer / Exporter / RAG / GraphRAG）

虽然项目名义上采用了 DDD + 六边形架构，但在实际代码中仍存在几个典型“回胖点”：

- `src/wechat_summarizer/mcp/server.py` 同时承担注册、编排、业务逻辑和 HTTP 适配
- `src/wechat_summarizer/infrastructure/config/container.py` 逐渐演化为超大组合根
- `src/wechat_summarizer/presentation/gui/app.py` 仍然是 GUI 的高耦合协调中心

这说明项目当前更需要的是 **边界收口 + 组合根瘦身 + 纵向工作流收编**，而不是一次性把仓库拆成大量独立服务。

---

## 2. 外部依据（2026 仍可直接采用）

### 2.1 Monolith First

- Martin Fowler: [Monolith First](https://martinfowler.com/bliki/MonolithFirst.html)

对本项目的直接含义：

- 这个项目没有明显的独立部署边界
- GUI / CLI / MCP 都共享同一领域模型和大部分应用用例
- 当前主要问题是模块边界和组合根，而不是跨服务伸缩

因此，**先把单体做模块化**，比贸然拆微服务更符合工程现实。

### 2.2 Dependency Composition / Composition Root

- Martin Fowler: [Reducing Coupling Through Dependency Composition](https://martinfowler.com/articles/dependency-composition.html)

对本项目的直接含义：

- 依赖注入容器不是业务中心，而应是“最后组装”的位置
- 业务编排不应散落在组合根里
- 组合根应该只负责接线，业务流程应下沉到 feature / service / use case

### 2.3 FastMCP 官方组合模式

- FastMCP: [Composition Patterns](https://gofastmcp.com/patterns/composition)

对本项目的直接含义：

- MCP Server 最适合采用可组合 `toolsets` / `resources` / `sub-app` 风格
- 不应继续把所有工具和资源内联进单一 `server.py`
- MCP 入口文件应退化为一个“薄装配层”

### 2.4 Python 官方结构化并发

- Python 3.14 文档: [asyncio.TaskGroup](https://docs.python.org/3/library/asyncio-task.html#task-groups)

对本项目的直接含义：

- 批量抓取 / 批量摘要 / GUI 后台任务更适合结构化并发
- 未来继续重构异步批处理时，应优先走 `TaskGroup` 而不是扩散式 `gather(return_exceptions=True)`

### 2.5 PyPA 官方插件发现机制

- PyPA: [Creating and discovering plugins](https://packaging.python.org/guides/creating-and-discovering-plugins/)

对本项目的直接含义：

- 当前项目已经有 `entry_points` 风格插件基础
- 这意味着“扩展性”完全可以通过 **插件边界** 达成，而不必强制拆服务
- 适配器生态更适合插件化，而不是服务化

---

## 3. 备选方案对比

### 方案 A：继续维持现状，只做零散清理

优点：

- 改动最小
- 风险低

缺点：

- 组合根继续膨胀
- `server.py` / `container.py` / `app.py` 还会持续回胖
- 后续 AI、RAG、MCP 新能力只会继续堆在横向层里

结论：

- 只能止痛，不能治本

### 方案 B：拆成多个微服务 / 子进程服务

优点：

- 理论上部署边界更清晰
- 某些推理能力可独立扩容

缺点：

- 桌面 GUI 项目会显著增加分发和运维复杂度
- CLI / GUI / MCP 共享模型将被迫跨进程通信
- 目前没有明确的团队规模、运维能力和独立伸缩需求来支撑这一成本

结论：

- 对当前项目属于过度设计

### 方案 C：模块化单体 + 垂直切片 + 薄组合根 + 插件扩展

优点：

- 保留单仓、单进程、单分发优势
- 把“横向分层代码”逐步收编成“按业务工作流组织”的 feature slice
- 组合根变薄后更容易测试、更容易替换入口
- 与现有插件系统天然兼容

缺点：

- 需要持续迁移，不能一蹴而就
- 需要明确 feature 边界，避免重新长成“伪 feature 目录”

结论：

- **这是当前项目最可行、最新且性价比最高的路线**

---

## 4. 选型结论

本项目推荐采用：

> **模块化单体（Modular Monolith） + 垂直切片（Vertical Slices） + 薄组合根（Thin Composition Root） + 插件化扩展边界（Plugin-first Extension Boundary）**

并采用以下迁移策略：

> **Monolith First + Branch by Abstraction**

也就是：

- 不搞大爆炸式重写
- 不直接切微服务
- 先抽出 feature service / toolset / resource / runtime adapter
- 再逐步把旧的横向编排代码替换掉

---

## 5. 为什么它最适合这个项目

### 5.1 与项目交付形态匹配

这个项目本质上是一个“多入口、单核心”的桌面/本地工具：

- GUI、CLI、MCP 共用同一领域模型和大部分用例
- 没有明显需要单独部署的业务域
- 目前主要矛盾是可维护性，而不是服务级吞吐

所以它更适合：

- 一个强内聚单体
- 多个清晰模块
- 多个薄入口

而不是多服务拆分。

### 5.2 与现有代码基础匹配

项目已经具备：

- 领域模型
- Use Case
- DI Container
- 插件系统

这意味着并不需要推倒重来，只要改变“组合和编排方式”即可。

### 5.3 与 AI/MCP 演进方向匹配

MCP 工具、资源、工作流最怕“大文件内联注册”。FastMCP 官方也明确给出了组合模式，因此：

- 把 MCP 改成组合式 toolset/resource
- 把 article fetch/summarize 收编为 feature slice

是当前最顺势的一步。

---

## 6. 目标架构轮廓

### 6.1 结构原则

保留现有层次，但让业务工作流优先落在 feature 层：

```text
domain/
application/
features/
  article_workflow/
  batch_workflow/        # 下一批
  export_workflow/       # 下一批
infrastructure/
presentation/
mcp/
  toolsets/
  resources/
  server.py              # 仅做组合
```

### 6.2 责任划分

- `domain/`: 业务规则、不变量、领域对象
- `application/`: 用例与端口
- `features/`: 面向入口层的“工作流编排”
- `infrastructure/`: 适配器与外部依赖
- `presentation/`: GUI / CLI 展示层
- `mcp/`: MCP 入口适配层，不直接承载业务逻辑

### 6.3 组合根原则

以下文件都应被持续“瘦身”：

- `infrastructure/config/container.py`
- `mcp/server.py`
- `presentation/gui/app.py`

它们的理想状态是：

- 只做装配
- 不做复杂业务
- 不直接堆积多分支流程

---

## 7. 本轮已落地的第一批重构

### 7.1 新增 article workflow 垂直切片

新增：

- `src/wechat_summarizer/features/article_workflow/dto.py`
- `src/wechat_summarizer/features/article_workflow/service.py`

作用：

- 把“抓取文章 / 获取预览 / 生成摘要 / 批量摘要”整合为面向入口层的工作流服务
- 入口层不再直接组装 `fetch_use_case + summarize_use_case`

### 7.2 MCP 组合式拆分

新增：

- `src/wechat_summarizer/mcp/toolsets/article_tools.py`
- `src/wechat_summarizer/mcp/toolsets/analysis_tools.py`
- `src/wechat_summarizer/mcp/resources/article_content.py`

作用：

- 按工具集和资源集拆开
- `server.py` 退回到组合根角色

### 7.3 Container 缓存失效修正

补充：

- `reload_summarizers()` 现在同步失效 `article_workflow_service` 和 `evaluator`

作用：

- 防止 GUI 保存密钥后仍拿到旧的工作流实例 / 旧评估器

---

## 8. 后续建议的迁移顺序

### Batch 2：GUI 工作流切片化

优先把以下流程抽成 feature / coordinator：

- 单篇处理工作流
- 批量处理工作流
- 导出工作流

目标：

- `presentation/gui/app.py` 继续瘦身
- 页面逻辑只调用 ViewModel / feature service

### Batch 3：Container 模块化装配

把超长 `container.py` 拆成：

- `container_scrapers.py`
- `container_summarizers.py`
- `container_exporters.py`
- `container_runtime.py`

主容器只保留：

- 缓存字段
- 属性装配
- 生命周期控制

### Batch 4：结构化并发统一

把批处理、GUI 后台任务、MCP 批量工具进一步统一到：

- `TaskGroup`
- 限流
- 可取消
- 可观测异常分组

---

## 9. 风险与边界

### 风险 1：feature 目录沦为“另一层大杂烩”

规避方法：

- feature 只放工作流，不放底层适配器
- feature 命名按业务动作而不是技术层命名

### 风险 2：Container 和 feature 双重编排

规避方法：

- Container 只创建对象
- feature 才负责编排多个 use case

### 风险 3：GUI / MCP 各自复制工作流

规避方法：

- 统一复用 feature service
- 不允许入口层重复拼装核心流程

---

## 10. 最终判断

从 2026 的工程实践视角看，这个项目最值得采用的不是“更分布式”，而是“更模块化、更组合式、更可替换”：

- **单体继续保留**
- **业务流程按切片归拢**
- **入口文件变薄**
- **插件继续承担扩展职责**
- **并发和可观测性作为第二阶段统一升级**

这条路线既符合最新可用的架构经验，也最适合当前仓库的真实形态与风险水平。
