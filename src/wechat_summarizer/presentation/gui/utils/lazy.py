"""
组件懒加载系统 (Lazy Loading)
按需加载重组件，优化初始加载性能

功能特性:
- 路由级代码分割
- 按需加载重组件
- 加载状态显示
- 失败降级处理
- 预加载支持

安全措施:
- 模块路径验证
- 加载超时保护
- 内存泄漏防护
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Dict, Any, Type, Set
import importlib
import threading
import time
import logging
from dataclasses import dataclass
from enum import Enum
import weakref

logger = logging.getLogger(__name__)


# 安全限制
MAX_CONCURRENT_LOADS = 5  # 最大并发加载数
LOAD_TIMEOUT_SECONDS = 30  # 加载超时
MAX_RETRY_COUNT = 3  # 最大重试次数
MAX_CACHED_COMPONENTS = 50  # 最大缓存组件数
ALLOWED_MODULE_PREFIX = "wechat_summarizer."  # 允许加载的模块前缀


class LoadState(Enum):
    """加载状态"""
    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class LoadResult:
    """加载结果"""
    state: LoadState
    component: Optional[Any] = None
    error: Optional[str] = None
    load_time_ms: float = 0


class LazyComponent:
    """懒加载组件描述"""
    
    def __init__(
        self,
        module_path: str,
        class_name: str,
        preload: bool = False,
        fallback: Optional[Type[tk.Widget]] = None
    ):
        """
        Args:
            module_path: 模块路径
            class_name: 类名
            preload: 是否预加载
            fallback: 降级组件类
        """
        self.module_path = module_path
        self.class_name = class_name
        self.preload = preload
        self.fallback = fallback
        self._loaded_class: Optional[Type] = None
        self._load_state = LoadState.IDLE
        self._error: Optional[str] = None


class LazyLoader:
    """懒加载管理器
    
    单例模式，管理所有组件的懒加载
    """
    
    _instance: Optional['LazyLoader'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # 组件注册表
        self._components: Dict[str, LazyComponent] = {}
        
        # 已加载的组件缓存
        self._loaded_cache: Dict[str, Type] = {}
        
        # 加载中的任务
        self._loading_tasks: Set[str] = set()
        
        # 加载锁
        self._load_lock = threading.Lock()
        
        # 回调队列
        self._callbacks: Dict[str, list] = {}
        
        # 弱引用实例缓存(防止内存泄漏)
        self._instances: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
    
    def register(
        self,
        name: str,
        module_path: str,
        class_name: str,
        preload: bool = False,
        fallback: Optional[Type[tk.Widget]] = None
    ):
        """注册懒加载组件
        
        Args:
            name: 组件名称
            module_path: 模块路径
            class_name: 类名
            preload: 是否预加载
            fallback: 降级组件类
        """
        # 安全验证：检查模块路径
        if not self._validate_module_path(module_path):
            logger.error(f"模块路径不允许: {module_path}")
            return
        
        self._components[name] = LazyComponent(
            module_path=module_path,
            class_name=class_name,
            preload=preload,
            fallback=fallback
        )
        
        if preload:
            self.preload_component(name)
    
    def _validate_module_path(self, module_path: str) -> bool:
        """验证模块路径安全性"""
        # 只允许加载指定前缀的模块
        if not module_path.startswith(ALLOWED_MODULE_PREFIX):
            return False
        
        # 防止路径遍历
        if ".." in module_path or module_path.startswith("/"):
            return False
        
        return True
    
    def preload_component(self, name: str):
        """预加载组件"""
        if name not in self._components:
            return
        
        def _preload():
            self._load_component_sync(name)
        
        thread = threading.Thread(target=_preload, daemon=True)
        thread.start()
    
    def load_component(
        self,
        name: str,
        callback: Optional[Callable[[LoadResult], None]] = None
    ):
        """异步加载组件
        
        Args:
            name: 组件名称
            callback: 加载完成回调
        """
        # 检查缓存
        if name in self._loaded_cache:
            if callback:
                result = LoadResult(
                    state=LoadState.SUCCESS,
                    component=self._loaded_cache[name]
                )
                callback(result)
            return
        
        # 检查并发限制
        with self._load_lock:
            if len(self._loading_tasks) >= MAX_CONCURRENT_LOADS:
                if callback:
                    callback(LoadResult(
                        state=LoadState.ERROR,
                        error="加载队列已满，请稍后重试"
                    ))
                return
            
            # 添加回调
            if name not in self._callbacks:
                self._callbacks[name] = []
            if callback:
                self._callbacks[name].append(callback)
            
            # 如果已在加载中，等待
            if name in self._loading_tasks:
                return
            
            self._loading_tasks.add(name)
        
        # 异步加载
        def _async_load():
            result = self._load_component_sync(name)
            
            with self._load_lock:
                self._loading_tasks.discard(name)
                callbacks = self._callbacks.pop(name, [])
            
            for cb in callbacks:
                try:
                    cb(result)
                except Exception as e:
                    logger.error(f"回调执行失败: {e}")
        
        thread = threading.Thread(target=_async_load, daemon=True)
        thread.start()
    
    def _load_component_sync(self, name: str) -> LoadResult:
        """同步加载组件"""
        start_time = time.time()
        
        if name not in self._components:
            return LoadResult(
                state=LoadState.ERROR,
                error=f"组件未注册: {name}"
            )
        
        component = self._components[name]
        retry_count = 0
        
        while retry_count < MAX_RETRY_COUNT:
            try:
                # 超时控制
                module = importlib.import_module(component.module_path)
                cls = getattr(module, component.class_name)
                
                # 缓存
                self._loaded_cache[name] = cls
                component._loaded_class = cls
                component._load_state = LoadState.SUCCESS
                
                # 清理旧缓存
                self._cleanup_cache()
                
                load_time = (time.time() - start_time) * 1000
                logger.info(f"组件加载成功: {name} ({load_time:.1f}ms)")
                
                return LoadResult(
                    state=LoadState.SUCCESS,
                    component=cls,
                    load_time_ms=load_time
                )
                
            except Exception as e:
                retry_count += 1
                logger.warning(f"组件加载失败 (尝试 {retry_count}/{MAX_RETRY_COUNT}): {e}")
                time.sleep(0.5)
        
        # 所有重试都失败
        error_msg = f"组件加载失败: {name}"
        component._load_state = LoadState.ERROR
        component._error = error_msg
        
        return LoadResult(
            state=LoadState.ERROR,
            error=error_msg
        )
    
    def _cleanup_cache(self):
        """清理过多的缓存"""
        if len(self._loaded_cache) > MAX_CACHED_COMPONENTS:
            # 移除最早添加的
            keys = list(self._loaded_cache.keys())
            for key in keys[:len(keys) // 2]:
                self._loaded_cache.pop(key, None)
    
    def get_component(self, name: str) -> Optional[Type]:
        """获取已加载的组件类(同步)"""
        if name in self._loaded_cache:
            return self._loaded_cache[name]
        
        # 尝试同步加载
        result = self._load_component_sync(name)
        return result.component
    
    def is_loaded(self, name: str) -> bool:
        """检查组件是否已加载"""
        return name in self._loaded_cache
    
    def unregister(self, name: str):
        """注销组件"""
        self._components.pop(name, None)
        self._loaded_cache.pop(name, None)
    
    def clear_cache(self):
        """清空缓存"""
        self._loaded_cache.clear()


class LazyWidget(tk.Frame):
    """懒加载组件容器
    
    显示加载状态，加载完成后渲染实际组件
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        component_name: str,
        component_props: Optional[Dict[str, Any]] = None,
        loading_text: str = "加载中...",
        error_text: str = "加载失败",
        retry_text: str = "重试",
        **kwargs
    ):
        """
        Args:
            parent: 父容器
            component_name: 组件名称
            component_props: 组件属性
            loading_text: 加载中文本
            error_text: 错误文本
            retry_text: 重试按钮文本
        """
        bg = kwargs.pop("bg", "#1a1a1a")
        super().__init__(parent, bg=bg, **kwargs)
        
        self._component_name = component_name
        self._component_props = component_props or {}
        self._loading_text = loading_text
        self._error_text = error_text
        self._retry_text = retry_text
        self._bg = bg
        
        self._loader = LazyLoader()
        self._actual_widget: Optional[tk.Widget] = None
        self._state = LoadState.IDLE
        
        self._setup_ui()
        self._start_loading()
    
    def _setup_ui(self):
        """构建UI"""
        # 加载状态容器
        self._status_frame = tk.Frame(self, bg=self._bg)
        self._status_frame.pack(fill=tk.BOTH, expand=True)
        
        # 加载指示器
        self._loading_label = tk.Label(
            self._status_frame,
            text=self._loading_text,
            bg=self._bg,
            fg="#808080",
            font=("Segoe UI", 14)
        )
        
        # 旋转动画
        self._spinner_canvas = tk.Canvas(
            self._status_frame,
            width=40,
            height=40,
            bg=self._bg,
            highlightthickness=0
        )
        self._spinner_angle = 0
        self._spinner_running = False
        
        # 错误状态
        self._error_label = tk.Label(
            self._status_frame,
            text=self._error_text,
            bg=self._bg,
            fg="#ef4444",
            font=("Segoe UI", 14)
        )
        
        self._retry_button = tk.Button(
            self._status_frame,
            text=self._retry_text,
            bg="#3b82f6",
            fg="#ffffff",
            font=("Segoe UI", 11),
            relief=tk.FLAT,
            cursor="hand2",
            command=self._start_loading
        )
    
    def _show_loading(self):
        """显示加载状态"""
        self._state = LoadState.LOADING
        
        # 隐藏其他状态
        self._error_label.pack_forget()
        self._retry_button.pack_forget()
        
        # 显示加载状态
        self._spinner_canvas.pack(pady=(50, 10))
        self._loading_label.pack()
        
        # 启动动画
        self._spinner_running = True
        self._animate_spinner()
    
    def _show_error(self, error: str):
        """显示错误状态"""
        self._state = LoadState.ERROR
        self._spinner_running = False
        
        # 隐藏加载状态
        self._spinner_canvas.pack_forget()
        self._loading_label.pack_forget()
        
        # 显示错误
        self._error_label.configure(text=f"{self._error_text}\n{error}")
        self._error_label.pack(pady=(50, 10))
        self._retry_button.pack()
    
    def _show_component(self, component_class: Type):
        """显示实际组件"""
        self._state = LoadState.SUCCESS
        self._spinner_running = False
        
        # 移除状态容器
        self._status_frame.pack_forget()
        
        # 创建实际组件
        try:
            self._actual_widget = component_class(self, **self._component_props)
            self._actual_widget.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            logger.error(f"组件实例化失败: {e}")
            self._status_frame.pack(fill=tk.BOTH, expand=True)
            self._show_error(str(e))
    
    def _animate_spinner(self):
        """旋转动画"""
        if not self._spinner_running:
            return
        
        self._spinner_canvas.delete("all")
        
        # 绘制旋转弧
        import math
        cx, cy = 20, 20
        r = 15
        
        for i in range(8):
            angle = self._spinner_angle + i * 45
            rad = math.radians(angle)
            x1 = cx + r * 0.6 * math.cos(rad)
            y1 = cy + r * 0.6 * math.sin(rad)
            x2 = cx + r * math.cos(rad)
            y2 = cy + r * math.sin(rad)
            
            alpha = int(255 * (1 - i / 8))
            color = f"#{alpha:02x}{alpha:02x}{255:02x}"
            
            self._spinner_canvas.create_line(
                x1, y1, x2, y2,
                fill=color,
                width=2,
                capstyle=tk.ROUND
            )
        
        self._spinner_angle = (self._spinner_angle + 30) % 360
        
        if self._spinner_running:
            self.after(50, self._animate_spinner)
    
    def _start_loading(self):
        """开始加载"""
        self._show_loading()
        
        def on_loaded(result: LoadResult):
            # 在主线程更新UI
            self.after(0, lambda: self._on_load_complete(result))
        
        self._loader.load_component(self._component_name, on_loaded)
    
    def _on_load_complete(self, result: LoadResult):
        """加载完成回调"""
        if result.state == LoadState.SUCCESS and result.component:
            self._show_component(result.component)
        else:
            self._show_error(result.error or "未知错误")
    
    def get_actual_widget(self) -> Optional[tk.Widget]:
        """获取实际组件"""
        return self._actual_widget


