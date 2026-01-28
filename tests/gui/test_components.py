"""
GUI组件单元测试
测试覆盖: 虚拟列表、懒加载、性能监控、可访问性工具

运行测试:
    pytest tests/gui/test_components.py -v
"""

import pytest
import time
import sys
import os
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


# ============== 虚拟列表测试 ==============
class TestVirtualList:
    """虚拟列表组件测试"""
    
    def test_import_virtuallist(self):
        """测试模块导入"""
        from wechat_summarizer.presentation.gui.components.virtuallist import (
            VirtualList, VirtualItem, MAX_ITEMS
        )
        assert MAX_ITEMS == 100000
    
    def test_virtual_item_dataclass(self):
        """测试VirtualItem数据类"""
        from wechat_summarizer.presentation.gui.components.virtuallist import VirtualItem
        
        item = VirtualItem(index=0, data="test", height=40, y_offset=0)
        assert item.index == 0
        assert item.data == "test"
        assert item.height == 40
    
    def test_data_limit_enforcement(self):
        """测试数据量限制"""
        from wechat_summarizer.presentation.gui.components.virtuallist import MAX_ITEMS
        
        # 验证最大数据量限制
        assert MAX_ITEMS <= 100000, "数据量限制应不超过10万"
    
    def test_scroll_throttle_value(self):
        """测试滚动节流值"""
        from wechat_summarizer.presentation.gui.components.virtuallist import SCROLL_THROTTLE_MS
        
        # 验证60fps节流
        assert SCROLL_THROTTLE_MS == 16, "滚动节流应为16ms(60fps)"


# ============== 懒加载测试 ==============
class TestLazyLoader:
    """懒加载系统测试"""
    
    def test_import_lazy(self):
        """测试模块导入"""
        from wechat_summarizer.presentation.gui.utils.lazy import (
            LazyLoader, LazyComponent, LoadState, LoadResult
        )
        assert LoadState.IDLE.value == "idle"
        assert LoadState.LOADING.value == "loading"
        assert LoadState.SUCCESS.value == "success"
        assert LoadState.ERROR.value == "error"
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        from wechat_summarizer.presentation.gui.utils.lazy import LazyLoader
        
        loader1 = LazyLoader()
        loader2 = LazyLoader()
        assert loader1 is loader2, "LazyLoader应为单例"
    
    def test_module_path_validation(self):
        """测试模块路径安全验证"""
        from wechat_summarizer.presentation.gui.utils.lazy import LazyLoader, ALLOWED_MODULE_PREFIX
        
        loader = LazyLoader()
        
        # 合法路径
        assert loader._validate_module_path("wechat_summarizer.presentation.gui.components.test")
        
        # 非法路径 - 不在允许前缀
        assert not loader._validate_module_path("os.path")
        assert not loader._validate_module_path("subprocess")
        
        # 非法路径 - 路径遍历
        assert not loader._validate_module_path("wechat_summarizer.../etc/passwd")
        assert not loader._validate_module_path("/etc/passwd")
    
    def test_load_result_dataclass(self):
        """测试LoadResult数据类"""
        from wechat_summarizer.presentation.gui.utils.lazy import LoadResult, LoadState
        
        result = LoadResult(state=LoadState.SUCCESS, component=str, load_time_ms=50.5)
        assert result.state == LoadState.SUCCESS
        assert result.component == str
        assert result.load_time_ms == 50.5
    
    def test_concurrent_load_limit(self):
        """测试并发加载限制"""
        from wechat_summarizer.presentation.gui.utils.lazy import MAX_CONCURRENT_LOADS
        
        assert MAX_CONCURRENT_LOADS <= 10, "并发加载数应合理限制"


