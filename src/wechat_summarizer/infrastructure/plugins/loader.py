"""插件加载器

通过 Python entry_points 机制发现和加载第三方插件。
支持热加载和插件生命周期管理。
"""

from __future__ import annotations

import importlib.metadata
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar

from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from ...application.ports.outbound import ExporterPort, ScraperPort, SummarizerPort


class PluginType(str, Enum):
    """插件类型"""
    
    SCRAPER = "wechat_summarizer.scrapers"
    SUMMARIZER = "wechat_summarizer.summarizers"
    EXPORTER = "wechat_summarizer.exporters"
    
    @property
    def description(self) -> str:
        """插件类型描述"""
        return {
            PluginType.SCRAPER: "抓取器插件",
            PluginType.SUMMARIZER: "摘要器插件",
            PluginType.EXPORTER: "导出器插件",
        }.get(self, "未知插件")


@dataclass
class PluginInfo:
    """插件信息"""
    
    name: str
    """插件名称（entry_point name）"""
    
    plugin_type: PluginType
    """插件类型"""
    
    entry_point: str
    """入口点完整路径（module:class）"""
    
    package: str | None = None
    """来源包名"""
    
    version: str | None = None
    """包版本"""
    
    loaded: bool = False
    """是否已加载"""
    
    instance: Any = None
    """插件实例"""
    
    error: str | None = None
    """加载错误信息"""


T = TypeVar("T")


