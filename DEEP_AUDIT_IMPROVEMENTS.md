# 深度审计改进方案 — WeChat Article Summarizer v2.4.0

## 审计日期: 2026-02-19
## 本文档为 DEEP_AUDIT_ISSUES.md 中每个问题的详细改进方案

---

# 第一部分：P0 紧急问题修复方案

---

## 方案 P0-1: DI容器惰性初始化改造

### 目标
将容器从急切初始化改为惰性初始化，解除对测试套件的阻断。

### 改造步骤

#### 步骤1: 容器惰性化重构
修改 `src/wechat_summarizer/infrastructure/config/container.py`:

```python
# 当前问题模式（伪代码）：
class Container:
    def __init__(self):
        self.llm_client = OpenAIClient(api_key=...)  # 立即连接外部服务！
        self.scraper = HttpxScraper(...)               # 立即创建连接池！

# 改造为惰性模式：
from functools import cached_property

class Container:
    def __init__(self, config: Settings):
        self._config = config

    @cached_property
    def llm_client(self) -> LLMPort:
        """仅在首次访问时创建"""
        provider = self._config.llm_provider
        if provider == "openai":
            return OpenAIAdapter(api_key=self._config.openai_api_key)
        elif provider == "anthropic":
            return AnthropicAdapter(api_key=self._config.anthropic_api_key)
        # ...

    @cached_property
    def scraper(self) -> ScraperPort:
        return HttpxScraperAdapter(timeout=self._config.scraper_timeout)
```

#### 步骤2: 创建测试容器
创建 `tests/conftest.py` 中的测试容器覆盖：

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture(scope="session")
def mock_container():
    """提供完全mock的容器，不连接任何外部服务"""
    container = Container(config=TestSettings())
    # 覆盖所有外部依赖
    container._llm_client = AsyncMock(spec=LLMPort)
    container._scraper = AsyncMock(spec=ScraperPort)
    container._storage = MagicMock(spec=StoragePort)
    return container

@pytest.fixture(autouse=True)
def reset_container(mock_container):
    """每个测试前重置容器状态"""
    mock_container._llm_client.reset_mock()
    yield
```

#### 步骤3: 阻止模块级容器实例化
确保没有模块在导入时创建容器实例：

```python
# 错误：模块级实例化
container = Container()  # 导入即触发！

# 正确：工厂函数或延迟获取
def get_container() -> Container:
    if not hasattr(get_container, '_instance'):
        get_container._instance = Container(config=load_settings())
    return get_container._instance
```

### 验证方法
1. 运行 `pytest tests/ --co` 验证所有测试可被收集（无导入错误）
2. 运行 `pytest tests/ -x` 验证所有387个测试可执行
3. 确认无外部网络调用：`pytest tests/ --timeout=5` 在5秒内完成

### 预估工时: 2-3天

---

## 方案 P0-2: GUI app.py 上帝对象拆分

### 目标
将113KB的app.py拆分为10-15个独立组件类。

### 拆分架构

```
presentation/gui/
├── __init__.py
├── main_window.py          # 主窗口 - 薄协调器 (~200行)
├── frames/
│   ├── __init__.py
│   ├── sidebar_frame.py    # 侧边栏导航 (~150行)
│   ├── article_list_frame.py  # 文章列表管理 (~300行)
│   ├── article_detail_frame.py # 文章详情展示 (~200行)
│   ├── summarization_frame.py  # 摘要生成控制 (~250行)
│   ├── export_frame.py     # 导出选项面板 (~200行)
│   ├── settings_frame.py   # 设置面板 (~300行)
│   └── progress_overlay.py # 进度指示器 (~100行)
├── dialogs/
│   ├── __init__.py
│   ├── api_key_dialog.py   # API密钥配置对话框
│   ├── export_dialog.py    # 导出确认对话框
│   └── about_dialog.py     # 关于对话框
├── viewmodels/
│   ├── __init__.py
│   ├── article_viewmodel.py    # 文章列表ViewModel
│   ├── summary_viewmodel.py    # 摘要ViewModel
│   └── settings_viewmodel.py   # 设置ViewModel
├── widgets/
│   ├── __init__.py
│   ├── article_card.py     # 文章卡片组件
│   ├── llm_selector.py     # LLM选择器组件
│   └── url_input.py        # URL输入组件
└── event_bus.py             # GUI事件总线
```

### 拆分步骤

#### 步骤1: 创建事件总线
```python
# presentation/gui/event_bus.py
from typing import Callable, Any
from collections import defaultdict

