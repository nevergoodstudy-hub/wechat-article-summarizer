"""Static data for the GUI home dashboard."""

from __future__ import annotations

from dataclasses import dataclass

from ..styles.colors import ModernColors


@dataclass(frozen=True)
class DashboardTip:
    """A compact tip shown in the home-page tip bar."""

    icon: str
    title: str
    content: str


@dataclass(frozen=True)
class ActionCardSpec:
    """Configuration for a home-page action card."""

    icon: str
    title: str
    description: str
    page: str
    color: str


DASHBOARD_TIPS: tuple[DashboardTip, ...] = (
    DashboardTip("📋", "粘贴即用", "复制微信文章链接，直接粘贴到下方输入框即可开始处理"),
    DashboardTip("⌨️", "快捷键", "Ctrl+1~4 切换页面，Ctrl+D 切换主题，Ctrl+E 导出"),
    DashboardTip("🤖", "AI 摘要", "在设置中配置 API 密钥，即可使用 DeepSeek/OpenAI 智能摘要"),
    DashboardTip("📦", "批量打包", "批量处理后可一键导出为 ZIP 压缩包"),
    DashboardTip("🗃️", "智能缓存", "已处理文章自动缓存，重复链接秒速加载"),
    DashboardTip("📂", "文件导入", "在批量页面点击「从文件导入」支持 .txt 批量导入链接"),
)


def get_action_cards(
    *,
    single_page: str,
    batch_page: str,
    history_page: str,
) -> tuple[ActionCardSpec, ...]:
    """Return the default Bento action-card configuration."""
    return (
        ActionCardSpec("📄", "单篇处理", "抓取并生成摘要", single_page, ModernColors.INFO),
        ActionCardSpec("📚", "批量处理", "多篇文章批量处理", batch_page, ModernColors.SUCCESS),
        ActionCardSpec("📜", "历史记录", "查看已处理文章", history_page, ModernColors.WARNING),
    )
