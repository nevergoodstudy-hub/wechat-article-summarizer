"""全局常量"""

import importlib.metadata as _metadata

# 版本信息 — 从 pyproject.toml 动态读取，保证唯一来源
try:
    VERSION = _metadata.version("wechat-summarizer")
except _metadata.PackageNotFoundError:
    VERSION = "2.4.0"  # fallback（开发模式未 pip install -e . 时）

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