class GUIEventBus:
    """GUI组件间的发布/订阅事件总线"""
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event_type: str, **data: Any) -> None:
        for handler in self._handlers[event_type]:
            handler(**data)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        self._handlers[event_type].remove(handler)
```

#### 步骤2: 创建MainWindow薄协调器
```python
# presentation/gui/main_window.py
import customtkinter as ctk
from .event_bus import GUIEventBus
from .frames.sidebar_frame import SidebarFrame
from .frames.article_list_frame import ArticleListFrame
# ...

class MainWindow(ctk.CTk):
    def __init__(self, container: Container):
        super().__init__()
        self.event_bus = GUIEventBus()
        self.container = container

        # 构建布局
        self.sidebar = SidebarFrame(self, self.event_bus)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = ArticleListFrame(self, self.event_bus, container)
        self.content.grid(row=0, column=1, sticky="nsew")

        # 连接事件
        self.event_bus.subscribe("navigate", self._on_navigate)
        self.event_bus.subscribe("article_selected", self._on_article_selected)
```

#### 步骤3: 逐步提取组件
按照以下顺序逐步提取，每步后运行测试验证：
1. 提取 `SidebarFrame` — 导航相关方法
2. 提取 `ArticleListFrame` — 文章列表CRUD方法
3. 提取 `SummarizationFrame` — 摘要生成相关方法
4. 提取 `ExportFrame` — 导出相关方法
5. 提取 `SettingsFrame` — 设置相关方法
6. 提取各Dialog类
7. 提取ViewModel类，将业务逻辑从Frame中分离
8. 提取可重用Widget组件

### 验证方法
1. 每步提取后运行现有GUI测试
2. 主窗口 `MainWindow.__init__` 不超过50行
3. 每个文件不超过400行
4. 无循环导入

### 预估工时: 5-8天（增量式重构）

---

## 方案 P0-3: SSRF DNS重绑定防护

### 目标
实现"解析一次，验证IP，连接已验证IP"的安全SSRF防护模式。

### 实现方案

```python
# src/wechat_summarizer/shared/utils/ssrf_protection.py
import ipaddress
import socket
from typing import Optional
import httpx

class SSRFSafeTransport(httpx.AsyncHTTPTransport):
    """自定义httpx传输层，防止DNS重绑定"""

    BLOCKED_RANGES = [
        ipaddress.ip_network("127.0.0.0/8"),       # Loopback
        ipaddress.ip_network("10.0.0.0/8"),         # RFC1918
        ipaddress.ip_network("172.16.0.0/12"),      # RFC1918
        ipaddress.ip_network("192.168.0.0/16"),     # RFC1918
        ipaddress.ip_network("169.254.0.0/16"),     # Link-local
        ipaddress.ip_network("::1/128"),             # IPv6 loopback
        ipaddress.ip_network("fe80::/10"),           # IPv6 link-local
        ipaddress.ip_network("fc00::/7"),            # IPv6 ULA
        ipaddress.ip_network("::ffff:127.0.0.0/104"),  # IPv6-mapped IPv4 loopback
    ]

    BLOCKED_HOSTNAMES = {"localhost", "instance-data", "metadata.google.internal"}

    @classmethod
    def is_ip_blocked(cls, ip_str: str) -> bool:
        """检查IP是否在封锁范围内（包括替代表示法）"""
        try:
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
            for network in cls.BLOCKED_RANGES:
                if ip in network:
                    return True
            return False
        except ValueError:
            return True  # 无效IP默认阻止

    @classmethod
    def resolve_and_validate(cls, hostname: str) -> list[str]:
        """解析DNS并验证所有返回的IP地址"""
        if hostname.lower() in cls.BLOCKED_HOSTNAMES:
            raise SSRFBlockedError(f"Blocked hostname: {hostname}")

        # 尝试直接解析为IP（处理替代表示法）
        try:
            ip = ipaddress.ip_address(hostname)
            if cls.is_ip_blocked(str(ip)):
                raise SSRFBlockedError(f"Blocked IP: {ip}")
            return [str(ip)]
        except ValueError:
            pass  # 不是IP字面量，继续DNS解析

        # DNS解析
        try:
            addr_infos = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
        except socket.gaierror:
            raise SSRFBlockedError(f"DNS resolution failed: {hostname}")

        validated_ips = []
        for info in addr_infos:
            ip_str = info[4][0]
            if cls.is_ip_blocked(ip_str):
                raise SSRFBlockedError(f"DNS resolved to blocked IP: {ip_str}")
            validated_ips.append(ip_str)

        if not validated_ips:
            raise SSRFBlockedError(f"No valid IPs for: {hostname}")

        return validated_ips

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """拦截请求，使用已验证的IP直接连接"""
        url = request.url
        hostname = url.host

        # 解析并验证IP
        validated_ips = self.resolve_and_validate(hostname)

        # 使用第一个已验证IP重写URL，保留Host头
        new_url = url.copy_with(host=validated_ips[0])
        request = httpx.Request(
            method=request.method,
            url=new_url,
            headers={**request.headers, "Host": hostname},
            content=request.content,
        )

        return await super().handle_async_request(request)


