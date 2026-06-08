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

> 证据：`tests/test_container.py` 覆盖构造/全局容器惰性加载与默认最小化测试容器；`scripts/check_test_executability.py` 统计默认 `not integration` 测试可执行率，当前 846/866 = 97.7%。

### P0-2 GUI 上帝对象彻底拆分
- [x] 保持 `presentation/gui/app.py` 仅为薄入口（< 150 行）
- [x] 抽离 `main_window` 协调器（页面装配+事件路由）
- [ ] 抽离 `frames`（sidebar/article/summarization/export/settings）
- [ ] 抽离 `dialogs`（导出确认/API配置/退出确认）
- [x] 抽离 `viewmodels`（状态与命令，不直接操作复杂UI细节）
- [x] 文件上限：单文件目标 < 400 行

> 证据：`presentation/gui/app.py` 当前 110 行，仅组合 mixins、创建根窗口并委托 `MainWindow`；`main_window.py` 当前 36 行，封装 app_factory/build/run 协调入口；`viewmodels/` 已包含 `MainViewModel`、`SettingsViewModel`、`SingleProcessViewModel`、`BatchProcessViewModel` 与 ports；`app_layout.py` 将 shell 布局、页面装配、快捷键、响应式与日志面板从 bootstrap 流程中剥离，`app_bootstrap.py` 降至 167 行；`frames/home_dashboard.py` 与 `frames/home_info.py` 将首页欢迎/快捷入口/导航卡片/状态总览/最近记录/提示条从 `pages/home_page.py` 抽离，`home_page.py` 当前 83 行；本轮新增 `frames/settings_service.py`、`frames/settings_preferences.py` 与 `settings_api_actions.py`，将设置页摘要服务、API 密钥、导出、系统、性能、语言和快捷操作区从 `pages/settings_page.py` 抽离，`settings_page.py` 当前 391 行；已将 `components/border.py` 的渐变绘制、边框容器、分隔线与颜色工具拆到 `gradient_border_draw.py`、`gradient_border.py`、`divider.py`、`border_utils.py`，兼容导出入口降至 39 行，拆分后相关文件分别为 82/173/293/207 行；已将 `components/datagrid.py` 的模型、虚拟滚动、表头、行渲染、工具栏/状态栏、数据操作与手动 demo 拆到 `datagrid_models.py`、`datagrid_virtual.py`、`datagrid_header.py`、`datagrid_rows.py`、`datagrid_toolbar.py`、`datagrid_data.py`、`datagrid_demo.py`，兼容入口降至 113 行，拆分后相关文件分别为 33/118/121/113/84/129/60 行；已将 `components/input.py` 的兼容层、验证状态/颜色、浮动标签/清除按钮、单行输入、文本域、密码输入与工厂函数拆到 `input_compat.py`、`input_state.py`、`input_adornments.py`、`input_modern.py`、`input_textarea.py`、`input_password.py`、`input_factories.py`，兼容入口降至 25 行，拆分后相关文件分别为 28/69/164/195/102/28/30 行；已将 `components/tabs.py` 的兼容层、数据模型/主题色、滑动指示器、按钮渲染、选择/关闭、拖拽/键盘导航、主体组件和工厂函数拆到 `tabs_compat.py`、`tabs_models.py`、`tab_indicator.py`、`tabs_button.py`、`tabs_selection.py`、`tabs_drag.py`、`tabs_modern.py`、`tabs_factory.py`，兼容入口降至 19 行，拆分后相关文件分别为 12/66/81/103/108/53/115/24 行；已将 `utils/microinteractions.py` 的点击反馈、加载状态、脉冲/折叠动画、焦点环、注册清理管理器与手动 demo 拆到 `microinteractions_feedback.py`、`microinteractions_loading.py`、`microinteractions_motion.py`、`microinteractions_focus.py`、`microinteractions_manager.py`、`microinteractions_demo.py`，兼容入口降至 21 行，拆分后相关文件分别为 185/110/129/38/87/84 行；已将 `components/button.py` 的 CustomTkinter 兼容层、变体/尺寸模型、水波纹动画、现代按钮主体、图标按钮、按钮组和工厂函数拆到 `button_compat.py`、`button_models.py`、`button_ripple.py`、`button_modern.py`、`button_icon.py`、`button_group.py`、`button_factories.py`，兼容入口降至 22 行，拆分后相关文件分别为 19/110/84/184/34/37/30 行；已将 `utils/autosave.py` 的常量、数据模型、本地草稿加密、草稿存储、自动保存管理器、恢复对话框与手动 demo 拆到 `autosave_constants.py`、`autosave_models.py`、`autosave_encryptor.py`、`autosave_storage.py`、`autosave_manager.py`、`autosave_dialog.py`、`autosave_demo.py`，兼容入口降至 37 行，拆分后相关文件分别为 18/36/58/159/205/142/74 行；已将 `components/modal.py` 的 CustomTkinter 兼容层、尺寸模型、基础模态框、确认框、提示框和便捷工厂函数拆到 `modal_compat.py`、`modal_models.py`、`modal_base.py`、`modal_confirm.py`、`modal_alert.py`、`modal_factory.py`，兼容入口降至 23 行，拆分后相关文件分别为 17/17/244/139/130/69 行；已将 `utils/performance.py` 的常量、数据模型、计时器、核心监控器、悬浮窗、门面函数和手动 demo 拆到 `performance_constants.py`、`performance_models.py`、`performance_timer.py`、`performance_monitor.py`、`performance_overlay.py`、`performance_facade.py`、`performance_demo.py`，兼容入口降至 43 行，拆分后相关文件分别为 20/61/33/228/184/48/75 行；已将 `utils/animation.py` 的数据模型、缓动函数、动画引擎、便捷函数和手动 demo 拆到 `animation_models.py`、`animation_easing.py`、`animation_engine.py`、`animation_facade.py`、`animation_demo.py`，兼容入口降至 22 行，拆分后相关文件分别为 54/159/299/32/108 行；已将 `dialogs/word_preview.py` 的内容预览解析、共享文档渲染、窗口骨架、单篇预览和批量预览拆到 `word_preview_content.py`、`word_preview_render.py`、`word_preview_window.py`、`word_preview_single.py`、`word_preview_batch.py`，兼容入口降至 14 行，拆分后相关文件分别为 124/156/62/54/150 行；已将 `utils/accessibility.py` 的焦点模型、焦点管理器、Skip Link、方向键导航、Live Region、通用 helper 和手动 demo 拆到 `accessibility_models.py`、`accessibility_focus.py`、`accessibility_skiplink.py`、`accessibility_keyboard.py`、`accessibility_live.py`、`accessibility_helper.py`、`accessibility_demo.py`，兼容入口降至 27 行，拆分后相关文件分别为 54/177/47/46/32/50/86 行；已将 `assets/icons.py` 的图标模型、路径目录、可选运行时依赖、SVG path 解析、渲染器、缓存管理器和门面函数拆到 `icons_models.py`、`icons_paths.py`、`icons_runtime.py`、`icons_parser.py`、`icons_renderer.py`、`icons_manager.py`、`icons_facade.py`，兼容入口降至 34 行，拆分后相关文件分别为 31/50/33/254/164/130/33 行；已将 `components/sidebar.py` 的导航模型、Tooltip、状态持久化、导航项渲染/交互、展开收起动画、核心组件和手动 demo 拆到 `sidebar_models.py`、`sidebar_tooltip.py`、`sidebar_state.py`、`sidebar_items.py`、`sidebar_animation.py`、`sidebar_core.py`、`sidebar_demo.py`，兼容入口降至 22 行，拆分后相关文件分别为 46/56/84/240/70/110/61 行，并将 sidebar 用户路径测试改为显式 `Path.home()` 下路径，修复 Linux CI `/tmp` 与安全默认策略的假失败；本轮继续将 `utils/lazy.py` 的加载模型/安全限制、线程加载器、懒加载容器、图片加载、门面函数和手动 demo 拆到 `lazy_models.py`、`lazy_loader.py`、`lazy_widget.py`、`lazy_image.py`、`lazy_facade.py`、`lazy_demo.py`，兼容入口降至 34 行，拆分后相关文件分别为 50/158/145/63/18/39 行；上述已拆分文件均 <400 行，并由 `tests/test_gui_app_composition.py` 锁定组合关系、兼容导出、内容预览行为、可访问性默认模型、图标模型/路径/parser 行为、sidebar mixin 组合/状态路径校验、lazy 兼容导出与行数目标。由于仍有其它 GUI 大文件待拆，文件上限项暂不勾选；由于导出选项、设置目录选择和历史页确认等弹窗逻辑仍散落在 runtime/pages 中，`dialogs` 总项暂不勾选。