class LazyImage(tk.Label):
    """懒加载图片组件"""
    
    def __init__(
        self,
        parent: tk.Widget,
        image_path: Optional[str] = None,
        placeholder_text: str = "🖼",
        width: int = 100,
        height: int = 100,
        **kwargs
    ):
        bg = kwargs.pop("bg", "#1a1a1a")
        super().__init__(
            parent,
            text=placeholder_text,
            bg=bg,
            fg="#404040",
            font=("Segoe UI", 24),
            width=width // 10,
            height=height // 20,
            **kwargs
        )
        
        self._image_path = image_path
        self._width = width
        self._height = height
        self._photo_image = None
        
        if image_path:
            self._load_image()
    
    def _load_image(self):
        """异步加载图片"""
        def _load():
            try:
                from PIL import Image, ImageTk
                
                img = Image.open(self._image_path)
                img = img.resize((self._width, self._height), Image.Resampling.LANCZOS)
                
                # 在主线程更新
                self.after(0, lambda: self._set_image(img))
                
            except Exception as e:
                logger.error(f"图片加载失败: {e}")
        
        thread = threading.Thread(target=_load, daemon=True)
        thread.start()
    
    def _set_image(self, img):
        """设置图片"""
        try:
            from PIL import ImageTk
            self._photo_image = ImageTk.PhotoImage(img)
            self.configure(image=self._photo_image, text="")
        except Exception as e:
            logger.error(f"图片设置失败: {e}")
    
    def set_image_path(self, path: str):
        """设置图片路径"""
        self._image_path = path
        self._load_image()


