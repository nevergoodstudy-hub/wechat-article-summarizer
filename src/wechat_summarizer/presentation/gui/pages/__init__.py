"""GUI页面模块

从 app.py 提取的页面组件 (Phase 2-3)：
- HomePage: 首页（欢迎区 + 导航卡片 + 版权信息 + tips轮播）
- SinglePage: 单篇文章处理页面
- BatchPage: 批量文章处理页面
- HistoryPage: 历史记录页面
- SettingsPage: 设置页面
"""

from .batch_page import BatchPage
from .history_page import HistoryPage
from .home_page import HomePage
from .settings_page import SettingsPage
from .single_page import SinglePage

__all__ = [
    "BatchPage",
    "HistoryPage",
    "HomePage",
    "SettingsPage",
    "SinglePage",
]
