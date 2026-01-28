"""配置管理 - 基于Pydantic Settings

注意：该项目同时兼容两类环境变量：
1) 推荐：WECHAT_SUMMARIZER_ 前缀 + 双下划线嵌套（Pydantic Settings 原生支持）
2) 兼容：历史/简化变量名（如 OPENAI_API_KEY、OPENAI_BASE_URL、OUTPUT_DIR）

兼容逻辑实现于 get_settings()：会从 OS 环境变量与 .env 文件读取并回填到 settings 对象。
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from ...shared.constants import (
    CONFIG_DIR_NAME,
    CONFIG_FILE_NAME,
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_DEEPSEEK_BASE_URL,
    DEFAULT_DEEPSEEK_MODEL,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_ZHIPU_MODEL,
)


class ScraperSettings(BaseSettings):
    """抓取器配置"""

    timeout: int = Field(default=30, description="请求超时秒数")
    max_retries: int = Field(default=3, description="最大重试次数")
    use_playwright: bool = Field(default=False, description="是否优先使用Playwright")
    user_agent_rotation: bool = Field(default=True, description="是否启用UA轮换")
    proxy: str | None = Field(default=None, description="代理服务器地址")


class OllamaSettings(BaseSettings):
    """Ollama配置"""

    host: str = Field(default=DEFAULT_OLLAMA_HOST, description="Ollama服务地址")
    model: str = Field(default=DEFAULT_OLLAMA_MODEL, description="使用的模型")
    timeout: int = Field(default=120, description="请求超时秒数")


class OpenAISettings(BaseSettings):
    """OpenAI配置"""

    api_key: SecretStr = Field(default=SecretStr(""), description="API密钥")
    base_url: str | None = Field(default=None, description="API基础URL（用于代理）")
    model: str = Field(default=DEFAULT_OPENAI_MODEL, description="使用的模型")


class DeepSeekSettings(BaseSettings):
    """DeepSeek配置
    
    DeepSeek 是国产高性能大语言模型，提供与 OpenAI 兼容的 API 接口。
    支持 deepseek-chat (DeepSeek V3) 和 deepseek-coder 等模型。
    """

    api_key: SecretStr = Field(default=SecretStr(""), description="DeepSeek API密钥")
    base_url: str = Field(default=DEFAULT_DEEPSEEK_BASE_URL, description="DeepSeek API基础URL")
    model: str = Field(default=DEFAULT_DEEPSEEK_MODEL, description="使用的模型")


class AnthropicSettings(BaseSettings):
    """Anthropic配置"""

    api_key: SecretStr = Field(default=SecretStr(""), description="API密钥")
    model: str = Field(default=DEFAULT_ANTHROPIC_MODEL, description="使用的模型")


class ZhipuSettings(BaseSettings):
    """智谱AI配置"""

    api_key: SecretStr = Field(default=SecretStr(""), description="API密钥")
    model: str = Field(default=DEFAULT_ZHIPU_MODEL, description="使用的模型")


class BatchSettings(BaseSettings):
    """批量获取配置
    
    配置公众号文章批量获取相关的参数。
    """

    # 请求频率控制
    request_interval: float = Field(
        default=3.0,
        description="请求间隔秒数（推荐2-5秒）",
    )
    max_requests_per_minute: int = Field(
        default=20,
        description="每分钟最大请求数",
    )
    
    # 文章获取限制
    max_articles_per_account: int = Field(
        default=500,
        description="单个公众号每日最大获取文章数",
    )
    page_size: int = Field(
        default=10,
        description="每页文章数（API限制最大10）",
    )
    
    # 缓存配置
    cache_enabled: bool = Field(
        default=True,
        description="是否启用文章列表缓存",
    )
    cache_ttl_hours: int = Field(
        default=24,
        description="缓存有效期（小时）",
    )
    cache_dir: str = Field(
        default=".cache/wechat_batch",
        description="缓存目录",
    )
    
    # 认证配置
    credentials_file: str = Field(
        default=".wechat_credentials.json",
        description="凭据保存文件名",
    )
    auto_refresh_credentials: bool = Field(
        default=True,
        description="是否自动刷新过期凭据",
    )
    
    # 重试配置
    max_retries: int = Field(
        default=3,
        description="最大重试次数",
    )
    retry_delay: float = Field(
        default=5.0,
        description="重试延迟秒数",
    )


class ExportSettings(BaseSettings):
    """导出配置"""

    default_output_dir: str = Field(
        default="./output",
        description="默认输出目录",
    )

    # OneNote（Microsoft Graph）
    # 说明：需要先运行 `wechat-summarizer onenote-auth` 完成设备码授权。
    onenote_client_id: str = Field(
        default="", description="Azure 应用 (App registration) Client ID"
    )
    onenote_tenant: str = Field(
        default="common",
        description="Tenant（common / organizations / consumers / 或具体 tenant_id）",
    )
    onenote_notebook: str = Field(default="", description="目标笔记本名称")
    onenote_section: str = Field(default="", description="目标分区（Section）名称")

    # Notion
    notion_api_key: SecretStr = Field(default=SecretStr(""), description="Notion API密钥")
    notion_database_id: str = Field(default="", description="Notion数据库ID")

    # Obsidian
    obsidian_vault_path: str = Field(default="", description="Obsidian库路径")


class AppSettings(BaseSettings):
    """主应用配置"""

    model_config = SettingsConfigDict(
        env_prefix="WECHAT_SUMMARIZER_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # 基本设置
    debug: bool = Field(default=False, description="调试模式")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="日志级别",
    )

    # 默认摘要方法
    default_summary_method: str = Field(
        default="simple",
        description="默认摘要方法 (simple, ollama, openai, deepseek, anthropic, zhipu)",
    )

    # 子配置
    scraper: ScraperSettings = Field(default_factory=ScraperSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    deepseek: DeepSeekSettings = Field(default_factory=DeepSeekSettings)
    anthropic: AnthropicSettings = Field(default_factory=AnthropicSettings)
    zhipu: ZhipuSettings = Field(default_factory=ZhipuSettings)
    export: ExportSettings = Field(default_factory=ExportSettings)
    batch: BatchSettings = Field(default_factory=BatchSettings)


def _parse_dotenv_file(path: Path) -> dict[str, str]:
    """极简 .env 解析器（避免额外依赖 python-dotenv）。

    只支持 KEY=VALUE，忽略空行与 # 注释；支持 value 用单/双引号包裹。
    """
    if not path.exists() or not path.is_file():
        return {}

    env: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        # 如果编码异常，尝试忽略错误
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        # 支持 `export KEY=VALUE`
        if line.startswith("export "):
            line = line[len("export ") :].strip()

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        # 去掉两端引号
        if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
            value = value[1:-1]

        if key:
            env[key] = value

    return env


def _get_env_value(key: str, dotenv: dict[str, str]) -> str | None:
    """从 OS 环境变量或 .env 文件获取值（OS 优先）。"""
    return os.getenv(key) or dotenv.get(key)


@lru_cache
def get_settings() -> AppSettings:
    """获取应用配置（单例）

    - 先由 Pydantic Settings 读取 WECHAT_SUMMARIZER_* 变量（含 .env）
    - 再回填兼容旧变量（OPENAI_API_KEY / OPENAI_BASE_URL / OUTPUT_DIR 等）

    这样既保持“企业级嵌套配置”的能力，也对用户保留简单易用的 .env 写法。
    """
    settings = AppSettings()

    dotenv = _parse_dotenv_file(Path(".env"))

    # ---- OpenAI legacy ----
    if not settings.openai.api_key.get_secret_value():
        legacy_key = _get_env_value("OPENAI_API_KEY", dotenv)
        if legacy_key:
            settings.openai.api_key = SecretStr(legacy_key)

    if settings.openai.base_url is None:
        legacy_base_url = _get_env_value("OPENAI_BASE_URL", dotenv)
        if legacy_base_url:
            settings.openai.base_url = legacy_base_url

    # ---- DeepSeek legacy ----
    if not settings.deepseek.api_key.get_secret_value():
        legacy_key = _get_env_value("DEEPSEEK_API_KEY", dotenv)
        if legacy_key:
            settings.deepseek.api_key = SecretStr(legacy_key)

    # ---- Anthropic legacy (预留) ----
    if not settings.anthropic.api_key.get_secret_value():
        legacy_key = _get_env_value("ANTHROPIC_API_KEY", dotenv)
        if legacy_key:
            settings.anthropic.api_key = SecretStr(legacy_key)

    # ---- Zhipu legacy (预留) ----
    if not settings.zhipu.api_key.get_secret_value():
        legacy_key = _get_env_value("ZHIPU_API_KEY", dotenv)
        if legacy_key:
            settings.zhipu.api_key = SecretStr(legacy_key)

    # ---- Export legacy ----
    # 兼容 OUTPUT_DIR=./output 写法
    if settings.export.default_output_dir == "./output":
        legacy_out = _get_env_value("OUTPUT_DIR", dotenv)
        if legacy_out:
            settings.export.default_output_dir = legacy_out

    # Notion
    if not settings.export.notion_api_key.get_secret_value():
        legacy = _get_env_value("NOTION_API_KEY", dotenv)
        if legacy:
            settings.export.notion_api_key = SecretStr(legacy)
    if not settings.export.notion_database_id:
        legacy = _get_env_value("NOTION_DATABASE_ID", dotenv)
        if legacy:
            settings.export.notion_database_id = legacy

    # Obsidian
    if not settings.export.obsidian_vault_path:
        legacy = _get_env_value("OBSIDIAN_VAULT_PATH", dotenv)
        if legacy:
            settings.export.obsidian_vault_path = legacy

    # OneNote（Microsoft Graph）
    if not settings.export.onenote_client_id:
        legacy = _get_env_value("ONENOTE_CLIENT_ID", dotenv)
        if legacy:
            settings.export.onenote_client_id = legacy

    if settings.export.onenote_tenant == "common":
        legacy = _get_env_value("ONENOTE_TENANT", dotenv)
        if legacy:
            settings.export.onenote_tenant = legacy

    if not settings.export.onenote_notebook:
        legacy = _get_env_value("ONENOTE_NOTEBOOK", dotenv)
        if legacy:
            settings.export.onenote_notebook = legacy

    if not settings.export.onenote_section:
        legacy = _get_env_value("ONENOTE_SECTION", dotenv)
        if legacy:
            settings.export.onenote_section = legacy

    return settings


def get_config_path() -> Path:
    """获取配置文件路径"""
    return Path.home() / CONFIG_DIR_NAME / CONFIG_FILE_NAME
