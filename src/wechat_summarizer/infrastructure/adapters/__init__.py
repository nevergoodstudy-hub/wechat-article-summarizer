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
    "AnthropicSummarizer",
    # Exporters
    "BaseExporter",
    # Scrapers
    "BaseScraper",
    # Summarizers
    "BaseSummarizer",
    "ClientConfig",
    "HtmlExporter",
    # HTTP Client Pool
    "HttpClientPool",
    # Storage
    "LocalJsonStorage",
    "MarkdownExporter",
    "OllamaSummarizer",
    "OpenAISummarizer",
    "SimpleSummarizer",
    "WechatHttpxScraper",
    "WechatPlaywrightScraper",
    "WordExporter",
    "ZhipuSummarizer",
    "get_async_client",
    "get_http_pool",
]