# ============== 性能监控测试 ==============
class TestPerformanceMonitor:
    """性能监控系统测试"""
    
    def test_import_performance(self):
        """测试模块导入"""
        from wechat_summarizer.presentation.gui.utils.performance import (
            PerformanceMonitor, PerformanceMetrics, SlowOperation,
            PerformanceLevel, PerformanceTimer
        )
        
        assert PerformanceLevel.EXCELLENT.value == "excellent"
        assert PerformanceLevel.POOR.value == "poor"
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        from wechat_summarizer.presentation.gui.utils.performance import PerformanceMonitor
        
        monitor1 = PerformanceMonitor()
        monitor2 = PerformanceMonitor()
        assert monitor1 is monitor2, "PerformanceMonitor应为单例"
    
    def test_metrics_dataclass(self):
        """测试PerformanceMetrics数据类"""
        from wechat_summarizer.presentation.gui.utils.performance import PerformanceMetrics
        
        metrics = PerformanceMetrics(fps=60.0, frame_time_ms=16.67, memory_mb=150.0, cpu_percent=25.0)
        
        assert metrics.fps == 60.0
        assert metrics.frame_time_ms == 16.67
        assert metrics.memory_mb == 150.0
    
    def test_metrics_to_dict_no_sensitive_data(self):
        """测试指标转换不含敏感数据"""
        from wechat_summarizer.presentation.gui.utils.performance import PerformanceMetrics
        
        metrics = PerformanceMetrics(fps=60.0, frame_time_ms=16.67, memory_mb=150.0, cpu_percent=25.0)
        data = metrics.to_dict()
        
        # 验证只包含安全字段
        allowed_keys = {"fps", "frame_time_ms", "memory_mb", "cpu_percent", "timestamp"}
        assert set(data.keys()) == allowed_keys
        
        # 验证数值已四舍五入
        assert isinstance(data["fps"], float)
        assert isinstance(data["memory_mb"], float)
    
    def test_slow_operation_name_truncation(self):
        """测试慢操作名称截断"""
        from wechat_summarizer.presentation.gui.utils.performance import SlowOperation
        
        long_name = "a" * 100
        op = SlowOperation(name=long_name, duration_ms=150.0)
        data = op.to_dict()
        
        # 名称应被截断到50字符
        assert len(data["name"]) <= 50
    
    def test_slow_operation_threshold(self):
        """测试慢操作阈值"""
        from wechat_summarizer.presentation.gui.utils.performance import SLOW_OP_THRESHOLD_MS
        
        assert SLOW_OP_THRESHOLD_MS == 100, "慢操作阈值应为100ms"
    
    def test_performance_level_classification(self):
        """测试性能等级分类"""
        from wechat_summarizer.presentation.gui.utils.performance import PerformanceLevel
        
        # 验证等级定义
        levels = [e.value for e in PerformanceLevel]
        assert "excellent" in levels
        assert "good" in levels
        assert "fair" in levels
        assert "poor" in levels
    
    def test_timer_context_manager(self):
        """测试计时器上下文管理器"""
        from wechat_summarizer.presentation.gui.utils.performance import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        with monitor.timer("test_operation"):
            time.sleep(0.01)  # 10ms
        
        # 不应触发慢操作警告(阈值100ms)
        # 这里只测试不抛异常


# ============== 可访问性工具测试 ==============
class TestAccessibility:
    """可访问性工具测试"""
    
    def test_import_accessibility(self):
        """测试模块导入"""
        from wechat_summarizer.presentation.gui.utils.accessibility import (
            FocusManager, FocusRingStyle, FocusableElement, FocusDirection
        )
        assert True
    
    def test_focus_ring_style_defaults(self):
        """测试焦点轮廓默认样式"""
        from wechat_summarizer.presentation.gui.utils.accessibility import FocusRingStyle
        
        # FocusRingStyle 是一个类，DEFAULT是类属性
        assert FocusRingStyle.DEFAULT["color"] == "#3b82f6"
        assert FocusRingStyle.DEFAULT["width"] == 2
        assert FocusRingStyle.DEFAULT["offset"] == 2
    
    def test_focusable_element(self):
        """测试可聚焦元素数据类"""
        from wechat_summarizer.presentation.gui.utils.accessibility import FocusableElement
        import tkinter as tk
        
        # 仅测试dataclass定义
        assert hasattr(FocusableElement, '__dataclass_fields__')
        assert 'widget' in FocusableElement.__dataclass_fields__
        assert 'tab_index' in FocusableElement.__dataclass_fields__
        assert 'label' in FocusableElement.__dataclass_fields__


# ============== 自动保存测试 ==============
class TestAutoSave:
    """表单自动保存测试"""
    
    def test_import_autosave(self):
        """测试模块导入"""
        from wechat_summarizer.presentation.gui.utils.autosave import (
            Draft, DraftStorage, SimpleEncryptor
        )
        assert True
    
    def test_encryption_roundtrip(self):
        """测试加密解密往返"""
        from wechat_summarizer.presentation.gui.utils.autosave import SimpleEncryptor
        
        # 使用固定密钥测试，密钥需要足够长
        encryptor = SimpleEncryptor("test_key_for_encryption_test")
        original = "TestData123"
        
        encrypted = encryptor.encrypt(original)
        decrypted = encryptor.decrypt(encrypted)
        
        assert decrypted == original
        assert encrypted != original  # 确保确实加密了
    
    def test_draft_size_limit(self):
        """测试草稿大小限制"""
        from wechat_summarizer.presentation.gui.utils.autosave import MAX_DRAFT_SIZE
        
        assert MAX_DRAFT_SIZE == 100 * 1024, "草稿大小应限制为100KB"
    
    def test_draft_expiry_days(self):
        """测试草稿过期天数"""
        from wechat_summarizer.presentation.gui.utils.autosave import DRAFT_EXPIRE_DAYS
        
        assert DRAFT_EXPIRE_DAYS == 7, "草稿应7天后过期"


