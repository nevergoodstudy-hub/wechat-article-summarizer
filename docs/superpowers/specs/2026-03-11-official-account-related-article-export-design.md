# 微信公众号搜索、相关文章预览与自动导出设计
## 问题陈述
当前项目已经具备微信公众号批量抓取、登录、链接导出与摘要生成的部分基础设施，但还缺少一条完整的“按公众号搜索 → 选择公众号 → 拉取近期文章 → 按关键词筛选相关文章 → 预览并导出”的闭环 GUI 工作流。用户现在无法在图形界面中直接搜索公众号，也无法把“相关链接清单”和“内容/摘要包”作为一次操作导出。
## 当前状态
现有能力已经覆盖这个功能链路的大半基础。
- `src/wechat_summarizer/domain/entities/official_account.py` 已定义公众号实体。
- `src/wechat_summarizer/domain/entities/article_list.py` 已定义文章列表及条目聚合。
- `src/wechat_summarizer/application/ports/outbound/article_list_port.py` 已抽象文章列表抓取能力。
- `src/wechat_summarizer/infrastructure/adapters/wechat_batch/article_fetcher.py` 已能基于 `fakeid` 拉取公众号文章列表。
- `src/wechat_summarizer/infrastructure/adapters/wechat_batch/auth_manager.py` 已支持二维码登录、Cookie/Token 维护。
- `src/wechat_summarizer/infrastructure/adapters/wechat_batch/link_exporter.py` 已支持 TXT/CSV/JSON/Markdown 链接导出。
- `src/wechat_summarizer/presentation/cli/batch_commands.py` 已暴露 `mp` 相关批处理入口。

当前主要缺口有三点。
1. 还没有公众号搜索适配器，系统无法根据公众号名称或别名拿到候选账号。
2. GUI 没有一条面向公众号搜索场景的独立工作流，二维码登录、搜索、筛选、导出之间没有形成统一状态机。
3. 现有批处理 GUI 已有一定复杂度，新功能若继续堆入 `BatchPage` 或 `app.py`，会直接恶化当前正在推进的 GUI 解耦工作。
## 目标
- 在现有批处理区域内新增“公众号搜索工作流”模式，而不是单独做一个完全平行的新页面。
- 在 GUI 内直接支持二维码登录；未登录时，用户不需要切到 CLI。
- 支持按公众号名称/别名搜索候选账号，并让用户先选择账号。
- 选定账号后抓取近期文章，默认窗口为最近 `50` 篇。
- 按关键词对“标题 + 摘要”做相关文章筛选。
- 在导出前展示总文章数、命中数和命中结果预览。
- 一次导出同时产出链接清单与内容/摘要打包产物。
- 复用现有 `wechat_batch` 基础设施，并保持 `BatchPage` 继续作为壳层而不是新的 God Object。
## 非目标
- 本轮不重写整个批处理页面。
- 不把低层微信公众号逻辑重新塞回 `presentation/gui/app.py`。
- 不改变现有摘要器选择策略，只在导出链路中沿用现有摘要生成能力。
- 不在第一版中扩展为跨公众号聚合搜索；范围仅限“先选一个公众号，再在其近期文章内筛选”。
## 用户工作流
1. 用户进入批处理页面并切换到“公众号搜索模式”。
2. 如果当前未登录，界面展示二维码登录卡片。
3. 用户输入公众号查询词与相关文章关键词。
4. 系统搜索候选公众号并展示结果列表。
5. 用户选择一个公众号。
6. 系统抓取该公众号近期 `N` 篇文章，默认 `N=50`。
7. 系统基于文章标题和摘要按关键词过滤相关文章。
8. 界面展示总文章数、命中数以及命中列表预览。
9. 用户触发导出。
10. 系统导出链接清单文件与内容/摘要包，并返回导出结果与部分失败信息。
## 方案概览
采用“保留批处理入口、拆分独立工作流组件”的方案。
- `BatchPage` 只负责模式切换和组合已有/新增面板。
- 新增独立的公众号工作流面板与对应 ViewModel，承接登录、搜索、选择、预览、导出的状态编排。
- 应用层通过新的搜索 port 和三个 use case 封装业务流程。
- 基础设施层新增公众号搜索器，复用现有登录态与会话能力。
- 容器负责延迟装配新增依赖，避免页面或 GUI 入口直接构造底层对象。
## 分层设计
### Domain
延续现有 `OfficialAccount` 与 `ArticleList` 领域实体，不新增 GUI 专属领域对象。关键词匹配结果和导出结果属于应用层 DTO/结果对象，而不是下沉到 domain。
### Application
新增以下边界与用例。
- `src/wechat_summarizer/application/ports/outbound/official_account_search_port.py`
  - 根据名称/别名搜索公众号候选项。
- `src/wechat_summarizer/application/use_cases/search_official_accounts_use_case.py`
  - 封装账号搜索流程与错误归一化。
- `src/wechat_summarizer/application/use_cases/preview_related_account_articles_use_case.py`
  - 基于所选公众号抓取近期文章，按关键词做预览过滤，并返回总数/命中数/预览条目。
- `src/wechat_summarizer/application/use_cases/export_related_account_articles_use_case.py`
  - 基于预览结果执行导出，组织链接导出与内容/摘要打包，并汇总导出报告。

应用层负责：
- 参数校验与默认值落地；
- 调用搜索/文章列表/导出能力；
- 归一化失败类型与用户可展示消息；
- 组织预览与导出结果结构。
### Infrastructure
新增：
- `src/wechat_summarizer/infrastructure/adapters/wechat_batch/account_searcher.py`

