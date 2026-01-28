"""插件系统

支持通过 Python entry_points 机制加载第三方插件。

插件类型：
- wechat_summarizer.scrapers: 抓取器插件
- wechat_summarizer.summarizers: 摘要器插件
- wechat_summarizer.exporters: 导出器插件

开发插件示例 (pyproject.toml):
    [project.entry-points."wechat_summarizer.scrapers"]
    my_scraper = "my_package.scrapers:MyScraper"
"""

from .loader import PluginLoader, PluginInfo, PluginType

__all__ = ["PluginLoader", "PluginInfo", "PluginType"]