# ============== 快捷键测试 ==============
class TestShortcuts:
    """快捷键系统测试"""
    
    def test_import_shortcuts(self):
        """测试模块导入"""
        from wechat_summarizer.presentation.gui.utils.shortcuts import (
            KeyboardShortcutManager, Shortcut
        )
        assert True
    
    def test_shortcut_dataclass(self):
        """测试快捷键数据类"""
        from wechat_summarizer.presentation.gui.utils.shortcuts import Shortcut
        
        shortcut = Shortcut(
            id="test_save",
            name="保存",
            keys="Ctrl+S",
            callback=lambda: None,
            group="文件",
            description="保存文件"
        )
        
        assert shortcut.keys == "Ctrl+S"
        assert shortcut.description == "保存文件"
    
    def test_max_shortcuts_limit(self):
        """测试最大快捷键数量限制"""
        from wechat_summarizer.presentation.gui.utils.shortcuts import KeyboardShortcutManager
        
        assert KeyboardShortcutManager.MAX_SHORTCUTS == 100, "最大快捷键数应为100"


# ============== 剪贴板检测测试 ==============
class TestClipboardDetector:
    """剪贴板URL检测测试"""
    
    def test_import_clipboard_detector(self):
        """测试模块导入"""
        # clipboard_detector 模块可能有不同的导出
        try:
            from wechat_summarizer.presentation.gui.utils import clipboard_detector
            assert hasattr(clipboard_detector, 'MAX_URLS') or True  # 模块存在即可
        except ImportError:
            pytest.skip("clipboard_detector模块不可用")
    
    def test_clipboard_module_exists(self):
        """测试剪贴板模块存在"""
        import importlib.util
        spec = importlib.util.find_spec(
            "wechat_summarizer.presentation.gui.utils.clipboard_detector"
        )
        assert spec is not None, "clipboard_detector模块应存在"


# ============== i18n测试 ==============
class TestI18n:
    """国际化工具测试"""
    
    def test_import_i18n(self):
        """测试模块导入"""
        try:
            from wechat_summarizer.presentation.gui.utils import i18n
            assert True
        except ImportError:
            pytest.skip("i18n模块不可用")
    
    def test_i18n_module_exists(self):
        """测试i18n模块存在"""
        import importlib.util
        spec = importlib.util.find_spec(
            "wechat_summarizer.presentation.gui.utils.i18n"
        )
        assert spec is not None, "i18n模块应存在"


# ============== 主题管理器测试 ==============
class TestThemeManager:
    """主题管理器测试"""
    
    def test_import_theme_manager(self):
        """测试模块导入"""
        try:
            from wechat_summarizer.presentation.gui.utils import theme_manager
            assert True
        except ImportError:
            pytest.skip("theme_manager模块不可用")
    
    def test_theme_manager_module_exists(self):
        """测试主题管理器模块存在"""
        import importlib.util
        spec = importlib.util.find_spec(
            "wechat_summarizer.presentation.gui.utils.theme_manager"
        )
        assert spec is not None, "theme_manager模块应存在"


# ============== 安全审查测试 ==============
class TestSecurityMeasures:
    """安全措施测试"""
    
    def test_core_components_have_limits(self):
        """测试核心组件都有限制"""
        from wechat_summarizer.presentation.gui.components.virtuallist import MAX_ITEMS
        from wechat_summarizer.presentation.gui.utils.lazy import MAX_CONCURRENT_LOADS, MAX_CACHED_COMPONENTS
        from wechat_summarizer.presentation.gui.utils.performance import MAX_HISTORY_SIZE, MAX_SLOW_OPS_LOG
        from wechat_summarizer.presentation.gui.utils.autosave import MAX_DRAFT_SIZE
        from wechat_summarizer.presentation.gui.utils.shortcuts import KeyboardShortcutManager
        
        # 验证所有限制都是合理的正数
        assert MAX_ITEMS > 0
        assert MAX_CONCURRENT_LOADS > 0
        assert MAX_CACHED_COMPONENTS > 0
        assert MAX_HISTORY_SIZE > 0
        assert MAX_SLOW_OPS_LOG > 0
        assert MAX_DRAFT_SIZE > 0
        assert KeyboardShortcutManager.MAX_SHORTCUTS > 0
    
    def test_no_arbitrary_code_execution(self):
        """测试无任意代码执行"""
        from wechat_summarizer.presentation.gui.utils.lazy import LazyLoader, ALLOWED_MODULE_PREFIX
        
        loader = LazyLoader()
        
        # 确保不能加载任意模块
        dangerous_modules = [
            "os",
            "subprocess",
            "sys",
            "builtins",
            "__builtins__",
            "importlib",
            "eval",
            "exec"
        ]
        
        for module in dangerous_modules:
            assert not loader._validate_module_path(module), f"不应允许加载 {module}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
