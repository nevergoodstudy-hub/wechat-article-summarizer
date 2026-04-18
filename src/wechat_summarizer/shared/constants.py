"""全局常量"""

from __future__ import annotations

import importlib.metadata as _metadata
import re
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover - Python 3.10 fallback
    tomllib = None  # type: ignore[assignment]


def _read_version_from_pyproject() -> str | None:
    """Read the local project version when running from a source checkout."""

    pyproject_path = Path(__file__).resolve().parents[3] / "pyproject.toml"
    if not pyproject_path.exists():
        return None

    try:
        pyproject_text = pyproject_path.read_text(encoding="utf-8")
    except OSError:
        return None

    if tomllib is not None:
        try:
            data = tomllib.loads(pyproject_text)
        except (TypeError, ValueError):
            data = {}
        version = data.get("project", {}).get("version")
        if isinstance(version, str) and version.strip():
            return version.strip()

    match = re.search(r'(?ms)^\[project\].*?^version\s*=\s*"([^"]+)"', pyproject_text)
    if match:
        return match.group(1).strip()

    return None


def _resolve_version() -> str:
    """Resolve the runtime version without depending on stale site-packages metadata."""

    version = _read_version_from_pyproject()
    if version:
        return version

    try:
        return _metadata.version("wechat-summarizer")
    except _metadata.PackageNotFoundError:
        return "2.4.3"


VERSION = _resolve_version()

APP_NAME = "WeChat Article Summarizer"

# 默认配置
DEFAULT_TIMEOUT = 30  # 秒
DEFAULT_MAX_RETRIES = 3
DEFAULT_CHUNK_SIZE = 4000  # Token

# User-Agent池
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# 微信相关
WECHAT_DOMAIN = "mp.weixin.qq.com"
WECHAT_CONTENT_SELECTORS = [
    "#js_content",
    ".rich_media_content",
    "#page-content",
]

# LLM默认配置
DEFAULT_OLLAMA_MODEL = "qwen2.5:7b"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"  # DeepSeek V3
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_ANTHROPIC_MODEL = "claude-3-haiku-20240307"
DEFAULT_ZHIPU_MODEL = "glm-4-flash"

# Token限制
MAX_TOKENS_OLLAMA = 8000
MAX_TOKENS_OPENAI = 128000
MAX_TOKENS_DEEPSEEK = 64000  # DeepSeek 支持 64K 上下文
MAX_TOKENS_ANTHROPIC = 100000
MAX_TOKENS_ZHIPU = 128000

# GUI相关
GUI_WINDOW_TITLE = f"微信公众号文章总结器 v{VERSION}"
GUI_WINDOW_SIZE = "1200x800"
GUI_MIN_SIZE = (800, 600)

# 主题颜色
THEME_COLORS = {
    "primary": "#07C160",  # 微信绿
    "secondary": "#576B95",  # 微信蓝
    "success": "#91d5ff",
    "warning": "#faad14",
    "error": "#ff4d4f",
    "background": "#f5f5f5",
    "text": "#333333",
}

# 文件路径
CONFIG_DIR_NAME = ".wechat_summarizer"
CONFIG_FILE_NAME = "config.yaml"
CACHE_DIR_NAME = "cache"
LOG_FILE_NAME = "app.log"
