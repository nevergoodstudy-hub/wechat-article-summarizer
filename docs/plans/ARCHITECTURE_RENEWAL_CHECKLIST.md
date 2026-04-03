# 架构深度焕新执行清单（严格推进版）

> 目标：在不重写项目的前提下，完成安全、可维护性、可测试性的系统级焕新。
> 方法：按优先级 P0→P1→P2→P3 执行，所有项必须有可验证产物。

---

## 0. 执行总则（必须遵守）

- [ ] 所有改动走小步提交（每项清单可独立回滚）
- [ ] 每步完成后运行：`ruff` + `pytest`（最少核心集）
- [ ] 不允许在 `domain/` 引入 `infrastructure/presentation/mcp`
- [ ] MCP 新增工具默认：参数校验 + 权限校验 + 审计脱敏
- [ ] 每周更新风险看板（阻塞项/回滚点/覆盖率）

---

## 1. P0 紧急修复（先做，预计 5~7 天）

### P0-1 容器与测试阻断治理
- [ ] 将容器初始化彻底改为惰性加载（禁止导入即初始化外部依赖）
- [ ] 提供测试容器覆盖入口（`tests/conftest.py` 统一注入）
- [ ] 外部依赖（LLM/httpx/chromadb）在测试默认 mock/stub
- [ ] 产物：测试可执行率提升到 >= 90%

### P0-2 GUI 上帝对象彻底拆分
- [ ] 保持 `presentation/gui/app.py` 仅为薄入口（< 150 行）
- [ ] 抽离 `main_window` 协调器（页面装配+事件路由）
- [ ] 抽离 `frames`（sidebar/article/summarization/export/settings）
- [ ] 抽离 `dialogs`（导出确认/API配置/退出确认）
- [ ] 抽离 `viewmodels`（状态与命令，不直接操作复杂UI细节）
- [ ] 文件上限：单文件目标 < 400 行

### P0-3 SSRF DNS Rebinding 修复
- [ ] 实现“一次解析+固定IP连接”策略（transport 层）
- [ ] 禁止自动跟随重定向，重定向目标逐跳校验
- [ ] 拦截替代 IP 表示法（十进制/八进制/IPv6-mapped）
- [ ] 拦截云元数据地址段（如 169.254.169.254）
- [ ] 增加集成测试：DNS rebinding / redirect / alt-IP

### P0-4 MCP 输入安全加固
- [ ] 所有 `@tool` 入参统一接入 `MCPInputValidator`
- [ ] URL、路径、文本、方法名、长度限制全面校验
- [ ] 阻断命令注入字符集与危险 payload
- [ ] 错误返回统一化（业务错误 vs 校验错误）

---

## 2. P1 高优先级（预计 7~12 天）

### P1-1 架构边界自动守卫
- [ ] 新增 `scripts/check_domain_boundary.py`
- [ ] CI 强制执行 domain boundary check
- [ ] 违规依赖改为 `Protocol` 端口抽象

### P1-2 并发模型升级
- [ ] 批量并发由 `asyncio.gather` 迁移到 `TaskGroup`
- [ ] 增加并发限流（Semaphore）
- [ ] 引入 `except*` 处理 ExceptionGroup

### P1-3 MCP 审计日志脱敏
- [ ] 审计日志实现递归脱敏（dict/list/string）
- [ ] 匹配 token/api_key/password/bearer/sk- 等敏感模式
- [ ] 超长字段截断（如 >200 chars）

### P1-4 / P1-5 SSRF 补强
- [ ] 重定向链每跳合法性校验
- [ ] host、ip、cidr 黑白名单统一入口
- [ ] IP canonicalization 后再判断内网/保留地址

### P1-6 安全存储审计
- [ ] 校验 PBKDF2 盐值：随机、独立、长度>=16 bytes
- [ ] 旧数据迁移策略与兼容读取实现

### P1-7 MCP 运行权限最小化
- [ ] `security_config.py` 定义 allowed_dirs / allowed_hosts
- [ ] 危险操作增加人工确认开关（HITL）
- [ ] 远程监听默认拒绝，必须显式开启

### P1-8 测试隔离改造
- [ ] 移除跨测试共享可变状态
- [ ] 文件系统副作用统一 `tmp_path`
- [ ] 增加随机顺序执行检查（如 pytest-randomly）

---

## 3. P2 工程质量与平台化（预计 1~2 周）

### 代码质量与类型系统
- [ ] `ruff check --fix` + 手工收敛剩余关键告警
- [ ] 修复现有类型问题（progress/secure_storage/structured_logging 等）
- [ ] 引入 `mypy` 渐进严格策略（先核心模块）

### CI/CD 与供应链安全
- [ ] CI 拆分阶段：lint/type/test/security/build
- [ ] 引入 `pip-audit` 依赖漏洞扫描
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
- [ ] 边界检查进入 CI 且可阻断违规
- [ ] 并发模型完成迁移，异常可观测
- [ ] 审计日志无敏感泄露

### Phase C（P2 完成）
- [ ] CI 全链路稳定
- [ ] 类型检查覆盖核心模块
- [ ] 依赖安全扫描常态化

---

## 6. 推荐执行顺序（严格版）

1. [ ] P0-4 MCP 输入安全
2. [ ] P0-3 SSRF Rebinding
3. [ ] P0-1 容器测试阻断
4. [ ] P0-2 GUI 解耦
5. [ ] P1-1 边界守卫
6. [ ] P1-3 审计脱敏
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
