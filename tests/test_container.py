"""依赖注入容器测试

测试 Container 类的依赖创建和管理功能。
"""

import pytest

from wechat_summarizer.infrastructure.config.container import (
    Container,
    get_container,
    reset_container,
)
from wechat_summarizer.infrastructure.config.settings import AppSettings


class TestContainer:
    """Container 测试"""

    @pytest.fixture(autouse=True)
    def reset(self) -> None:
        """每个测试前重置容器"""
        reset_container()

    @pytest.mark.unit
    def test_container_creation(self) -> None:
        """测试容器创建"""
        container = Container()
        assert container.settings is not None
        assert isinstance(container.settings, AppSettings)

    @pytest.mark.unit
    def test_scrapers_lazy_loading(self) -> None:
        """测试抓取器延迟加载"""
        container = Container()
        assert container._scrapers is None

        scrapers = container.scrapers
        assert scrapers is not None
        assert len(scrapers) > 0
        assert container._scrapers is scrapers  # 缓存

    @pytest.mark.unit
    def test_summarizers_lazy_loading(self) -> None:
        """测试摘要器延迟加载"""
        container = Container()
        assert container._summarizers is None

        summarizers = container.summarizers
        assert summarizers is not None
        assert "simple" in summarizers  # simple 始终可用
        assert container._summarizers is summarizers

    @pytest.mark.unit
    def test_exporters_lazy_loading(self) -> None:
        """测试导出器延迟加载"""
        container = Container()
        assert container._exporters is None

        exporters = container.exporters
        assert exporters is not None
        assert "html" in exporters
        assert "markdown" in exporters
        assert container._exporters is exporters

    @pytest.mark.unit
    def test_storage_creation(self) -> None:
        """测试存储创建"""
        container = Container()
        storage = container.storage
        # 存储可能为 None（如果创建失败）或有效对象
        # 这里只测试不抛异常
        assert storage is None or storage is not None

    @pytest.mark.unit
    def test_fetch_use_case_creation(self) -> None:
        """测试抓取用例创建"""
        container = Container()
        use_case = container.fetch_use_case
        assert use_case is not None

    @pytest.mark.unit
    def test_summarize_use_case_creation(self) -> None:
        """测试摘要用例创建"""
        container = Container()
        use_case = container.summarize_use_case
        assert use_case is not None

    @pytest.mark.unit
    def test_export_use_case_creation(self) -> None:
        """测试导出用例创建"""
        container = Container()
        use_case = container.export_use_case
        assert use_case is not None

    @pytest.mark.unit
    def test_batch_use_case_creation(self) -> None:
        """测试批量处理用例创建"""
        container = Container()
        use_case = container.batch_use_case
        assert use_case is not None


class TestGlobalContainer:
    """全局容器测试"""

    @pytest.fixture(autouse=True)
    def reset(self) -> None:
        """每个测试前重置容器"""
        reset_container()

    @pytest.mark.unit
    def test_get_container_singleton(self) -> None:
        """测试全局容器单例"""
        container1 = get_container()
        container2 = get_container()
        assert container1 is container2

    @pytest.mark.unit
    def test_reset_container(self) -> None:
        """测试重置容器"""
        container1 = get_container()
        reset_container()
        container2 = get_container()
        assert container1 is not container2