> 本轮新增证据：已将 `components/select.py` 的 CustomTkinter/Tk 兼容层、选择模式/选项模型、搜索与下拉面板渲染、主体选择器和工厂函数拆到 `select_compat.py`、`select_models.py`、`select_dropdown.py`、`select_modern.py`、`select_factory.py`，兼容入口降至 15 行，拆分后相关文件分别为 16/37/156/165/32 行；已将 `utils/clipboard_detector.py` 的检测结果/安全常量、微信链接提取与去重、剪贴板读取、浏览器活动探测和自动检测聚合拆到 `clipboard_models.py`、`clipboard_wechat.py`、`clipboard_manager.py`、`clipboard_browser.py`、`clipboard_auto.py`，兼容入口降至 17 行，拆分后相关文件分别为 20/169/32/57/90 行；已将 `utils/shortcuts.py` 的快捷键模型、偏好持久化、帮助面板、快捷键管理器和手动 demo 拆到 `shortcuts_models.py`、`shortcuts_storage.py`、`shortcuts_panel.py`、`shortcuts_manager.py`、`shortcuts_demo.py`，兼容入口降至 13 行，拆分后相关文件分别为 32/40/113/175/42 行；已将 `components/card.py` 的 CustomTkinter/Tk 兼容层、枚举模型、基础卡片、内容卡片、操作卡片、统计卡片和工厂函数拆到 `card_compat.py`、`card_models.py`、`card_base.py`、`card_content.py`、`card_action.py`、`card_stat.py`、`card_factory.py`，兼容入口降至 22 行，拆分后相关文件分别为 13/31/121/110/66/99/31 行；已将 `utils/transition.py` 的过渡枚举/配置、缓动函数、页面过渡动画、路由器和手动 demo 拆到 `transition_models.py`、`transition_easing.py`、`transition_page.py`、`transition_router.py`、`transition_demo.py`，兼容入口降至 17 行，拆分后相关文件分别为 31/49/202/71/63 行；`tests/test_gui_app_composition.py` 新增 select、clipboard、shortcuts、card 与 transition 兼容导出、mixin/模型行为、枚举值、工厂函数、路由历史和行数目标测试。当前 `presentation/gui` 下 Python 文件最高为 `components/contextmenu.py` 398 行，未发现 >=400 行文件，因此 `文件上限：单文件目标 < 400 行` 已勾选。

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
