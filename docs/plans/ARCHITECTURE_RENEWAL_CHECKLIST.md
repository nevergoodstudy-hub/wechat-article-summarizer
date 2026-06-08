# 架构深度焕新执行清单（严格推进版）

> 目标：在不重写项目的前提下，完成安全、可维护性、可测试性的系统级焕新。
> 方法：按优先级 P0→P1→P2→P3 执行，所有项必须有可验证产物。

---

## 0. 执行总则（必须遵守）

- [x] 所有改动走小步提交（每项清单可独立回滚）
- [x] 每步完成后运行：`ruff` + `pytest`（最少核心集）
- [x] 不允许在 `domain/` 引入 `infrastructure/presentation/mcp`
- [x] MCP 新增工具默认：参数校验 + 权限校验 + 审计脱敏
- [ ] 每周更新风险看板（阻塞项/回滚点/覆盖率）

---

## 1. P0 紧急修复（先做，预计 5~7 天）

### P0-1 容器与测试阻断治理
- [x] 将容器初始化彻底改为惰性加载（禁止导入即初始化外部依赖）
- [x] 提供测试容器覆盖入口（`tests/conftest.py` 统一注入）
- [x] 外部依赖（LLM/httpx/chromadb）在测试默认 mock/stub
- [x] 产物：测试可执行率提升到 >= 90%

> 证据：`tests/test_container.py` 覆盖构造/全局容器惰性加载与默认最小化测试容器；`scripts/check_test_executability.py` 统计默认 `not integration` 测试可执行率，当前 784/804 = 97.5%。

### P0-2 GUI 上帝对象彻底拆分
- [x] 保持 `presentation/gui/app.py` 仅为薄入口（< 150 行）
- [x] 抽离 `main_window` 协调器（页面装配+事件路由）
- [ ] 抽离 `frames`（sidebar/article/summarization/export/settings）
- [ ] 抽离 `dialogs`（导出确认/API配置/退出确认）
- [x] 抽离 `viewmodels`（状态与命令，不直接操作复杂UI细节）
- [ ] 文件上限：单文件目标 < 400 行

> 证据：`presentation/gui/app.py` 当前 110 行，仅组合 mixins、创建根窗口并委托 `MainWindow`；`main_window.py` 当前 36 行，封装 app_factory/build/run 协调入口；`viewmodels/` 已包含 `MainViewModel`、`SettingsViewModel`、`SingleProcessViewModel`、`BatchProcessViewModel` 与 ports；`app_layout.py` 将 shell 布局、页面装配、快捷键、响应式与日志面板从 bootstrap 流程中剥离，`app_bootstrap.py` 降至 167 行；本轮新增 `frames/home_dashboard.py` 与 `frames/home_info.py`，将首页欢迎/快捷入口/导航卡片/状态总览/最近记录/提示条从 `pages/home_page.py` 抽离，`home_page.py` 当前 66 行，首页相关文件均 <400 行，并由 `tests/test_gui_app_composition.py` 锁定组合关系与行数目标。

### P0-3 SSRF DNS Rebinding 修复
- [x] 实现“一次解析+固定IP连接”策略（transport 层）
- [x] 禁止自动跟随重定向，重定向目标逐跳校验
- [x] 拦截替代 IP 表示法（十进制/八进制/IPv6-mapped）
- [x] 拦截云元数据地址段（如 169.254.169.254）
- [x] 增加集成测试：DNS rebinding / redirect / alt-IP

> 证据：`tests/test_dns_rebinding_integration.py` 覆盖抓取器路径上的 DNS rebinding（二次解析变更为元数据 IP 且不进入 HTTPTransport）、逐跳 redirect 目标校验（跳转到 169.254.169.254 即阻断）、替代 IP 表示法（十进制整型/前导零）在连接前阻断。

### P0-4 MCP 输入安全加固
- [x] 所有 `@tool` 入参统一接入 `MCPInputValidator`
- [x] URL、路径、文本、方法名、长度限制全面校验
- [x] 阻断命令注入字符集与危险 payload
- [x] 错误返回统一化（业务错误 vs 校验错误）

> 证据：`mcp/responses.py` 统一输出 `validation/business/rate_limit/authorization` 错误类型与 `isError`；文章/分析 toolsets、速率限制、HTTP token 鉴权入口已接入统一响应；`tests/test_mcp_toolsets.py`、`tests/test_mcp.py`、`tests/test_mcp_server_composition.py` 覆盖校验错误、业务错误、限流错误和鉴权错误。

