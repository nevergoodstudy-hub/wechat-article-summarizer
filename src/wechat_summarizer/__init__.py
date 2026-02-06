"""微信公众号文章总结器

一个功能强大的微信公众号文章抓取、摘要和导出工具。

架构：
- 领域驱动设计 (DDD) + 六边形架构 (Hexagonal Architecture)
- 支持多种抓取策略（HTTPX快速模式、Playwright渲染模式）
- 支持多种摘要方式（本地规则、Ollama、OpenAI等）
- 支持多种导出格式（HTML、Markdown、OneNote、Notion等）

使用方式：
    # GUI模式
    python -m wechat_summarizer

    # CLI模式
    python -m wechat_summarizer cli fetch <URL>
    python -m wechat_summarizer cli batch <URL1> <URL2> ...
"""

from .shared.constants import APP_NAME, VERSION

__version__ = VERSION
__app_name__ = APP_NAME

__all__ = ["__version__", "__app_name__"]
