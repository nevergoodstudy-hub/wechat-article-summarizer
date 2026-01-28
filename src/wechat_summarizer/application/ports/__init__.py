"""
应用层端口

Hexagonal Architecture中的端口定义：
- inbound: 入站端口，定义应用层对外提供的服务接口
- outbound: 出站端口，定义应用层依赖的外部服务接口
"""

from .inbound import ArticleServicePort, BatchProgress, BatchServicePort, ProgressCallback
from .outbound import (
    AsyncExporterPort,
    AsyncScraperPort,
    AsyncSummarizerPort,
    ExporterPort,
    ScraperPort,
    StoragePort,
    SummarizerPort,
)

__all__ = [
    # Inbound
    "ArticleServicePort",
    "BatchServicePort",
    "BatchProgress",
    "ProgressCallback",
    # Outbound
    "ScraperPort",
    "AsyncScraperPort",
    "SummarizerPort",
    "AsyncSummarizerPort",
    "ExporterPort",
    "AsyncExporterPort",
    "StoragePort",
]