职责：
- 复用 `auth_manager.py` 已维护的会话、Cookie 与 Token；
- 调用微信公众号后台搜索接口；
- 将返回结果解析为 `OfficialAccount`；
- 对登录过期、空结果、接口异常做清晰区分。

复用：
- `article_fetcher.py` 负责根据 `fakeid` 拉近期文章列表；
- `link_exporter.py` 负责链接类产物；
- 现有摘要/导出能力继续生成内容与摘要包。
### Presentation
新增 GUI 组件与 ViewModel。
- `src/wechat_summarizer/presentation/gui/components/url_batch_panel.py`
  - 从 `BatchPage` 中拆出既有 URL 批处理 UI，给新模式腾出干净入口。
- `src/wechat_summarizer/presentation/gui/components/official_account_workflow_panel.py`
  - 展示二维码登录、查询表单、候选账号、预览结果与导出状态。
- `src/wechat_summarizer/presentation/gui/viewmodels/official_account_workflow_viewmodel.py`
  - 管理状态机、输入参数、异步任务启动和 GUI 事件通知。

保留：
- `src/wechat_summarizer/presentation/gui/pages/batch_page.py`
  - 作为模式容器与装配壳层，不直接实现公众号搜索业务细节。
## 容器装配
在 `src/wechat_summarizer/infrastructure/config/container.py` 中新增延迟依赖：
- `official_account_searcher`
- `search_official_accounts_use_case`
- `preview_related_account_articles_use_case`
- `export_related_account_articles_use_case`

容器是新增依赖的唯一装配入口。`app.py` 不直接创建微信公众号搜索器、文章预览器或导出编排器。
## 状态模型
公众号工作流 ViewModel 采用显式状态机，状态集合如下：
- `unauthenticated`
- `fetching_qrcode`
- `waiting_scan`
- `scan_confirmed`
- `authenticated`
- `searching_accounts`
- `account_selected`
- `previewing_articles`
- `ready_to_export`
- `exporting`
- `completed`
- `failed`

关键状态流转：
- 未登录时先进入二维码链路；登录成功后才允许搜索。
- 账号选择后才能进入文章预览。
- 预览成功且命中结果可导出时进入 `ready_to_export`。
- 导出结束后进入 `completed`；任一步骤失败进入 `failed`，同时保留可恢复信息。
## 数据与交互规则
- 默认文章窗口：最近 `50` 篇。
- 关键词匹配范围：文章标题 + 摘要。
- 搜索顺序：先搜公众号候选，再选一个账号，再做文章过滤。
- 无结果不是系统错误；需要区分“搜索无结果”“预览无命中”和“接口失败/登录失效”。
- 保持现有摘要器选择行为；新功能不引入新的摘要策略开关。
## 错误处理与取消
第一版必须覆盖以下错误面：
- 二维码拉取失败；
- 二维码过期；
- 登录已失效或中途过期；
- 公众号搜索无结果；
- 公众号搜索接口失败；
- 文章列表拉取失败；
- 关键词过滤后零命中；
- 导出过程中部分文章失败；
- 用户取消当前步骤。

处理原则：
- 对“无结果”与“真实失败”使用不同 UI 文案和状态。
- 导出发生部分失败时，保留已成功输出的文件，并在报告中记录失败项。
- 取消操作需要使 ViewModel 回到稳定状态，避免卡死在中间 loading。
## 导出结构
输出目录建议采用：

`output/<timestamp>_<account>_<keyword>/`

目录内至少包含：
- `matched_links.csv`
- `matched_links.md`
- `search_result.json`
- `export_report.json`
- `articles.zip`

`articles.zip` 第一版内容：
- 每篇文章对应一个 Markdown 文件；
- `manifest.json` 记录文章元数据、导出状态、摘要状态与源链接。
## 测试策略
### Infrastructure
- 为 `account_searcher.py` 编写搜索结果解析、登录过期、空结果、异常响应测试。
### Application
- 为三个新用例分别覆盖：
  - 正常搜索；
  - 搜索无结果；
  - 预览命中与零命中；
  - 导出成功；
  - 部分导出失败但总体完成。
### Presentation
- 为 `official_account_workflow_viewmodel.py` 编写状态流转测试。
- 为 `BatchPage` 的模式切换与新面板装配编写 GUI/视图层测试。

完成后至少验证：
- `pytest` 新增目标测试；
- `ruff check`
- `mypy src/wechat_summarizer --ignore-missing-imports`
- `python scripts/check_domain_boundary.py`
## 验收标准
1. GUI 内可完成二维码登录。
2. 能按公众号名称或别名搜索并返回候选账号。
3. 选择账号后可抓取近期文章并按关键词过滤。
4. 预览界面可展示总数、命中数和命中列表。
5. 一次导出可同时产出链接清单和内容/摘要包。
6. 部分失败不会抹掉已成功生成的输出。
7. `presentation/gui/app.py` 不新增底层微信公众号实现细节。
8. `BatchPage` 保持为壳层，不退化成新的 God Object。
9. 变更通过目标测试、`ruff`、`mypy` 和 domain boundary 检查。
## 后续执行约束
实现阶段应遵循 TDD，并在可用时使用多代理并行拆分：
- 一条实现线负责基础设施搜索器与应用用例；
- 一条实现线负责 GUI 面板与 ViewModel；
- 一条实现线负责测试补齐与最终验证。

所有实现都必须建立在本设计约束之上，尤其要避免重新把 GUI 编排和基础设施细节耦合回 `app.py`。
