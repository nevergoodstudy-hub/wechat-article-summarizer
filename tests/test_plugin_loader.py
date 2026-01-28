"""插件加载器测试

测试 PluginLoader 的发现和加载功能。
"""

import pytest

from wechat_summarizer.infrastructure.plugins import (
    PluginInfo,
    PluginLoader,
    PluginType,
)


class TestPluginType:
    """PluginType 枚举测试"""

    @pytest.mark.unit
    def test_plugin_type_values(self) -> None:
        """测试插件类型值"""
        assert PluginType.SCRAPER.value == "wechat_summarizer.scrapers"
        assert PluginType.SUMMARIZER.value == "wechat_summarizer.summarizers"
        assert PluginType.EXPORTER.value == "wechat_summarizer.exporters"

    @pytest.mark.unit
    def test_plugin_type_descriptions(self) -> None:
        """测试插件类型描述"""
        assert PluginType.SCRAPER.description == "抓取器插件"
        assert PluginType.SUMMARIZER.description == "摘要器插件"
        assert PluginType.EXPORTER.description == "导出器插件"


class TestPluginInfo:
    """PluginInfo 数据类测试"""

    @pytest.mark.unit
    def test_plugin_info_creation(self) -> None:
        """测试插件信息创建"""
        info = PluginInfo(
            name="test_plugin",
            plugin_type=PluginType.SCRAPER,
            entry_point="my_package.scrapers:MyScraper",
            package="my-package",
            version="1.0.0",
        )

        assert info.name == "test_plugin"
        assert info.plugin_type == PluginType.SCRAPER
        assert info.entry_point == "my_package.scrapers:MyScraper"
        assert info.package == "my-package"
        assert info.version == "1.0.0"
        assert info.loaded is False
        assert info.instance is None
        assert info.error is None


class TestPluginLoader:
    """PluginLoader 测试"""

    @pytest.fixture
    def loader(self) -> PluginLoader:
        """创建插件加载器"""
        return PluginLoader()

    @pytest.mark.unit
    def test_loader_creation(self, loader: PluginLoader) -> None:
        """测试加载器创建"""
        assert loader._discovered is not None
        assert len(loader._discovered) == len(PluginType)
        assert loader._loaded_instances == {}

    @pytest.mark.unit
    def test_discover_returns_dict(self, loader: PluginLoader) -> None:
        """测试 discover 返回字典"""
        result = loader.discover()

        assert isinstance(result, dict)
        assert PluginType.SCRAPER in result
        assert PluginType.SUMMARIZER in result
        assert PluginType.EXPORTER in result

    @pytest.mark.unit
    def test_get_discovered_all(self, loader: PluginLoader) -> None:
        """测试获取所有已发现的插件"""
        loader.discover()
        plugins = loader.get_discovered()

        assert isinstance(plugins, list)
        # 所有插件都应该是 PluginInfo 实例
        for p in plugins:
            assert isinstance(p, PluginInfo)

    @pytest.mark.unit
    def test_get_discovered_by_type(self, loader: PluginLoader) -> None:
        """测试按类型获取已发现的插件"""
        loader.discover()

        scrapers = loader.get_discovered(PluginType.SCRAPER)
        summarizers = loader.get_discovered(PluginType.SUMMARIZER)
        exporters = loader.get_discovered(PluginType.EXPORTER)

        assert isinstance(scrapers, list)
        assert isinstance(summarizers, list)
        assert isinstance(exporters, list)

    @pytest.mark.unit
    def test_get_stats(self, loader: PluginLoader) -> None:
        """测试获取统计信息"""
        loader.discover()
        stats = loader.get_stats()

        assert "total_discovered" in stats
        assert "total_loaded" in stats
        assert "by_type" in stats
        assert isinstance(stats["total_discovered"], int)
        assert isinstance(stats["total_loaded"], int)

    @pytest.mark.unit
    def test_unload_all(self, loader: PluginLoader) -> None:
        """测试卸载所有插件"""
        loader.discover()
        loader.unload_all()

        assert loader._loaded_instances == {}


class TestPluginLoaderIntegration:
    """PluginLoader 集成测试"""

    @pytest.mark.integration
    def test_container_has_plugin_loader(self) -> None:
        """测试容器中包含插件加载器"""
        from wechat_summarizer.infrastructure.config import get_container, reset_container

        reset_container()
        container = get_container()

        assert container.plugin_loader is not None
        assert isinstance(container.plugin_loader, PluginLoader)

    @pytest.mark.integration
    def test_plugin_loader_discovers_on_access(self) -> None:
        """测试访问时自动发现插件"""
        from wechat_summarizer.infrastructure.config import get_container, reset_container

        reset_container()
        container = get_container()
        loader = container.plugin_loader

        # 应该已经调用了 discover
        stats = loader.get_stats()
        assert stats is not None