class SSRFBlockedError(Exception):
    pass
```

### 关键改进点
1. **解析一次，连接一次**: DNS解析结果直接用于连接，消除TOCTOU窗口
2. **替代IP表示法**: 使用 `ipaddress.ip_address()` 自动规范化所有格式
3. **禁用重定向**: 在httpx客户端设置 `follow_redirects=False`，手动处理重定向并验证每个目标
4. **云元数据阻止**: 封锁 `instance-data`, `metadata.google.internal` 等hostname

### 集成方式
```python
# 在httpx客户端创建时使用安全传输
safe_client = httpx.AsyncClient(
    transport=SSRFSafeTransport(),
    follow_redirects=False,  # 禁用自动重定向
    timeout=httpx.Timeout(30.0),
)
```

### 验证方法
1. 单元测试：验证各种IP格式被阻止（十进制、八进制、IPv6映射）
2. 单元测试：验证DNS重绑定场景（mock socket.getaddrinfo 返回内部IP）
3. 集成测试：使用真实DNS重绑定测试服务验证

### 预估工时: 2天

---

## 方案 P0-4: MCP服务器输入验证强化

### 目标
为MCP服务器所有工具参数添加严格输入验证和清理。

### 实现方案

#### 步骤1: 创建MCP输入验证器
```python
# src/wechat_summarizer/mcp/input_validator.py
import re
from pathlib import PurePosixPath
from urllib.parse import urlparse

class MCPInputValidator:
    """MCP工具参数验证器"""

    # 允许的URL scheme
    ALLOWED_SCHEMES = {"http", "https"}

    # 路径遍历模式
    PATH_TRAVERSAL_PATTERN = re.compile(r'\.\.[/\\]')

    # Shell注入字符
    SHELL_DANGEROUS_CHARS = set(';|&`$(){}[]!#~<>\'\"\\')

    @classmethod
    def validate_url(cls, url: str) -> str:
        """验证URL安全性"""
        parsed = urlparse(url)
        if parsed.scheme not in cls.ALLOWED_SCHEMES:
            raise MCPValidationError(f"Disallowed URL scheme: {parsed.scheme}")
        if not parsed.hostname:
            raise MCPValidationError("URL missing hostname")
        # 使用SSRF防护模块进一步验证
        SSRFSafeTransport.resolve_and_validate(parsed.hostname)
        return url

    @classmethod
    def validate_file_path(cls, path: str, allowed_dirs: list[str]) -> str:
        """验证文件路径安全性"""
        if cls.PATH_TRAVERSAL_PATTERN.search(path):
            raise MCPValidationError(f"Path traversal detected: {path}")
        resolved = PurePosixPath(path).as_posix()
        if not any(resolved.startswith(d) for d in allowed_dirs):
            raise MCPValidationError(f"Path outside allowed directories: {path}")
        return resolved

    @classmethod
    def sanitize_text(cls, text: str, max_length: int = 10000) -> str:
        """清理文本输入"""
        if len(text) > max_length:
            raise MCPValidationError(f"Input too long: {len(text)} > {max_length}")
        # 移除null字节和不可见Unicode字符（防止隐藏指令）
        text = text.replace('\x00', '')
        text = ''.join(c for c in text if c.isprintable() or c in '\n\r\t')
        return text

    @classmethod
    def validate_no_shell_injection(cls, value: str) -> str:
        """确保值不包含shell注入字符"""
        dangerous = cls.SHELL_DANGEROUS_CHARS.intersection(value)
        if dangerous:
            raise MCPValidationError(
                f"Shell injection characters detected: {dangerous}"
            )
        return value