---

## 2. P1 高优先级（预计 7~12 天）

### P1-1 架构边界自动守卫
- [ ] 新增 `scripts/check_domain_boundary.py`
- [x] CI 强制执行 domain boundary check
- [x] 违规依赖改为 `Protocol` 端口抽象

### P1-2 并发模型升级
- [x] 批量并发由 `asyncio.gather` 迁移到 `TaskGroup`
- [x] 增加并发限流（Semaphore）
- [ ] 引入 `except*` 处理 ExceptionGroup

> 注：项目当前仍支持 Python 3.10，主代码暂不能直接使用 `except*` 语法；本轮已通过 `StructuredConcurrencyError` 对 Python 3.11+ 原生 `ExceptionGroup` 做兼容展开，待版本下限提升后再完成字面 `except*` 迁移。

### P1-3 MCP 审计日志脱敏
- [x] 审计日志实现递归脱敏（dict/list/string）
- [x] 匹配 token/api_key/password/bearer/sk- 等敏感模式
- [x] 超长字段截断（如 >200 chars）

### P1-4 / P1-5 SSRF 补强
- [ ] 重定向链每跳合法性校验
- [ ] host、ip、cidr 黑白名单统一入口
- [ ] IP canonicalization 后再判断内网/保留地址

### P1-6 安全存储审计
- [x] 校验 PBKDF2 盐值：随机、独立、长度>=16 bytes
- [x] 旧数据迁移策略与兼容读取实现

### P1-7 MCP 运行权限最小化
- [x] `security_config.py` 定义 allowed_dirs / allowed_hosts
- [ ] 危险操作增加人工确认开关（HITL）
- [x] 远程监听默认拒绝，必须显式开启

### P1-8 测试隔离改造
- [x] 移除跨测试共享可变状态
- [ ] 文件系统副作用统一 `tmp_path`
- [x] 增加随机顺序执行检查（如 pytest-randomly）

---

## 3. P2 工程质量与平台化（预计 1~2 周）

### 代码质量与类型系统
- [ ] `ruff check --fix` + 手工收敛剩余关键告警
- [ ] 修复现有类型问题（progress/secure_storage/structured_logging 等）
- [ ] 引入 `mypy` 渐进严格策略（先核心模块）

### CI/CD 与供应链安全
- [x] CI 拆分阶段：lint/type/test/security/build
- [x] 引入 `pip-audit` 依赖漏洞扫描
- [ ] 加入测试矩阵（Python 3.12~3.14）

### 性能与资源治理
- [ ] 内存缓存增加上限（LRU/TTL/容量阈值）
- [ ] GUI 与批处理路径加性能指标采样（耗时/内存）

---

## 4. P3 持续改进（滚动推进）

- [ ] i18n 文案抽离完整化（禁止新增硬编码）
- [ ] CLI 增加批量 JSON 标准输出
- [ ] 测试标记分层（unit/integration/e2e/slow）
- [ ] 架构 ADR 文档化（关键决策可追溯）

---

## 5. 分阶段验收标准（DoD）

### Phase A（P0 完成）
- [ ] 核心功能回归通过
- [ ] MCP 安全基线全部生效
- [ ] GUI 主入口完成瘦身并稳定运行

### Phase B（P1 完成）
- [x] 边界检查进入 CI 且可阻断违规
- [ ] 并发模型完成迁移，异常可观测
- [x] 审计日志无敏感泄露

### Phase C（P2 完成）
- [x] CI 全链路稳定
- [ ] 类型检查覆盖核心模块
- [x] 依赖安全扫描常态化

---

## 6. 推荐执行顺序（严格版）

1. [x] P0-4 MCP 输入安全
2. [x] P0-3 SSRF Rebinding
3. [x] P0-1 容器测试阻断
4. [ ] P0-2 GUI 解耦
5. [x] P1-1 边界守卫
6. [x] P1-3 审计脱敏
7. [ ] P1-2 TaskGroup 迁移
8. [ ] P1-8 测试隔离
9. [ ] P2 质量与 CI 平台化
10. [ ] P3 持续优化

---

## 7. 每日推进模板（执行时复制）

- 今日目标：
- 变更文件：
- 风险点：
- 回滚点：
- 验证结果（lint/test/security）：
- 明日阻塞项：
