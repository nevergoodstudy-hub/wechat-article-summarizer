"""基础设施适配器"""

from .exporters import (
    BaseExporter,
    HtmlExporter,
    MarkdownExporter,
    WordExporter,
)
from .http_client_pool import ClientConfig, HttpClientPool, get_async_client, get_http_pool
from .scrapers import BaseScraper, WechatHttpxScraper, WechatPlaywrightScraper
from .storage import LocalJsonStorage
from .summarizers import (
    AnthropicSummarizer,
    BaseSummarizer,
    OllamaSummarizer,
    OpenAISummarizer,
    SimpleSummarizer,
    ZhipuSummarizer,
)

__all__ = [
    # Scrapers
    "BaseScraper",
    "WechatHttpxScraper",
    "WechatPlaywrightScraper",
    # Summarizers
    "BaseSummarizer",
    "SimpleSummarizer",
    "OllamaSummarizer",
    "OpenAISummarizer",
    "AnthropicSummarizer",
    "ZhipuSummarizer",
    # Exporters
    "BaseExporter",
    "HtmlExporter",
    "MarkdownExporter",
    "WordExporter",
    # Storage
    "LocalJsonStorage",
    # HTTP Client Pool
    "HttpClientPool",
    "ClientConfig",
    "get_http_pool",
    "get_async_client",
]