class MCPValidationError(Exception):
    pass
```

#### 步骤2: 在每个工具处理器中应用验证
```python
# 在mcp/server.py的每个工具中添加
@mcp.tool()
async def summarize_article(url: str) -> dict:
    """摘要指定URL的文章"""
    # 输入验证
    url = MCPInputValidator.validate_url(url)
    url = MCPInputValidator.validate_no_shell_injection(url)

    # 业务逻辑...
    result = await use_case.execute(url)
    return result
```

#### 步骤3: 添加人机交互确认
```python
# 对危险操作要求确认
@mcp.tool()
async def export_to_file(path: str, format: str) -> dict:
    """导出文章到文件 — 需要用户确认"""
    path = MCPInputValidator.validate_file_path(path, allowed_dirs=["/output"])
    format = MCPInputValidator.validate_no_shell_injection(format)

    # 返回确认请求而非直接执行
    return {
        "status": "confirmation_required",
        "message": f"将导出到 {path}，格式为 {format}。请确认。",
        "action_id": generate_action_id(),
    }
```

### 验证方法
1. 测试命令注入：`"; cat /etc/passwd"`, `$(whoami)`, `` `id` ``
2. 测试路径遍历：`../../etc/passwd`, `..\\..\\windows\\system32`
3. 测试Unicode隐藏指令：包含零宽字符的输入
4. 测试超长输入：10MB字符串

### 预估工时: 2天

---

# 第二部分：P1 高优先级改进方案

---

## 方案 P1-1: 领域层边界修复

### 步骤
1. 运行依赖分析：`grep -r "from.*infrastructure" src/wechat_summarizer/domain/`
2. 将所有外部依赖替换为端口接口（Protocol类）
3. 将端口接口定义移到 `domain/ports/` 或 `application/ports/`
4. 配置 `import-linter` 或自定义检查脚本确保领域层无外部导入

### 验证
- `grep -r "from.*infrastructure\|from.*presentation\|from.*mcp" src/wechat_summarizer/domain/` 返回空

### 预估工时: 1天

---

## 方案 P1-2: asyncio.gather → TaskGroup 迁移

### 步骤
1. 全局搜索 `asyncio.gather` 使用点
2. 逐个替换为 `async with asyncio.TaskGroup() as tg:` 模式
3. 添加 `asyncio.Semaphore` 进行并发限制

```python
# 迁移前:
results = await asyncio.gather(*[scrape(url) for url in urls], return_exceptions=True)

# 迁移后:
async with asyncio.TaskGroup() as tg:
    tasks = [tg.create_task(scrape(url)) for url in urls]
# 所有任务完成后
results = [t.result() for t in tasks]

# 带并发限制:
semaphore = asyncio.Semaphore(5)  # 最多5个并发
async def limited_scrape(url):
    async with semaphore:
        return await scrape(url)

async with asyncio.TaskGroup() as tg:
    tasks = [tg.create_task(limited_scrape(url)) for url in urls]
```

### 验证
- `grep -r "asyncio.gather" src/` 返回空
- 运行现有异步测试确认无回归

### 预估工时: 1天

---

## 方案 P1-3: MCP审计日志脱敏

### 步骤
1. 创建日志脱敏过滤器
2. 对所有日志输出应用过滤器
3. 定义敏感字段列表（api_key, password, token, secret, authorization）

```python
# mcp/audit_logger.py
import re

