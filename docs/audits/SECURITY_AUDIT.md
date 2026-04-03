# 安全审查报告

> 审查时间: 2026-01-16
> 审查范围: wechat-article-summarizer 项目全部代码

---

## 审查结果总览

| 类别 | 状态 | 风险等级 |
|------|------|----------|
| 敏感信息保护 | ⚠️ 需改进 | 中 |
| 输入验证 | ⚠️ 需改进 | 中 |
| 网络安全 | ⚠️ 需改进 | 中 |
| 认证授权 | ✅ 良好 | 低 |
| 依赖安全 | ✅ 良好 | 低 |
| 日志安全 | ⚠️ 需改进 | 低 |

---

## 详细审查

### 1. 敏感信息保护

#### 1.1 API 密钥存储
**文件**: `infrastructure/config/settings.py`

**现状**:
- API 密钥使用普通 `str` 类型存储
- 配置从 `.env` 文件读取，符合最佳实践
- 提供了 `.env.example` 模板

**风险**:
- 密钥可能在日志、错误信息中意外暴露
- 内存中以明文形式存在

**建议修复**:
```python
from pydantic import SecretStr

class OpenAISettings(BaseSettings):
    api_key: SecretStr = Field(default=SecretStr(""), description="API密钥")
```

#### 1.2 Token 缓存
**文件**: `infrastructure/adapters/exporters/onenote.py`

**现状**:
- OneNote OAuth token 缓存到本地 JSON 文件
- 文件存储在用户目录 `~/.wechat_summarizer/onenote_token.json`

**风险**:
- Token 文件以明文存储，其他进程可读取
- 无文件权限设置

**建议修复**:
```python
import os
import stat

def save(self, data: dict[str, Any]) -> None:
    self._path.parent.mkdir(parents=True, exist_ok=True)
    tmp = self._path.with_suffix(self._path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # 设置文件权限为仅所有者可读写
    if os.name != 'nt':  # Unix 系统
        os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
    
    tmp.replace(self._path)
```

---

### 2. 输入验证

#### 2.1 URL 验证
**文件**: `domain/value_objects/url.py`

**现状**:
- 基本 URL 格式验证 ✅
- 协议验证（http/https）❌ 未实现
- 长度限制 ❌ 未实现
- SSRF 防护 ❌ 未实现

**风险**:
- 可能被用于 SSRF 攻击访问内网服务
- 恶意超长 URL 可能导致资源耗尽

**建议修复**:
```python
import ipaddress
from urllib.parse import urlparse

@dataclass(frozen=True)
class ArticleURL:
    value: str
    
    # 私有 IP 范围
    _PRIVATE_NETWORKS = [
        ipaddress.ip_network('10.0.0.0/8'),
        ipaddress.ip_network('172.16.0.0/12'),
        ipaddress.ip_network('192.168.0.0/16'),
        ipaddress.ip_network('127.0.0.0/8'),
        ipaddress.ip_network('169.254.0.0/16'),
    ]

    def __post_init__(self) -> None:
        if not self.value:
            raise InvalidURLError("URL不能为空")
        
        # 长度限制
        if len(self.value) > 2048:
            raise InvalidURLError("URL长度超出限制(最大2048字符)")
        
        parsed = urlparse(self.value)
        
        # 协议白名单
        if parsed.scheme not in ("http", "https"):
            raise InvalidURLError(f"不支持的协议: {parsed.scheme}")
        
        if not parsed.netloc:
            raise InvalidURLError(f"无效的URL格式: {self.value}")
        
        # SSRF 防护：检查是否为内网地址
        self._check_ssrf(parsed.netloc)
    
    def _check_ssrf(self, netloc: str) -> None:
        """检查是否为内网地址"""
        # 提取主机名（去除端口）
        host = netloc.split(':')[0]
        
        # 检查常见内网域名
        dangerous_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
        if host.lower() in dangerous_hosts:
            raise InvalidURLError("不允许访问本地地址")
        
        # 尝试解析为 IP 并检查是否为私有地址
        try:
            ip = ipaddress.ip_address(host)
            for network in self._PRIVATE_NETWORKS:
                if ip in network:
                    raise InvalidURLError("不允许访问内网地址")
        except ValueError:
            # 不是 IP 地址，跳过检查（DNS 可能解析到内网）
            pass
```

#### 2.2 HTML 内容处理
**文件**: `domain/value_objects/content.py`

**现状**:
- 使用 BeautifulSoup 解析 HTML ✅
- 移除 script/style 标签 ✅
- 无 XSS 防护（导出时可能需要）

**风险等级**: 低（主要用于内容提取，非用户输入渲染）

---

### 3. 网络安全

#### 3.1 HTTP 请求
**文件**: `infrastructure/adapters/scrapers/wechat_httpx.py`

**现状**:
- 使用 httpx 库 ✅
- 支持代理配置 ✅
- 支持超时设置 ✅
- 无证书验证禁用 ✅

**建议**: 当前实现符合安全要求

#### 3.2 OneNote OAuth 流程
**文件**: `infrastructure/adapters/exporters/onenote.py`

**现状**:
- 使用标准 OAuth 2.0 设备码流程 ✅
- Token 自动刷新 ✅
- 支持 Token 过期检测 ✅

**建议**: 实现符合 Microsoft 最佳实践

---

### 4. 日志安全

#### 4.1 敏感信息泄露
**现状**:
- 日志可能包含 URL（可能含敏感参数）
- 异常堆栈可能包含配置信息

**建议修复**:
```python
# shared/utils/logger.py
def _sanitize_log_message(message: str) -> str:
    """脱敏日志消息"""
    import re
    
    # 脱敏 API 密钥
    patterns = [
        (r'(api_key|api-key|apikey)[=:]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?', r'\1=***'),
        (r'(sk-[a-zA-Z0-9]{20,})', r'sk-***'),
        (r'(Bearer\s+)[a-zA-Z0-9._-]+', r'\1***'),
    ]
    
    for pattern, replacement in patterns:
        message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
    
    return message
```

---

### 5. 依赖安全

#### 5.1 第三方库版本
**文件**: `pyproject.toml`

**审查结果**:
- `httpx>=0.25.0` - ✅ 最新稳定版
- `beautifulsoup4>=4.12.0` - ✅ 安全
- `pydantic>=2.0.0` - ✅ 最新大版本
- `openai>=1.0.0` - ✅ 官方 SDK
- `playwright>=1.40.0` - ✅ 安全

**建议**:
- 定期运行 `pip-audit` 或 `safety check` 检查依赖漏洞
- 添加 `dependabot` 或 `renovate` 自动更新

---

## 修复优先级

| 问题 | 优先级 | 修复工时 |
|------|--------|----------|
| SSRF 防护 | 🔴 高 | 1小时 |
| URL 长度限制 | 🔴 高 | 15分钟 |
| API 密钥使用 SecretStr | 🟡 中 | 30分钟 |
| Token 文件权限 | 🟡 中 | 15分钟 |
| 日志脱敏 | 🟢 低 | 1小时 |

---

## 合规性检查

- [x] 无硬编码凭证
- [x] 使用环境变量/配置文件管理敏感信息
- [x] HTTPS 通信
- [x] 使用参数化查询/请求
- [ ] 输入验证完整性（需补充）
- [ ] 日志脱敏（需补充）

---

*报告生成时间: 2026-01-16*