class PluginLoader:
    """
    插件加载器
    
    通过 entry_points 发现和加载插件。支持以下功能：
    - 自动发现已安装的插件
    - 按类型过滤插件
    - 懒加载（仅在需要时实例化）
    - 错误隔离（单个插件失败不影响其他插件）
    
    示例：
        >>> loader = PluginLoader()
        >>> loader.discover()
        >>> scrapers = loader.load_all(PluginType.SCRAPER)
    """
    
    def __init__(self):
        self._discovered: dict[PluginType, list[PluginInfo]] = {
            pt: [] for pt in PluginType
        }
        self._loaded_instances: dict[str, Any] = {}
    
    def discover(self) -> dict[PluginType, list[PluginInfo]]:
        """
        发现所有已安装的插件
        
        扫描所有 entry_points 组，收集插件信息。
        
        Returns:
            按类型分组的插件信息字典
        """
        for plugin_type in PluginType:
            self._discovered[plugin_type] = self._discover_type(plugin_type)
        
        total = sum(len(v) for v in self._discovered.values())
        logger.info(f"发现 {total} 个插件")
        
        return self._discovered
    
    def _discover_type(self, plugin_type: PluginType) -> list[PluginInfo]:
        """发现指定类型的插件"""
        plugins: list[PluginInfo] = []
        
        try:
            eps = importlib.metadata.entry_points(group=plugin_type.value)
        except Exception as e:
            logger.warning(f"无法获取 {plugin_type.value} entry_points: {e}")
            return plugins
        
        for ep in eps:
            info = PluginInfo(
                name=ep.name,
                plugin_type=plugin_type,
                entry_point=f"{ep.value}",
                package=getattr(ep, "dist", None) and ep.dist.name if hasattr(ep, "dist") else None,
                version=getattr(ep, "dist", None) and ep.dist.version if hasattr(ep, "dist") else None,
            )
            plugins.append(info)
            logger.debug(f"发现插件: {info.name} ({plugin_type.description})")
        
        return plugins
    
    def get_discovered(self, plugin_type: PluginType | None = None) -> list[PluginInfo]:
        """
        获取已发现的插件信息
        
        Args:
            plugin_type: 插件类型，None 表示所有类型
        
        Returns:
            插件信息列表
        """
        if plugin_type is None:
            return [p for plugins in self._discovered.values() for p in plugins]
        return self._discovered.get(plugin_type, [])
    
    def load(self, plugin_info: PluginInfo, *args: Any, **kwargs: Any) -> Any:
        """
        加载单个插件
        
        Args:
            plugin_info: 插件信息
            *args, **kwargs: 传递给插件构造函数的参数
        
        Returns:
            插件实例
        
        Raises:
            ImportError: 模块导入失败
            TypeError: 类实例化失败
        """
        if plugin_info.loaded and plugin_info.instance is not None:
            return plugin_info.instance
        
        cache_key = f"{plugin_info.plugin_type.value}:{plugin_info.name}"
        
        if cache_key in self._loaded_instances:
            return self._loaded_instances[cache_key]
        
        try:
            # 解析 entry_point
            module_path, class_name = plugin_info.entry_point.rsplit(":", 1)
            
            # 导入模块
            module = importlib.import_module(module_path)
            
            # 获取类
            plugin_class = getattr(module, class_name)
            
            # 实例化
            instance = plugin_class(*args, **kwargs)
            
            # 更新状态
            plugin_info.loaded = True
            plugin_info.instance = instance
            self._loaded_instances[cache_key] = instance
            
            logger.info(f"加载插件成功: {plugin_info.name}")
            return instance
            
        except Exception as e:
            plugin_info.error = str(e)
            logger.error(f"加载插件失败 {plugin_info.name}: {e}")
            raise
    
    def load_all(
        self,
        plugin_type: PluginType,
        factory: Callable[[PluginInfo], tuple[tuple, dict]] | None = None,
        skip_errors: bool = True,
    ) -> list[Any]:
        """
        加载指定类型的所有插件
        
        Args:
            plugin_type: 插件类型
            factory: 参数工厂函数，接收 PluginInfo 返回 (args, kwargs)
            skip_errors: 是否跳过加载失败的插件
        
        Returns:
            成功加载的插件实例列表
        """
        instances: list[Any] = []
        
        for info in self._discovered.get(plugin_type, []):
            try:
                if factory:
                    args, kwargs = factory(info)
                else:
                    args, kwargs = (), {}
                
                instance = self.load(info, *args, **kwargs)
                instances.append(instance)
                
            except Exception as e:
                if skip_errors:
                    logger.warning(f"跳过加载失败的插件 {info.name}: {e}")
                else:
                    raise
        
        return instances
    
    def load_scrapers(
        self,
        factory: Callable[[PluginInfo], tuple[tuple, dict]] | None = None,
    ) -> list["ScraperPort"]:
        """加载所有抓取器插件"""
        return self.load_all(PluginType.SCRAPER, factory)
    
    def load_summarizers(
        self,
        factory: Callable[[PluginInfo], tuple[tuple, dict]] | None = None,
    ) -> list["SummarizerPort"]:
        """加载所有摘要器插件"""
        return self.load_all(PluginType.SUMMARIZER, factory)
    
    def load_exporters(
        self,
        factory: Callable[[PluginInfo], tuple[tuple, dict]] | None = None,
    ) -> list["ExporterPort"]:
        """加载所有导出器插件"""
        return self.load_all(PluginType.EXPORTER, factory)
    
    def unload(self, plugin_info: PluginInfo) -> None:
        """
        卸载插件
        
        清理插件实例，释放资源。
        """
        cache_key = f"{plugin_info.plugin_type.value}:{plugin_info.name}"
        
        if cache_key in self._loaded_instances:
            instance = self._loaded_instances.pop(cache_key)
            
            # 调用清理方法（如果存在）
            if hasattr(instance, "close"):
                try:
                    instance.close()
                except Exception as e:
                    logger.warning(f"插件清理失败 {plugin_info.name}: {e}")
            elif hasattr(instance, "cleanup"):
                try:
                    instance.cleanup()
                except Exception as e:
                    logger.warning(f"插件清理失败 {plugin_info.name}: {e}")
        
        plugin_info.loaded = False
        plugin_info.instance = None
        logger.debug(f"卸载插件: {plugin_info.name}")
    
    def unload_all(self) -> None:
        """卸载所有已加载的插件"""
        for plugins in self._discovered.values():
            for info in plugins:
                if info.loaded:
                    self.unload(info)
        
        self._loaded_instances.clear()
        logger.info("所有插件已卸载")
    
    def get_stats(self) -> dict[str, Any]:
        """
        获取插件统计信息
        
        Returns:
            统计信息字典
        """
        stats: dict[str, Any] = {
            "total_discovered": 0,
            "total_loaded": 0,
            "by_type": {},
        }
        
        for plugin_type, plugins in self._discovered.items():
            loaded_count = sum(1 for p in plugins if p.loaded)
            stats["by_type"][plugin_type.value] = {
                "discovered": len(plugins),
                "loaded": loaded_count,
                "plugins": [
                    {
                        "name": p.name,
                        "package": p.package,
                        "loaded": p.loaded,
                        "error": p.error,
                    }
                    for p in plugins
                ],
            }
            stats["total_discovered"] += len(plugins)
            stats["total_loaded"] += loaded_count
        
        return stats