SENSITIVE_PATTERNS = [
    (re.compile(r'(api[_-]?key|token|secret|password|authorization)\s*[=:]\s*\S+', re.I),
     r'\1=***REDACTED***'),
    (re.compile(r'(sk-|Bearer\s+)\S+'), r'\1***REDACTED***'),
]

def sanitize_log_entry(message: str) -> str:
    for pattern, replacement in SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)
    return message
```

### 预估工时: 0.5天

---

## 方案 P1-4 & P1-5: SSRF重定向验证 + 替代IP阻止

这两项已包含在 P0-3 方案的 `SSRFSafeTransport` 实现中。
- 重定向验证：`follow_redirects=False` + 手动处理
- 替代IP阻止：`ipaddress.ip_address()` 自动规范化

无额外工作量。

---

## 方案 P1-6: PBKDF2盐值验证与修复

### 验证清单
1. 检查 `_get_or_create_salt()` 是否使用 `os.urandom(16)` 生成≥16字节随机盐
2. 确认每个凭据有独立盐值（不是共享全局盐）
3. 确认盐值安全存储（不在日志或明文配置中）
4. 确认迭代次数≥100,000（NIST建议600,000+）

### 修复模板
```python
import os
import hashlib

def derive_key(password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    if salt is None:
        salt = os.urandom(32)  # 32字节随机盐
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt,
        iterations=600_000,  # NIST 2024建议
        dklen=32,
    )
    return key, salt
```

### 预估工时: 0.5天

---

## 方案 P1-7: MCP服务器权限限制

### 步骤
1. 定义MCP工具允许访问的目录白名单
2. 限制网络访问范围（仅允许访问配置的LLM API端点）
3. 添加操作审计日志

```python
# mcp/security_config.py
MCP_SECURITY = {
    "allowed_dirs": ["./output", "./exports", "./cache"],
    "allowed_network_hosts": [
        "api.openai.com",
        "api.anthropic.com",
        "open.bigmodel.cn",
    ],
    "max_file_size_mb": 50,
    "require_confirmation_for": ["export", "delete", "write"],
}
```

### 预估工时: 1天

---

## 方案 P1-8: 测试独立性修复

### 步骤
1. 运行 `pytest tests/ --randomly` 检测顺序依赖的测试
2. 对每个失败测试，分析并修复：
   - 共享全局状态 → 移到fixture中
   - 文件系统副作用 → 使用 `tmp_path` fixture
   - 容器单例 → 使用 `mock_container` fixture
3. 添加 `pytest-randomly` 到开发依赖中确保持续随机化

### 预估工时: 2天

---

# 第三部分：P2 中等优先级改进方案

---

## 方案 P2-1: Ruff代码质量修复

```bash
# 步骤1: 自动修复83%的问题
ruff check --fix src/ tests/

# 步骤2: 格式化
ruff format src/ tests/

# 步骤3: 查看剩余问题
ruff check src/ tests/ --output-format=grouped

# 步骤4: 添加到pre-commit
# pyproject.toml
[tool.ruff]
line-length = 120
target-version = "py314"
select = ["E", "F", "W", "I", "UP", "B", "SIM", "C4"]
```

### 预估工时: 0.5天

---

## 方案 P2-2: datetime.utcnow() 修复

```bash
# 全局搜索替换
grep -rn "utcnow()" src/
# 替换为 datetime.now(datetime.UTC)
```

### 预估工时: 0.5小时

---

## 方案 P2-3~P2-5: 类型错误修复

逐个修复BUG-003到BUG-006：
1. `progress.py`: 添加 `from typing import Optional`
2. `summary_evaluator.py`: 修正参数类型
3. `secure_storage.py` 和 `structured_logging.py`: 修正类型使用

### 预估工时: 0.5天

---

## 方案 P2-6: 内存缓存限制

```python
from functools import lru_cache
from cachetools import LRUCache, TTLCache