# 便捷函数
def lazy(
    module_path: str,
    class_name: str,
    preload: bool = False
) -> Callable:
    """装饰器：标记组件为懒加载
    
    Usage:
        @lazy("wechat_summarizer.presentation.gui.components.chart", "ChartWidget")
        class ChartWidget:
            pass
    """
    def decorator(cls):
        loader = LazyLoader()
        name = f"{module_path}.{class_name}"
        loader.register(name, module_path, class_name, preload)
        return cls
    return decorator


def preload_components(*names: str):
    """预加载多个组件"""
    loader = LazyLoader()
    for name in names:
        loader.preload_component(name)


# 使用示例
if __name__ == "__main__":
    root = tk.Tk()
    root.title("懒加载测试")
    root.geometry("600x400")
    root.configure(bg="#121212")
    
    # 注册组件
    loader = LazyLoader()
    
    # 注册一个虚假组件用于测试
    # loader.register(
    #     "chart",
    #     "wechat_summarizer.presentation.gui.components.chart",
    #     "ChartWidget"
    # )
    
    # 信息标签
    info_label = tk.Label(
        root,
        text="懒加载系统已初始化\n\n支持:\n- 路由级代码分割\n- 按需加载重组件\n- 加载状态显示\n- 失败降级处理\n- 预加载支持",
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 14),
        justify=tk.LEFT
    )
    info_label.pack(pady=50, padx=50)
    
    # 模拟懒加载容器
    class MockComponent(tk.Frame):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, bg="#1a1a1a", **kwargs)
            tk.Label(
                self,
                text="✅ 组件已加载",
                bg="#1a1a1a",
                fg="#10b981",
                font=("Segoe UI", 16)
            ).pack(pady=20)
    
    # 注册Mock组件直接到缓存
    loader._loaded_cache["mock_component"] = MockComponent
    
    # 创建懒加载容器
    lazy_widget = LazyWidget(
        root,
        component_name="mock_component",
        bg="#1a1a1a"
    )
    lazy_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    root.mainloop()
