"""
基础设施层

包含所有外部服务的具体实现（适配器）：
- adapters/scrapers: 抓取器实现
- adapters/summarizers: 摘要器实现
- adapters/exporters: 导出器实现
- config: 配置管理和依赖注入
"""

from .config import AppSettings, Container, get_container, get_settings

__all__ = [
    "AppSettings",
    "get_settings",
    "Container",
    "get_container",
]