# 替换无限缓存为有限LRU缓存
article_cache = TTLCache(maxsize=1000, ttl=3600)  # 最多1000条，1小时过期
summary_cache = LRUCache(maxsize=500)              # 最多500条
```

### 预估工时: 0.5天

---

## 方案 P2-7: 添加mypy类型检查

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.14"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

```bash
# 运行类型检查
mypy src/wechat_summarizer/
```

### 预估工时: 1天（初始配置 + 修复关键类型错误）

---

## 方案 P2-8: CI/CD流水线

创建 `.github/workflows/ci.yml`:

```yaml
name: CI
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - run: pip install ruff mypy
      - run: ruff check src/ tests/
      - run: ruff format --check src/ tests/
      - run: mypy src/wechat_summarizer/

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - run: pip install -e ".[dev]"
      - run: pytest tests/ --timeout=60 -x --tb=short

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - run: pip install pip-audit
      - run: pip-audit --require-hashes --fix --dry-run
```

### 预估工时: 1天

---

## 方案 P2-9: API密钥安全存储

```python
# 使用keyring进行安全存储
import keyring

class SecureConfigManager:
    SERVICE_NAME = "wechat-summarizer"

    @classmethod
    def set_api_key(cls, provider: str, key: str) -> None:
        keyring.set_password(cls.SERVICE_NAME, f"{provider}_api_key", key)

    @classmethod
    def get_api_key(cls, provider: str) -> str | None:
        return keyring.get_password(cls.SERVICE_NAME, f"{provider}_api_key")

    @classmethod
    def delete_api_key(cls, provider: str) -> None:
        keyring.delete_password(cls.SERVICE_NAME, f"{provider}_api_key")
```

### 预估工时: 1天

---

## 方案 P2-10: 依赖漏洞扫描

```bash
# 安装
pip install pip-audit safety

# 运行扫描
pip-audit --desc on
safety check --full-report

# 添加到CI（已包含在P2-8的CI流水线中）
```

### 预估工时: 0.5天

---

# 第四部分：P3 低优先级改进方案

| 问题 | 方案 | 预估工时 |
|------|------|---------|
| P3-1: 类型检查配置 | 已包含在P2-7中 | - |
| P3-2: i18n | 使用 `gettext` 或 `babel` 提取字符串 | 3天 |
| P3-3: CLI JSON输出 | 为CLI命令添加 `--format json` 选项 | 1天 |
| P3-4: BDD测试 | 使用 `pytest-bdd` + Gherkin | 3天 |
| P3-5: 测试标记 | 添加 `@pytest.mark.unit/integration/slow` | 0.5天 |
| P3-6: 并行测试 | 安装 `pytest-xdist`，CI使用 `-n auto` | 0.5天 |
| P3-7: 简化导出器 | 对简单导出器移除不必要的抽象层 | 1天 |

---

# 实施优先级路线图

## 第1周: P0紧急修复
- [ ] P0-1: 容器惰性化 (2-3天) ← **最高优先级，解锁186个测试**
- [ ] P0-3: SSRF DNS重绑定防护 (2天)
- [ ] P0-4: MCP输入验证 (2天)

## 第2周: P0收尾 + P1启动
- [ ] P0-2: app.py拆分 — 第一阶段: SidebarFrame + ArticleListFrame (3天)
- [ ] P1-2: TaskGroup迁移 (1天)
- [ ] P1-3: 日志脱敏 (0.5天)

## 第3周: P1 + P2
- [ ] P0-2: app.py拆分 — 第二阶段: 剩余Frame + ViewModel (4天)
- [ ] P1-1: 领域层边界修复 (1天)
- [ ] P1-6: PBKDF2验证 (0.5天)
- [ ] P1-8: 测试独立性 (2天)

## 第4周: P2 批量修复
- [ ] P2-1: Ruff自动修复 (0.5天)
- [ ] P2-2~P2-5: 类型错误修复 (1天)
- [ ] P2-7: mypy配置 (1天)
- [ ] P2-8: CI/CD流水线 (1天)
- [ ] P2-9: API密钥安全存储 (1天)
- [ ] P2-10: 依赖扫描 (0.5天)

## 第5周: P3 改进
- [ ] 按需选择P3项目实施

---

## 总预估工时

| 优先级 | 预估总工时 |
|--------|-----------|
| P0 | 11-15天 |
| P1 | 5.5天 |
| P2 | 5.5天 |
| P3 | 9天（可选）|
| **总计** | **约22-26个工作日 (核心)** |
