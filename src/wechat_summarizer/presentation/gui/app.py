"""GUI主应用 - 现代化界面设计

采用CustomTkinter的现代sidebar导航布局：
- 左侧固定sidebar导航栏
- 深色/浅色主题支持
- 页面切换动画
- 日志面板
- Word导出预览
"""
from __future__ import annotations
import json
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, List, Optional
from loguru import logger
from ...infrastructure.config import get_container, get_settings
from ...infrastructure.async_executor import GUIAsyncHelper, get_async_executor
from ...shared.constants import GUI_MIN_SIZE, GUI_WINDOW_TITLE, CONFIG_DIR_NAME, VERSION, APP_NAME
from ...shared.progress import BatchProgressTracker, ProgressInfo
from .utils.clipboard_detector import AutoLinkDetector, DetectionResult
from .utils.i18n import get_i18n, set_language, tr

# 2026现代化色彩系统
from .styles.colors import (
    ModernColors,
    THEME_DARK,
    THEME_LIGHT,
    get_theme,
    to_tkinter_color
)
from .styles.spacing import Spacing
from .styles.typography import ChineseFonts

# 2026现代化GUI组件
from .components.button import ModernButton, ButtonVariant, ButtonSize
from .components.input import ModernInput, ValidationState
from .components.card import ModernCard, CardStyle, ShadowDepth
from .components.progress import LinearProgress
from .components.toast import ToastManager, ToastType, init_toast_manager

# 性能监控与快捷键系统 (2026 UI)
from .utils.performance import PerformanceMonitor, PerformanceMetrics, PerformanceTimer
from .utils.shortcuts import KeyboardShortcutManager, Shortcut
from .utils.display import DisplayHelper
from .utils.windows_integration import Windows11StyleHelper

# 响应式布局系统 (2026 UI)
from .utils.responsive import BreakpointManager, Breakpoint, ResponsiveLayout

# 虚拟列表组件 (2026 UI) - 预留导入，大数据量时启用
# from .components.virtuallist import VirtualList

if TYPE_CHECKING:
    from ...domain.entities import Article
_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False

class AnimationHelper:
    """平滑动画工具类 - 高刷新率优化版
    
    性能优化：
    - 自动检测屏幕刷新率，支持 60Hz/120Hz/144Hz/165Hz/240Hz
    - 动态调整帧率以匹配屏幕
    - 精确帧时间控制（浮点数）
    - 优化的缓动函数
    - 减少不必要的重绘
    """
    # 动态 FPS：根据屏幕刷新率自动调整
    _fps: int = None
    _frame_duration: float = None
    _initialized: bool = False
    
    # 最佳动画时长（基于 UX 研究：200-300ms）
    DURATION_FAST = 150      # 快速反馈：微交互
    DURATION_NORMAL = 200    # 标准动画：按钮、卡片
    DURATION_SMOOTH = 250    # 平滑过渡：页面切换
    DURATION_SLOW = 300      # 慢速：强调效果
    
    @classmethod
    def _ensure_initialized(cls):
        """确保动画参数已初始化"""
        if not cls._initialized:
            cls._fps = DisplayHelper.get_optimal_fps()
            cls._frame_duration = 1000.0 / cls._fps
            cls._initialized = True
            
            refresh_rate = DisplayHelper.get_refresh_rate()
            if refresh_rate > 60:
                logger.info(f'🎮 动画系统已优化: 屏幕 {refresh_rate}Hz, 动画 {cls._fps}fps')
    
    @classmethod
    @property
    def FPS(cls) -> int:
        """获取当前 FPS"""
        cls._ensure_initialized()
        return cls._fps
    
    @classmethod
    @property
    def FRAME_DURATION(cls) -> float:
        """获取当前帧时长 (ms)"""
        cls._ensure_initialized()
        return cls._frame_duration
    
    @classmethod
    def get_fps(cls) -> int:
        """获取当前 FPS (兼容方法)"""
        cls._ensure_initialized()
        return cls._fps
    
    @classmethod
    def get_frame_duration(cls) -> float:
        """获取当前帧时长 (兼容方法)"""
        cls._ensure_initialized()
        return cls._frame_duration
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """缓出三次方 - 用于平滑的结束效果
        
        推荐用途：退出动画、淡出效果
        """
        return 1 - pow(1 - t, 3)
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """缓进缓出三次方 - 用于平滑过渡
        
        推荐用途：页面切换、位置移动
        注意：已优化性能，减少分支预测失败
        """
        t *= 2
        if t < 1:
            return 0.5 * t * t * t
        t -= 2
        return 0.5 * (t * t * t + 2)
    
    @staticmethod
    def ease_out_expo(t: float) -> float:
        """缓出指数 - 最平滑的减速效果
        
        推荐用途：所有动画的默认缓动函数
        Material Design 推荐使用
        """
        return 1 if t == 1 else 1 - pow(2, -10 * t)
    
    @staticmethod
    def ease_out_quart(t: float) -> float:
        """缓出四次方 - 比三次方更平滑
        
        推荐用途：大型元素移动、页面过渡
        """
        return 1 - pow(1 - t, 4)
    
    @staticmethod
    def ease_out_back(t: float) -> float:
        """缓出回弹 - 用于弹性效果
        
        推荐用途：强调性动画（但不要过度使用）
        """
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)
    @staticmethod
    def lerp(start: float, end: float, t: float) -> float:
        """线性插值"""
        return start + (end - start) * t
    @classmethod
    def animate_value(cls, root, start_val: float, end_val: float, duration_ms: int, callback, easing=None, on_complete=None):
        """动画数值变化 - 性能优化版
        
        优化点：
        - 使用浮点数帧时间，精度更高
        - 减少不必要的计算
        - 预先计算总帧数
        - 缓动函数默认使用最平滑的 ease_out_expo
        
        Args:
            root: Tkinter root窗口
            start_val: 起始值
            end_val: 结束值
            duration_ms: 动画时长(毫秒)，建议 150-300ms
            callback: 每帧回调函数(current_value)
            easing: 缓动函数，默认 ease_out_expo（最平滑）
            on_complete: 动画完成回调
        """
        if easing is None:
            easing = cls.ease_out_expo  # 使用更平滑的默认缓动
        
        # 使用浮点数计算总帧数，提高精度
        frame_duration = cls.get_frame_duration()
        total_frames = max(1, int(duration_ms / frame_duration))
        frame_duration_int = int(frame_duration)  # 转为整数用于 after()
        
        current_frame = [0]
        
        def update():
            if current_frame[0] >= total_frames:
                # 确保最终值精确
                callback(end_val)
                if on_complete:
                    on_complete()
                return
            
            # 计算进度（0.0 - 1.0）
            progress = current_frame[0] / total_frames
            eased_progress = easing(progress)
            current_val = cls.lerp(start_val, end_val, eased_progress)
            callback(current_val)
            
            current_frame[0] += 1
            root.after(frame_duration_int, update)
        
        update()
class TransitionManager:
    """页面过渡动画管理器 - 性能优化版
    
    使用 place() 几何管理器实现页面滑入滑出动画
    
    优化点：
    - 缩短动画时长至 200ms（UX 研究推荐范围）
    - 减少不必要的 update_idletasks() 调用
    - 优化位置计算，减少重绘
    """
    
    # 动画配置 - 基于 Material Design 和 Apple HIG
    DURATION_MS = 200  # 页面切换推荐 200-250ms
    DIRECTION_LEFT = 'left'
    DIRECTION_RIGHT = 'right'
    DIRECTION_UP = 'up'
    DIRECTION_DOWN = 'down'
    
    @classmethod
    def slide_transition(
        cls,
        root,
        container,
        old_frame,
        new_frame,
        direction: str = 'left',
        duration_ms: int = None,
        on_complete = None
    ):
        """执行页面滑动过渡动画
        
        Args:
            root: Tkinter root 窗口
            container: 页面容器 Frame
            old_frame: 旧页面 Frame (可为 None)
            new_frame: 新页面 Frame
            direction: 滑动方向 ('left', 'right', 'up', 'down')
            duration_ms: 动画时长 (毫秒)
            on_complete: 动画完成回调
        """
        if duration_ms is None:
            duration_ms = cls.DURATION_MS
        
        # 获取容器尺寸
        container.update_idletasks()
        width = container.winfo_width()
        height = container.winfo_height()
        
        if width <= 1 or height <= 1:
            # 容器尚未布局，直接显示新页面
            if old_frame:
                old_frame.grid_forget()
            new_frame.grid(row=0, column=0, sticky='nsew')
            if on_complete:
                on_complete()
            return
        
        # 计算起始和结束位置
        if direction == cls.DIRECTION_LEFT:
            # 新页面从右向左滑入
            new_start_x = width
            new_end_x = 0
            old_end_x = -width
            start_y = end_y = 0
            is_horizontal = True
        elif direction == cls.DIRECTION_RIGHT:
            # 新页面从左向右滑入
            new_start_x = -width
            new_end_x = 0
            old_end_x = width
            start_y = end_y = 0
            is_horizontal = True
        elif direction == cls.DIRECTION_UP:
            # 新页面从下向上滑入
            new_start_y = height
            new_end_y = 0
            old_end_y = -height
            start_x = end_x = 0
            is_horizontal = False
        else:  # direction == cls.DIRECTION_DOWN
            # 新页面从上向下滑入
            new_start_y = -height
            new_end_y = 0
            old_end_y = height
            start_x = end_x = 0
            is_horizontal = False
        
        # 准备动画：使用 place 定位
        if old_frame and old_frame.winfo_ismapped():
            old_frame.grid_forget()
            old_frame.place(x=0, y=0, relwidth=1, relheight=1)
        
        if is_horizontal:
            new_frame.place(x=new_start_x, y=0, relwidth=1, relheight=1)
        else:
            new_frame.place(x=0, y=new_start_y, relwidth=1, relheight=1)
        
        # 执行动画
        def update_position(progress):
            t = AnimationHelper.ease_in_out_cubic(progress)
            
            if is_horizontal:
                new_x = AnimationHelper.lerp(new_start_x, new_end_x, t)
                new_frame.place(x=int(new_x), y=0, relwidth=1, relheight=1)
                
                if old_frame and old_frame.winfo_exists():
                    old_x = AnimationHelper.lerp(0, old_end_x, t)
                    old_frame.place(x=int(old_x), y=0, relwidth=1, relheight=1)
            else:
                new_y = AnimationHelper.lerp(new_start_y, new_end_y, t)
                new_frame.place(x=0, y=int(new_y), relwidth=1, relheight=1)
                
                if old_frame and old_frame.winfo_exists():
                    old_y = AnimationHelper.lerp(0, old_end_y, t)
                    old_frame.place(x=0, y=int(old_y), relwidth=1, relheight=1)
        
        def on_animation_complete():
            # 清理：切换回 grid 布局
            if old_frame and old_frame.winfo_exists():
                old_frame.place_forget()
            
            new_frame.place_forget()
            new_frame.grid(row=0, column=0, sticky='nsew')
            
            if on_complete:
                on_complete()
        
        # 使用 AnimationHelper 执行动画
        AnimationHelper.animate_value(
            root,
            0.0, 1.0,
            duration_ms,
            update_position,
            easing=lambda x: x,  # 使用线性，在 update_position 中应用缓动
            on_complete=on_animation_complete
        )


class ExitConfirmDialog:
    """退出确认对话框 - 现代化 CustomTkinter 风格
    
    参考 CTkMessagebox 开源项目的设计规范：
    - 支持暗色/亮色主题
    - 带图标和自定义按钮
    - 模态对话框，防止用户误操作
    - 显示当前运行任务的详细信息
    """
    
    def __init__(self, parent, title: str, message: str, 
                 task_info: str = None, icon: str = 'warning'):
        """创建退出确认对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            message: 主要提示信息
            task_info: 当前运行任务的详细信息
            icon: 图标类型 ('warning', 'question', 'info')
        """
        self.result = None
        
        # 创建对话框窗口
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry('450x280')
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()  # 模态
        
        # 居中显示
        self.dialog.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 280) // 2
        self.dialog.geometry(f'+{x}+{y}')
        
        # 主容器
        container = ctk.CTkFrame(self.dialog, fg_color='transparent')
        container.pack(fill='both', expand=True, padx=25, pady=20)
        
        # 图标和标题区域
        header_frame = ctk.CTkFrame(container, fg_color='transparent')
        header_frame.pack(fill='x', pady=(0, 15))
        
        # 图标
        icon_text = {'warning': '⚠️', 'question': '❓', 'info': 'ℹ️'}.get(icon, '⚠️')
        icon_label = ctk.CTkLabel(
            header_frame,
            text=icon_text,
            font=ctk.CTkFont(size=36)
        )
        icon_label.pack(side='left', padx=(10, 15))
        
        # 标题和消息
        text_frame = ctk.CTkFrame(header_frame, fg_color='transparent')
        text_frame.pack(side='left', fill='both', expand=True)
        
        title_label = ctk.CTkLabel(
            text_frame,
            text=title,
            font=ctk.CTkFont(size=18, weight='bold'),
            anchor='w'
        )
        title_label.pack(fill='x')
        
        msg_label = ctk.CTkLabel(
            text_frame,
            text=message,
            font=ctk.CTkFont(size=13),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
            anchor='w',
            wraplength=320,
            justify='left'
        )
        msg_label.pack(fill='x', pady=(5, 0))
        
        # 任务信息区域（如果有）
        if task_info:
            task_frame = ctk.CTkFrame(
                container,
                corner_radius=Spacing.RADIUS_MD,
                fg_color=(ModernColors.WARNING_LIGHT, '#3d2e00'),
                border_width=1,
                border_color=(ModernColors.WARNING, '#5a4500')
            )
            task_frame.pack(fill='x', pady=(0, 15))
            
            task_label = ctk.CTkLabel(
                task_frame,
                text=f'📝 当前任务: {task_info}',
                font=ctk.CTkFont(size=12),
                text_color=(ModernColors.WARNING, '#ffc107'),
                anchor='w',
                wraplength=380
            )
            task_label.pack(fill='x', padx=15, pady=10)
        
        # 警告提示
        warning_label = ctk.CTkLabel(
            container,
            text='强制退出可能导致数据丢失或文件损坏',
            font=ctk.CTkFont(size=11),
            text_color=ModernColors.ERROR
        )
        warning_label.pack(pady=(0, 15))
        
        # 按钮区域
        btn_frame = ctk.CTkFrame(container, fg_color='transparent')
        btn_frame.pack(fill='x', pady=(10, 0))
        
        # 取消按钮（继续任务）
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text='继续任务',
            width=120,
            height=40,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=ModernColors.INFO,
            hover_color='#2563eb',
            font=ctk.CTkFont(size=14, weight='bold'),
            command=self._on_cancel
        )
        cancel_btn.pack(side='left', padx=(0, 10))
        
        # 强制退出按钮
        exit_btn = ctk.CTkButton(
            btn_frame,
            text='强制退出',
            width=120,
            height=40,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=ModernColors.ERROR,
            hover_color='#dc2626',
            font=ctk.CTkFont(size=14),
            command=self._on_force_exit
        )
        exit_btn.pack(side='right')
        
        # 等待到后台按钮
        wait_btn = ctk.CTkButton(
            btn_frame,
            text='后台运行',
            width=100,
            height=40,
            corner_radius=Spacing.RADIUS_MD,
            fg_color='gray40',
            font=ctk.CTkFont(size=13),
            command=self._on_minimize
        )
        wait_btn.pack(side='right', padx=(0, 10))
        
        # 绑定 ESC 键
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
        
        # 绑定窗口关闭事件
        self.dialog.protocol('WM_DELETE_WINDOW', self._on_cancel)
        
        # 等待对话框关闭
        self.dialog.wait_window()
    
    def _on_cancel(self):
        """取消/继续任务"""
        self.result = 'cancel'
        self.dialog.destroy()
    
    def _on_force_exit(self):
        """强制退出"""
        self.result = 'exit'
        self.dialog.destroy()
    
    def _on_minimize(self):
        """最小化到后台"""
        self.result = 'minimize'
        self.dialog.destroy()
    
    def get(self) -> str:
        """获取结果
        
        Returns:
            'cancel': 用户选择继续任务
            'exit': 用户选择强制退出
            'minimize': 用户选择最小化到后台
        """
        return self.result or 'cancel'


class BatchArchiveExportDialog:
    """批量压缩导出对话框 - 支持文章选择和多格式压缩
    
    Features:
    - 支持选择要导出的文章（全选/反选）
    - 支持 ZIP、7z、RAR 三种压缩格式
    - 显示各格式的可用性状态
    - 模态对话框
    """
    
    def __init__(self, parent, articles: list, archive_exporter=None):
        """创建批量压缩导出对话框
        
        Args:
            parent: 父窗口
            articles: 文章列表
            archive_exporter: 多格式压缩导出器实例（用于检测格式可用性）
        """
        from ...infrastructure.adapters.exporters import MultiFormatArchiveExporter, ArchiveFormat
        
        self.result = None  # {'articles': [...], 'format': 'zip', 'path': '...'}
        self.articles = articles
        self._archive_exporter = archive_exporter or MultiFormatArchiveExporter()
        self._format_infos = self._archive_exporter.get_available_formats()
        
        # 存储复选框变量
        self._article_vars: list[ctk.BooleanVar] = []
        
        # 创建对话框窗口
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title('📦 批量压缩导出')
        
        # 根据文章数量调整窗口高度
        base_height = 480
        article_height = min(len(articles) * 35, 250)  # 每篇文章 35 像素，最多 250
        window_height = base_height + article_height
        self.dialog.geometry(f'550x{window_height}')
        self.dialog.resizable(False, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()  # 模态
        
        # 居中显示
        self.dialog.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 550) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.dialog.geometry(f'+{x}+{y}')
        
        # 主容器
        container = ctk.CTkFrame(self.dialog, fg_color='transparent')
        container.pack(fill='both', expand=True, padx=20, pady=15)
        
        # 标题
        header_frame = ctk.CTkFrame(container, fg_color='transparent')
        header_frame.pack(fill='x', pady=(0, 10))
        
        ctk.CTkLabel(
            header_frame,
            text='📦 批量压缩导出',
            font=ctk.CTkFont(size=20, weight='bold')
        ).pack(side='left')
        
        ctk.CTkLabel(
            header_frame,
            text=f'共 {len(articles)} 篇文章',
            font=ctk.CTkFont(size=13),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY)
        ).pack(side='right')
        
        # ========== 文章选择区域 ==========
        article_section = ctk.CTkFrame(container, fg_color='transparent')
        article_section.pack(fill='both', expand=True, pady=(0, 10))
        
        # 文章选择标题栏
        article_header = ctk.CTkFrame(article_section, fg_color='transparent')
        article_header.pack(fill='x', pady=(0, 5))
        
        ctk.CTkLabel(
            article_header,
            text='📄 选择要导出的文章',
            font=ctk.CTkFont(size=14, weight='bold')
        ).pack(side='left')
        
        # 全选/反选按钮
        btn_frame = ctk.CTkFrame(article_header, fg_color='transparent')
        btn_frame.pack(side='right')
        
        ctk.CTkButton(
            btn_frame,
            text='全选',
            width=60,
            height=28,
            corner_radius=Spacing.RADIUS_SM,
            fg_color='gray40',
            font=ctk.CTkFont(size=11),
            command=self._select_all
        ).pack(side='left', padx=(0, 5))
        
        ctk.CTkButton(
            btn_frame,
            text='反选',
            width=60,
            height=28,
            corner_radius=Spacing.RADIUS_SM,
            fg_color='gray40',
            font=ctk.CTkFont(size=11),
            command=self._toggle_selection
        ).pack(side='left')
        
        # 文章列表（可滚动）
        self.article_list_frame = ctk.CTkScrollableFrame(
            article_section,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=(ModernColors.LIGHT_BG_SECONDARY, ModernColors.DARK_BG_SECONDARY),
            height=article_height
        )
        self.article_list_frame.pack(fill='both', expand=True)
        
        # 添加文章复选框
        for i, article in enumerate(articles):
            var = ctk.BooleanVar(value=True)  # 默认全选
            self._article_vars.append(var)
            
            item_frame = ctk.CTkFrame(self.article_list_frame, fg_color='transparent')
            item_frame.pack(fill='x', pady=2)
            
            cb = ctk.CTkCheckBox(
                item_frame,
                text='',
                variable=var,
                width=20,
                checkbox_width=18,
                checkbox_height=18,
                corner_radius=Spacing.RADIUS_SM,
                command=self._update_selection_count
            )
            cb.pack(side='left', padx=(5, 8))
            
            # 文章标题（截断显示）
            title_text = article.title[:45] + '...' if len(article.title) > 45 else article.title
            ctk.CTkLabel(
                item_frame,
                text=f'{i + 1}. {title_text}',
                font=ctk.CTkFont(size=12),
                anchor='w'
            ).pack(side='left', fill='x', expand=True)
        
        # 选中计数标签
        self.selection_count_label = ctk.CTkLabel(
            article_section,
            text=f'已选择 {len(articles)} 篇',
            font=ctk.CTkFont(size=11),
            text_color=ModernColors.INFO
        )
        self.selection_count_label.pack(anchor='w', pady=(5, 0))
        
        # ========== 格式选择区域 ==========
        format_section = ctk.CTkFrame(container, fg_color='transparent')
        format_section.pack(fill='x', pady=(10, 10))
        
        ctk.CTkLabel(
            format_section,
            text='📁 选择压缩格式',
            font=ctk.CTkFont(size=14, weight='bold')
        ).pack(anchor='w', pady=(0, 8))
        
        # 格式选项
        self._format_var = ctk.StringVar(value='zip')  # 默认 ZIP
        
        format_options_frame = ctk.CTkFrame(
            format_section,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=(ModernColors.LIGHT_BG_SECONDARY, ModernColors.DARK_BG_SECONDARY)
        )
        format_options_frame.pack(fill='x')
        
        for info in self._format_infos:
            self._create_format_option(format_options_frame, info)
        
        # ========== 按钮区域 ==========
        btn_section = ctk.CTkFrame(container, fg_color='transparent')
        btn_section.pack(fill='x', pady=(15, 0))
        
        # 取消按钮
        ctk.CTkButton(
            btn_section,
            text='取消',
            width=100,
            height=40,
            corner_radius=Spacing.RADIUS_MD,
            fg_color='gray40',
            font=ctk.CTkFont(size=14),
            command=self._on_cancel
        ).pack(side='left')
        
        # 导出按钮
        self.export_btn = ctk.CTkButton(
            btn_section,
            text='📦 选择路径并导出',
            width=180,
            height=40,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=ModernColors.SUCCESS,
            hover_color='#059669',
            font=ctk.CTkFont(size=14, weight='bold'),
            command=self._on_export
        )
        self.export_btn.pack(side='right')
        
        # 绑定事件
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
        self.dialog.protocol('WM_DELETE_WINDOW', self._on_cancel)
        
        # 等待对话框关闭
        self.dialog.wait_window()
    
    def _create_format_option(self, parent, format_info):
        """创建格式选项"""
        frame = ctk.CTkFrame(parent, fg_color='transparent')
        frame.pack(fill='x', padx=10, pady=5)
        
        # 单选按钮
        rb = ctk.CTkRadioButton(
            frame,
            text='',
            variable=self._format_var,
            value=format_info.format.value,
            width=20,
            radiobutton_width=18,
            radiobutton_height=18,
            state='normal' if format_info.available else 'disabled'
        )
        rb.pack(side='left', padx=(0, 8))
        
        # 格式名称和状态
        text_frame = ctk.CTkFrame(frame, fg_color='transparent')
        text_frame.pack(side='left', fill='x', expand=True)
        
        # 状态图标 + 名称
        status_icon = '✓' if format_info.available else '✗'
        status_color = ModernColors.SUCCESS if format_info.available else ModernColors.ERROR
        
        name_frame = ctk.CTkFrame(text_frame, fg_color='transparent')
        name_frame.pack(fill='x')
        
        ctk.CTkLabel(
            name_frame,
            text=status_icon,
            font=ctk.CTkFont(size=12),
            text_color=status_color,
            width=20
        ).pack(side='left')
        
        ctk.CTkLabel(
            name_frame,
            text=f'{format_info.name} ({format_info.extension})',
            font=ctk.CTkFont(size=13, weight='bold' if format_info.available else 'normal'),
            text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT) if format_info.available else 'gray50'
        ).pack(side='left', padx=(5, 0))
        
        # 原因说明
        ctk.CTkLabel(
            text_frame,
            text=format_info.reason,
            font=ctk.CTkFont(size=10),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY)
        ).pack(anchor='w', padx=(25, 0))
    
    def _select_all(self):
        """全选文章"""
        for var in self._article_vars:
            var.set(True)
        self._update_selection_count()
    
    def _toggle_selection(self):
        """反选文章"""
        for var in self._article_vars:
            var.set(not var.get())
        self._update_selection_count()
    
    def _update_selection_count(self):
        """更新选中计数"""
        count = sum(1 for var in self._article_vars if var.get())
        self.selection_count_label.configure(text=f'已选择 {count} 篇')
        
        # 如果没有选中任何文章，禁用导出按钮
        if count == 0:
            self.export_btn.configure(state='disabled')
        else:
            self.export_btn.configure(state='normal')
    
    def _on_cancel(self):
        """取消"""
        self.result = None
        self.dialog.destroy()
    
    def _on_export(self):
        """导出"""
        # 获取选中的文章
        selected_articles = [
            article for article, var in zip(self.articles, self._article_vars)
            if var.get()
        ]
        
        if not selected_articles:
            messagebox.showwarning('提示', '请至少选择一篇文章')
            return
        
        # 获取选中的格式
        format_value = self._format_var.get()
        
        # 检查格式是否可用
        format_info = next(
            (f for f in self._format_infos if f.format.value == format_value),
            None
        )
        if not format_info or not format_info.available:
            messagebox.showerror('错误', f'所选格式 {format_value} 不可用')
            return
        
        # 选择保存路径
        ext = format_info.extension
        filetypes = [
            (f'{format_info.name} 文件', f'*{ext}'),
            ('所有文件', '*.*')
        ]
        
        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=filetypes,
            initialfile=f'articles_{len(selected_articles)}篇{ext}'
        )
        
        if not path:
            return  # 用户取消选择
        
        self.result = {
            'articles': selected_articles,
            'format': format_value,
            'path': path
        }
        self.dialog.destroy()
    
    def get(self):
        """获取结果
        
        Returns:
            dict: {'articles': [...], 'format': 'zip'/'7z'/'rar', 'path': '...'}
            None: 用户取消
        """
        return self.result


class StartupTask:
    """启动任务定义
    
    每个任务包含名称、权重和执行函数
    """
    def __init__(self, name: str, weight: int, func, description: str = ''):
        self.name = name
        self.weight = weight  # 任务权重，用于计算进度百分比
        self.func = func
        self.description = description
        self.completed = False
        self.error = None


class SplashScreen:
    """启动画面 - 带真实进度跟踪的加载界面
    
    Features:
    - 无边框窗口
    - Logo 和标题
    - 副标题
    - 带呼吸效果的进度条，显示真实任务进度
    - 启动步骤文字显示当前正在执行的任务
    - 线程安全的进度更新
    """
    
    def __init__(self, root):
        """创建启动画面
        
        Args:
            root: 主窗口 (CTk)
        """
        self.root = root
        self._progress = 0
        self._target_progress = 0  # 目标进度，用于平滑动画
        self._closed = False
        self._breathing_phase = 0
        self._breathing_id = None
        self._progress_animation_id = None
        self._tasks: list[StartupTask] = []
        self._total_weight = 0
        self._completed_weight = 0
        
        # 创建顶层窗口
        self.window = ctk.CTkToplevel(root)
        self.window.withdraw()  # 先隐藏
        self.window.overrideredirect(True)  # 无边框
        self.window.attributes('-topmost', True)
        
        # 窗口尺寸和位置
        width = 520
        height = 360
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        # 主容器
        self.container = ctk.CTkFrame(
            self.window,
            corner_radius=Spacing.RADIUS_XL,
            fg_color=ModernColors.DARK_BG,
            border_width=1,
            border_color=ModernColors.DARK_BORDER
        )
        self.container.pack(fill='both', expand=True)
        
        # 内容区
        content = ctk.CTkFrame(self.container, fg_color='transparent')
        content.pack(fill='both', expand=True, padx=40, pady=30)
        
        # Logo/标题
        self.title_label = ctk.CTkLabel(
            content,
            text='📰 文章助手',
            font=ctk.CTkFont(size=32, weight='bold'),
            text_color=ModernColors.DARK_ACCENT
        )
        self.title_label.pack(pady=(20, 5))
        
        # 副标题
        self.subtitle_label = ctk.CTkLabel(
            content,
            text='WeChat Article Summarizer',
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.DARK_TEXT_SECONDARY
        )
        self.subtitle_label.pack(pady=(0, 30))
        
        # 进度条容器
        progress_container = ctk.CTkFrame(content, fg_color='transparent')
        progress_container.pack(fill='x', pady=10)
        
        # 进度条
        self.progress_bar = ctk.CTkProgressBar(
            progress_container,
            width=400,
            height=10,
            corner_radius=5,
            fg_color=ModernColors.DARK_CARD,
            progress_color=ModernColors.DARK_ACCENT
        )
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0)
        
        # 进度百分比标签
        self.percent_label = ctk.CTkLabel(
            progress_container,
            text='0%',
            font=ctk.CTkFont(size=11, weight='bold'),
            text_color=ModernColors.DARK_ACCENT
        )
        self.percent_label.pack(pady=(2, 0))
        
        # 状态文字
        self.status_label = ctk.CTkLabel(
            content,
            text='正在准备启动...',
            font=ctk.CTkFont(size=13),
            text_color=ModernColors.DARK_TEXT_SECONDARY
        )
        self.status_label.pack(pady=(15, 5))
        
        # 详细状态文字
        self.detail_label = ctk.CTkLabel(
            content,
            text='',
            font=ctk.CTkFont(size=10),
            text_color=ModernColors.DARK_TEXT_MUTED
        )
        self.detail_label.pack(pady=(0, 10))
        
        # 底部信息容器
        footer_frame = ctk.CTkFrame(content, fg_color='transparent')
        footer_frame.pack(side='bottom', fill='x', pady=(0, 5))
        
        # 版权信息 - 标准格式: Copyright © [dates] [owner]
        current_year = datetime.now().year
        copyright_text = f"© 2024-{current_year} WeChat Article Summarizer"
        self.copyright_label = ctk.CTkLabel(
            footer_frame,
            text=copyright_text,
            font=ctk.CTkFont(size=9),
            text_color=ModernColors.DARK_TEXT_MUTED
        )
        self.copyright_label.pack(pady=(0, 2))
        
        # 版本信息和许可证
        version_license_text = f"v{VERSION} | MIT License"
        self.version_label = ctk.CTkLabel(
            footer_frame,
            text=version_license_text,
            font=ctk.CTkFont(size=9),
            text_color=ModernColors.DARK_TEXT_MUTED
        )
        self.version_label.pack()
    
    def add_task(self, name: str, weight: int, func, description: str = ''):
        """添加启动任务
        
        Args:
            name: 任务名称（显示在状态标签）
            weight: 任务权重（决定进度条增量）
            func: 任务函数（将在主线程执行）
            description: 详细描述（可选）
        """
        task = StartupTask(name, weight, func, description)
        self._tasks.append(task)
        self._total_weight += weight
    
    def show(self):
        """显示启动画面"""
        self.window.deiconify()
        self.window.update()
        self._start_breathing_effect()
    
    def run_tasks(self) -> bool:
        """执行所有启动任务
        
        任务在主线程中顺序执行，但通过 update() 保持 UI 响应
        
        Returns:
            True 如果所有任务成功，否则 False
        """
        if not self._tasks:
            return True
        
        success = True
        
        for task in self._tasks:
            if self._closed:
                break
            
            # 更新状态显示
            self.status_label.configure(text=task.name)
            if task.description:
                self.detail_label.configure(text=task.description)
            else:
                self.detail_label.configure(text='')
            self.window.update()
            
            # 执行任务
            try:
                task.func()
                task.completed = True
            except Exception as e:
                task.error = str(e)
                success = False
                logger.error(f'启动任务失败 [{task.name}]: {e}')
            
            # 更新进度
            self._completed_weight += task.weight
            progress = self._completed_weight / self._total_weight if self._total_weight > 0 else 1.0
            self._animate_progress(progress)
            
            # 允许 UI 更新
            self.window.update()
        
        return success
    
    def _animate_progress(self, target: float):
        """平滑动画过渡到目标进度 - 性能优化版
        
        优化点：
        - 使用 AnimationHelper 的标准动画方法
        - 减少 update() 调用，避免阻塞主线程
        - 使用更平滑的缓动函数
        
        Args:
            target: 目标进度值 (0.0 - 1.0)
        """
        self._target_progress = target
        current = self._progress
        
        # 如果差距很小，直接设置
        if abs(target - current) < 0.01:
            self._progress = target
            self.progress_bar.set(target)
            self.percent_label.configure(text=f'{int(target * 100)}%')
            return
        
        # 使用优化的动画系统
        def update_callback(value):
            if not self._closed:
                self._progress = value
                self.progress_bar.set(value)
                self.percent_label.configure(text=f'{int(value * 100)}%')
        
        # 使用 150ms 快速动画，ease_out_quart 更平滑
        AnimationHelper.animate_value(
            self.window,
            current,
            target,
            AnimationHelper.DURATION_FAST,  # 150ms
            update_callback,
            easing=AnimationHelper.ease_out_quart  # 更平滑的缓动
        )
    
    def _start_breathing_effect(self):
        """启动进度条呼吸效果 - 性能优化版
        
        优化点：
        - 降低更新频率从 50ms 到 ~67ms（约 15fps）
        - 预计算颜色值，减少实时计算
        - 使用缓存的颜色值
        """
        import math
        
        # 预计算颜色值（缓存）
        base = ModernColors.DARK_ACCENT  # #8b5cf6
        bright = '#a78bfa'
        
        br = int(base.lstrip('#')[0:2], 16)
        bg = int(base.lstrip('#')[2:4], 16)
        bb = int(base.lstrip('#')[4:6], 16)
        
        hr = int(bright.lstrip('#')[0:2], 16)
        hg = int(bright.lstrip('#')[2:4], 16)
        hb = int(bright.lstrip('#')[4:6], 16)
        
        def breathe():
            if self._closed:
                return
            
            self._breathing_phase = (self._breathing_phase + 1) % 60
            
            # 计算呼吸亮度（正弦波）
            t = (math.sin(self._breathing_phase * math.pi / 30) + 1) / 2
            
            try:
                # 线性插值颜色
                r = int(br + (hr - br) * t)
                g = int(bg + (hg - bg) * t)
                b = int(bb + (hb - bb) * t)
                
                color = f'#{r:02x}{g:02x}{b:02x}'
                self.progress_bar.configure(progress_color=color)
            except Exception:
                pass
            
            # 降低更新频率：67ms ≈ 15fps（呼吸效果不需要 60fps）
            self._breathing_id = self.window.after(67, breathe)
        
        breathe()
    
    def update_progress(self, progress: float, status: str = None, detail: str = None):
        """手动更新进度（用于非任务模式）
        
        Args:
            progress: 进度值 (0.0 - 1.0)
            status: 状态文字
            detail: 详细描述
        """
        if self._closed:
            return
        
        self._animate_progress(progress)
        
        if status:
            self.status_label.configure(text=status)
        if detail is not None:
            self.detail_label.configure(text=detail)
        
        self.window.update()
    
    def set_complete(self, message: str = '启动完成！'):
        """设置为完成状态"""
        if self._closed:
            return
        
        self._animate_progress(1.0)
        self.status_label.configure(text=message)
        self.detail_label.configure(text='')
        # 改变进度条颜色为成功色
        self.progress_bar.configure(progress_color=ModernColors.SUCCESS)
        self.window.update()
    
    def close(self, delay_ms: int = 500):
        """关闭启动画面
        
        Args:
            delay_ms: 关闭前延迟 (毫秒)
        """
        def do_close():
            self._closed = True
            
            if self._breathing_id:
                try:
                    self.window.after_cancel(self._breathing_id)
                except Exception:
                    pass
            
            if self._progress_animation_id:
                try:
                    self.window.after_cancel(self._progress_animation_id)
                except Exception:
                    pass
            
            try:
                self.window.destroy()
            except Exception:
                pass
        
        if delay_ms > 0:
            self.window.after(delay_ms, do_close)
        else:
            do_close()


class ToastNotification:
    """Toast通知弹窗 - 带动画效果"""
    def __init__(self, parent, title: str, message: str, toast_type: str='info', duration_ms: int=3000, show_buttons: bool=False, on_confirm=None, on_cancel=None):
        """\n        Args:\n            parent: 父窗口\n            title: 通知标题\n            message: 通知消息\n            toast_type: 类型 (\"info\", \"success\", \"warning\", \"error\")\n            duration_ms: 显示时长（毫秒），0表示不自动关闭\n            show_buttons: 是否显示按钮\n            on_confirm: 确认回调\n            on_cancel: 取消回调\n        """
        self.parent = parent
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self._closed = False
        colors = {'info': (ModernColors.INFO, '#e0f2fe', 'ℹ️'), 'success': (ModernColors.SUCCESS, '#d1fae5', '✅'), 'warning': (ModernColors.WARNING, '#fef3c7', '⚠️'), 'error': (ModernColors.ERROR, '#fee2e2', '❌')}
        accent_color, bg_color, icon = colors.get(toast_type, colors['info'])
        self.window = ctk.CTkToplevel(parent)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.container = ctk.CTkFrame(self.window, corner_radius=Spacing.RADIUS_LG, fg_color=(bg_color, ModernColors.DARK_CARD), border_width=2, border_color=accent_color)
        self.container.pack(fill='both', expand=True, padx=2, pady=2)
        content = ctk.CTkFrame(self.container, fg_color='transparent')
        content.pack(fill='both', expand=True, padx=20, pady=15)
        title_frame = ctk.CTkFrame(content, fg_color='transparent')
        title_frame.pack(fill='x')
        ctk.CTkLabel(title_frame, text=f'{icon} {title}', font=ctk.CTkFont(size=16, weight='bold'), text_color=accent_color).pack(side='left')
        close_btn = ctk.CTkButton(title_frame, text='✕', width=25, height=25, corner_radius=Spacing.RADIUS_LG, fg_color='transparent', hover_color=('gray80', 'gray30'), text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT), command=self._close)
        close_btn.pack(side='right')
        ctk.CTkLabel(content, text=message, font=ctk.CTkFont(size=13), wraplength=350, justify='left', anchor='w', text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT)).pack(fill='x', pady=(10, 0))
        if show_buttons:
            btn_frame = ctk.CTkFrame(content, fg_color='transparent')
            btn_frame.pack(fill='x', pady=(15, 0))
            ctk.CTkButton(btn_frame, text='取消', width=80, height=32, corner_radius=Spacing.RADIUS_MD, fg_color='gray50', command=self._on_cancel_click).pack(side='right', padx=(5, 0))
            ctk.CTkButton(btn_frame, text='确认填入', width=100, height=32, corner_radius=Spacing.RADIUS_MD, fg_color=accent_color, command=self._on_confirm_click).pack(side='right')
        self.window.update_idletasks()
        width = max(400, self.container.winfo_reqwidth() + 4)
        height = self.container.winfo_reqheight() + 4
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + (parent_w - width) // 2
        y = parent_y + (parent_h - height) // 2
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        self.window.attributes('-alpha', 0)
        self.window.deiconify()
        self._fade_in()
        if duration_ms > 0 and (not show_buttons):
            self.window.after(duration_ms, self._fade_out)
    def _fade_in(self):
        """淡入动画"""
        def update_alpha(val):
            if not self._closed:
                try:
                    self.window.attributes('-alpha', val)
                except Exception:
                    return None
        AnimationHelper.animate_value(self.parent, 0, 1, 200, update_alpha, easing=AnimationHelper.ease_out_cubic)
    def _fade_out(self):
        """淡出动画并关闭"""
        if self._closed:
            return None
        def update_alpha(val):
            if not self._closed:
                try:
                    self.window.attributes('-alpha', val)
                except Exception:
                    pass
        def on_complete():
            self._close()
        AnimationHelper.animate_value(self.parent, 1, 0, 150, update_alpha, easing=AnimationHelper.ease_out_cubic, on_complete=on_complete)
    def _close(self):
        """关闭窗口"""
        if self._closed:
            return None
        self._closed = True
        try:
            if self.window.winfo_exists():
                self.window.withdraw()
                self.window.after(10, self._destroy_window)
        except Exception:
            pass
    def _destroy_window(self):
        """实际销毁窗口"""
        try:
            if self.window.winfo_exists():
                self.window.destroy()
        except Exception:
            pass
    def _on_confirm_click(self):
        """确认按钮点击"""
        if self.on_confirm:
            self.on_confirm()
        self._close()
    def _on_cancel_click(self):
        """取消按钮点击"""
        if self.on_cancel:
            self.on_cancel()
        self._close()
# 内存检测
try:
    import psutil
    _psutil_available = True
except ImportError:
    _psutil_available = False

def get_available_memory_gb() -> float | None:
    """获取可用内存(GB)，如果无法检测则返回 None"""
    if not _psutil_available:
        return None
    try:
        mem = psutil.virtual_memory()
        return mem.available / (1024 ** 3)
    except Exception:
        return None

LOW_MEMORY_THRESHOLD_GB = 4.0  # 低内存阈值：4GB

class UserPreferences:
    """用户偏好设置管理"""
    DEFAULT_PREFS = {'export_dir': '', 'remember_export_dir': True, 'default_export_format': 'word', 'auto_generate_summary': True, 'default_summary_method': 'simple', 'auto_start_enabled': False, 'minimize_to_tray': False, 'low_memory_mode': False, 'low_memory_prompt_dismissed': False, 'language': 'auto', 'api_keys': {'openai': '', 'anthropic': '', 'zhipu': ''}}
    def __init__(self):
        self._prefs_file = Path.home() / CONFIG_DIR_NAME / 'gui_preferences.json'
        self._prefs = self._load()
    def _load(self) -> dict:
        """加载用户偏好"""
        try:
            if self._prefs_file.exists():
                with open(self._prefs_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    return {**self.DEFAULT_PREFS, **loaded}
        except Exception as e:
            logger.warning(f'加载偏好设置失败: {e}')
        return self.DEFAULT_PREFS.copy()
    def _save(self):
        """保存用户偏好"""
        try:
            self._prefs_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._prefs_file, 'w', encoding='utf-8') as f:
                json.dump(self._prefs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f'保存偏好设置失败: {e}')
    def get(self, key: str, default=None):
        """获取偏好设置"""
        return self._prefs.get(key, default)
    def set(self, key: str, value):
        """设置偏好并保存"""
        self._prefs[key] = value
        self._save()
    @property
    def export_dir(self) -> str:
        return self._prefs.get('export_dir', '')
    @export_dir.setter
    def export_dir(self, value: str):
        self._prefs['export_dir'] = value
        self._save()
    @property
    def remember_export_dir(self) -> bool:
        return self._prefs.get('remember_export_dir', True)
    @remember_export_dir.setter
    def remember_export_dir(self, value: bool):
        self._prefs['remember_export_dir'] = value
        self._save()
    @property
    def default_export_format(self) -> str:
        return self._prefs.get('default_export_format', 'word')
    @default_export_format.setter
    def default_export_format(self, value: str):
        self._prefs['default_export_format'] = value
        self._save()
    def get_api_key(self, provider: str) -> str:
        """获取API密钥"""
        api_keys = self._prefs.get('api_keys', {})
        return api_keys.get(provider, '')
    def set_api_key(self, provider: str, key: str):
        """设置API密钥"""
        if 'api_keys' not in self._prefs:
            self._prefs['api_keys'] = {}
        self._prefs['api_keys'][provider] = key
        self._save()
    def get_all_api_keys(self) -> dict[str, str]:
        """获取所有API密钥"""
        return self._prefs.get('api_keys', {}).copy()
    @property
    def auto_start_enabled(self) -> bool:
        """开机自启动是否启用"""
        return self._prefs.get('auto_start_enabled', False)
    @auto_start_enabled.setter
    def auto_start_enabled(self, value: bool):
        self._prefs['auto_start_enabled'] = value
        self._save()
    @property
    def minimize_to_tray(self) -> bool:
        """最小化到系统托盘"""
        return self._prefs.get('minimize_to_tray', False)
    @minimize_to_tray.setter
    def minimize_to_tray(self, value: bool):
        self._prefs['minimize_to_tray'] = value
        self._save()
    @property
    def low_memory_mode(self) -> bool:
        """低内存模式"""
        return self._prefs.get('low_memory_mode', False)
    @low_memory_mode.setter
    def low_memory_mode(self, value: bool):
        self._prefs['low_memory_mode'] = value
        self._save()
    @property
    def low_memory_prompt_dismissed(self) -> bool:
        """是否已忽略低内存提示"""
        return self._prefs.get('low_memory_prompt_dismissed', False)
    @low_memory_prompt_dismissed.setter
    def low_memory_prompt_dismissed(self, value: bool):
        self._prefs['low_memory_prompt_dismissed'] = value
        self._save()
    @property
    def language(self) -> str:
        """界面语言设置 ('auto', 'zh_CN', 'en')"""
        return self._prefs.get('language', 'auto')
    @language.setter
    def language(self, value: str):
        self._prefs['language'] = value
        self._save()

class SummarizerInfo:
    """摘要器信息"""
    def __init__(self, name: str, available: bool, reason: str=''):
        self.name = name
        self.available = available
        self.reason = reason
    @property
    def display_name(self) -> str:
        if self.available:
            return f'✓ {self.name}'
        else:
            return f'✗ {self.name}'
class ExporterInfo:
    """导出器信息"""
    def __init__(self, name: str, available: bool, reason: str=''):
        self.name = name
        self.available = available
        self.reason = reason
    @property
    def display_name(self) -> str:
        if self.available:
            return f'✓ {self.name}'
        else:
            return f'✗ {self.name}'
class GUILogHandler:
    """自定义日志Handler"""
    DEFAULT_MAX_LINES = 1000
    LOW_MEMORY_MAX_LINES = 200
    
    def __init__(self, text_widget, root, low_memory_mode: bool = False):
        self.text_widget = text_widget
        self.root = root
        self._max_lines = self.LOW_MEMORY_MAX_LINES if low_memory_mode else self.DEFAULT_MAX_LINES
    
    def set_low_memory_mode(self, enabled: bool):
        """设置低内存模式"""
        self._max_lines = self.LOW_MEMORY_MAX_LINES if enabled else self.DEFAULT_MAX_LINES
    
    def write(self, message: str):
        if not message.strip():
            return None
        else:
            self.root.after(0, self._append_log, message)
    def _append_log(self, message: str):
        try:
            self.text_widget.configure(state='normal')
            self.text_widget.insert('end', message)
            self.text_widget.see('end')
            self.text_widget.configure(state='disabled')
            lines = int(self.text_widget.index('end-1c').split('.')[0])
            if lines > self._max_lines:
                self.text_widget.configure(state='normal')
                # 删除前半部分日志
                delete_to = self._max_lines // 2
                self.text_widget.delete('1.0', f'{delete_to}.0')
                self.text_widget.configure(state='disabled')
        except Exception:
            pass
class WechatSummarizerGUI:
    """微信公众号文章总结器GUI - 现代化界面"""
    PAGE_HOME = 'home'
    PAGE_SINGLE = 'single'
    PAGE_BATCH = 'batch'
    PAGE_HISTORY = 'history'
    PAGE_SETTINGS = 'settings'
    def __init__(self):
        if not _ctk_available:
            raise ImportError('customtkinter未安装，请运行: pip install customtkinter')
        else:
            # 基础初始化（不显示在进度条中）
            self.settings = get_settings()
            self.user_prefs = UserPreferences()
            set_language(self.user_prefs.language)
            
            self._chinese_font = ChineseFonts.get_best_font()
            self._appearance_mode = 'dark'
            ctk.set_appearance_mode(self._appearance_mode)
            ctk.set_default_color_theme('dark-blue')
            self.root = ctk.CTk()
            self.root.title(GUI_WINDOW_TITLE)
            self.root.geometry('1280x800')
            self.root.minsize(*GUI_MIN_SIZE)
            
            # 隐藏主窗口
            self.root.withdraw()
            
            # 创建启动画面
            splash = SplashScreen(self.root)
            
            # 预声明需要在任务中初始化的属性
            self.container = None
            self.current_article = None
            self.batch_urls = []
            self.batch_results = []
            self._current_page = self.PAGE_HOME
            self._page_frames = {}
            self._summarizer_info = []
            self._exporter_info = []
            self._log_handler = None
            self._log_handler_id = None
            self._animation_running = False
            
            # 任务运行状态跟踪（用于退出确认）
            self._batch_processing_active = False
            self._batch_export_active = False
            self._single_processing_active = False
            
            # 提示轮播组件状态
            self._tips_data = []
            self._current_tip_index = 0
            self._tip_auto_switch_id = None
            
            # 定义启动任务列表
            # 权重根据任务实际耗时估算：
            # - 简单操作(内存操作)：权重 1
            # - 中等操作(文件/配置)：权重 2
            # - 耗时操作(网络请求)：权重 4-5
            
            def task_apply_window_style():
                """应用窗口样式"""
                Windows11StyleHelper.apply_window_style(self.root, self._appearance_mode)
            
            def task_init_container():
                """初始化依赖注入容器"""
                self.container = get_container()
                # 加载 UserPreferences 中保存的 API 密钥到 Container
                saved_api_keys = self.user_prefs.get_all_api_keys()
                if any(saved_api_keys.values()):
                    self.container.reload_summarizers(saved_api_keys)
            
            def task_detect_summarizers():
                """检测可用的摘要服务"""
                self._summarizer_info = self._get_summarizer_info()
            
            def task_detect_exporters():
                """检测可用的导出器"""
                self._exporter_info = self._get_exporter_info()
            
            def task_build_ui():
                """构建用户界面"""
                self._build_ui()
            
            def task_setup_logging():
                """设置日志处理器"""
                self._setup_log_handler()
            
            def task_init_system():
                """初始化系统设置"""
                self._init_system_settings()
            
            def task_show_home():
                """显示主页"""
                self._show_page(self.PAGE_HOME)
            
            # 注册任务（名称, 权重, 函数, 详细描述）
            splash.add_task('正在应用窗口样式', 1, task_apply_window_style, '配置 Windows 11 风格')
            splash.add_task('正在初始化容器', 2, task_init_container, '加载依赖注入框架')
            splash.add_task('正在检测摘要服务', 5, task_detect_summarizers, '检测 Ollama、OpenAI 等服务状态')
            splash.add_task('正在检测导出器', 2, task_detect_exporters, '检测 Word、PDF 导出支持')
            splash.add_task('正在构建用户界面', 4, task_build_ui, '创建页面和控件')
            splash.add_task('正在配置日志系统', 1, task_setup_logging, '设置日志输出')
            splash.add_task('正在初始化系统', 2, task_init_system, '加载用户偏好设置')
            splash.add_task('正在准备主页', 1, task_show_home, '切换到主页视图')
            
            # 显示启动画面并执行任务
            splash.show()
            success = splash.run_tasks()
            
            if success:
                splash.set_complete('启动完成！')
            else:
                splash.set_complete('启动完成（部分服务不可用）')
            
            # 关闭启动画面，显示主窗口
            splash.close(delay_ms=400)
            self.root.after(450, self._show_main_window)
            
            self._check_memory_on_startup()
    
    def _show_main_window(self):
        """显示主窗口并播放欢迎动画"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self._play_welcome_animation()
    def _check_memory_on_startup(self):
        """启动时检测内存，如果低于阈值则提示用户"""
        if self.user_prefs.low_memory_mode or self.user_prefs.low_memory_prompt_dismissed:
            return
        available_gb = get_available_memory_gb()
        if available_gb is None:
            logger.debug('无法检测系统内存（psutil 未安装）')
            return
        logger.info(f'系统可用内存: {available_gb:.2f} GB')
        if available_gb < LOW_MEMORY_THRESHOLD_GB:
            self.root.after(1500, lambda: self._show_low_memory_warning(available_gb))
    def _show_low_memory_warning(self, available_gb: float):
        """显示低内存警告弹窗"""
        def on_enable():
            self.user_prefs.low_memory_mode = True
            if hasattr(self, 'low_memory_var'):
                self.low_memory_var.set(True)
            self._apply_low_memory_optimizations()
            logger.info('✅ 已启用低内存模式')
            # 使用新ToastManager (2026 UI组件)
            if hasattr(self, '_toast_manager') and self._toast_manager:
                self._toast_manager.success('已启用低内存模式，应用将减少内存占用')
            else:
                ToastNotification(self.root, '低内存模式', '已启用低内存模式，应用将减少内存占用', toast_type='success', duration_ms=3000)
        def on_dismiss():
            self.user_prefs.low_memory_prompt_dismissed = True
            logger.info('用户选择忽略低内存提示')
        ToastNotification(
            self.root,
            '⚠️ 内存不足',
            f'检测到系统可用内存仅 {available_gb:.1f} GB（低于 {LOW_MEMORY_THRESHOLD_GB:.0f} GB）\n\n建议启用「低内存模式」以获得更好的体验。',
            toast_type='warning',
            duration_ms=0,
            show_buttons=True,
            on_confirm=on_enable,
            on_cancel=on_dismiss
        )
    def _apply_low_memory_optimizations(self):
        """应用低内存模式优化"""
        # 1. 减少日志缓存行数
        if hasattr(self, '_log_handler') and self._log_handler:
            self._log_handler.set_low_memory_mode(True)
        # 2. 禁用动画效果
        self._animation_running = False
        # 3. 记录低内存模式状态，供其他组件检查
        self._low_memory_mode_active = True
        logger.debug('已应用低内存优化：减少日志缓存 (200行)、禁用动画效果')
    def _is_low_memory_mode(self) -> bool:
        """检查是否处于低内存模式"""
        return getattr(self, '_low_memory_mode_active', False) or self.user_prefs.low_memory_mode
    def _get_font(self, size: int=14, weight: str='normal') -> ctk.CTkFont:
        """获取配置好的中文字体"""
        return ctk.CTkFont(family=self._chinese_font, size=size, weight=weight)
    
    def _create_modern_button(
        self,
        master,
        text: str,
        command=None,
        variant: str = "primary",
        size: str = "medium",
        **kwargs
    ):
        """创建现代化按钮 (2026 UI设计)
        
        Args:
            master: 父容器
            text: 按钮文本
            command: 点击回调
            variant: 按钮变体 ("primary", "secondary", "ghost", "danger")
            size: 按钮尺寸 ("small", "medium", "large")
            **kwargs: 其他参数
            
        Returns:
            ModernButton: 现代化按钮实例
        """
        # 映射变体字符串到枚举
        variant_map = {
            "primary": ButtonVariant.PRIMARY,
            "secondary": ButtonVariant.SECONDARY,
            "ghost": ButtonVariant.GHOST,
            "danger": ButtonVariant.DANGER,
            "text": ButtonVariant.TEXT,
        }
        size_map = {
            "small": ButtonSize.SMALL,
            "medium": ButtonSize.MEDIUM,
            "large": ButtonSize.LARGE,
        }
        
        return ModernButton(
            master,
            text=text,
            command=command,
            variant=variant_map.get(variant, ButtonVariant.PRIMARY),
            size=size_map.get(size, ButtonSize.MEDIUM),
            theme=self._appearance_mode,
            **kwargs
        )
    
    def _create_modern_card(
        self,
        master,
        width: int = 300,
        height: int = 200,
        style: str = "elevated",
        **kwargs
    ):
        """创建现代化卡片 (2026 UI设计)
        
        Args:
            master: 父容器
            width: 宽度
            height: 高度
            style: 卡片样式 ("solid", "outlined", "elevated", "glass")
            **kwargs: 其他参数
            
        Returns:
            ModernCard: 现代化卡片实例
        """
        from .components.card import CornerRadius, ShadowDepth
        
        style_map = {
            "solid": CardStyle.SOLID,
            "outlined": CardStyle.OUTLINED,
            "elevated": CardStyle.ELEVATED,
            "glass": CardStyle.GLASS,
        }
        
        return ModernCard(
            master,
            width=width,
            height=height,
            corner_radius=CornerRadius.MEDIUM,
            shadow_depth=ShadowDepth.MEDIUM,
            style=style_map.get(style, CardStyle.ELEVATED),
            theme=self._appearance_mode,
            **kwargs
        )
    
    def _play_welcome_animation(self):
        """播放欢迎动画"""
        self._set_status('欢迎使用！', ModernColors.SUCCESS)
    def _get_summarizer_info(self) -> dict[str, SummarizerInfo]:
        """获取摘要器可用性信息"""
        info = {}
        info['simple'] = SummarizerInfo('simple', True, '基于规则的简单摘要')
        info['textrank'] = SummarizerInfo('textrank', True, '基于图算法的抽取式摘要')
        ollama_available = True
        ollama_reason = ''
        try:
            import httpx
            with httpx.Client(timeout=2) as client:
                client.get(f'{self.settings.ollama.host}/api/tags')
            ollama_reason = '本地Ollama服务'
        except Exception:
            ollama_available = False
            ollama_reason = f'无法连接到 {self.settings.ollama.host}'
        info['ollama'] = SummarizerInfo('ollama', ollama_available, ollama_reason)
        openai_key = self.user_prefs.get_api_key('openai') or self.settings.openai.api_key.get_secret_value()
        if openai_key:
            info['openai'] = SummarizerInfo('openai', True, 'OpenAI GPT')
        else:
            info['openai'] = SummarizerInfo('openai', False, '需要配置 API Key')
        # DeepSeek - 国产高性能大模型
        deepseek_key = self.user_prefs.get_api_key('deepseek') or self.settings.deepseek.api_key.get_secret_value()
        if deepseek_key:
            info['deepseek'] = SummarizerInfo('deepseek', True, 'DeepSeek V3')
        else:
            info['deepseek'] = SummarizerInfo('deepseek', False, '需要配置 API Key')
        anthropic_key = self.user_prefs.get_api_key('anthropic') or self.settings.anthropic.api_key.get_secret_value()
        if anthropic_key:
            info['anthropic'] = SummarizerInfo('anthropic', True, 'Claude AI')
        else:
            info['anthropic'] = SummarizerInfo('anthropic', False, '需要配置 API Key')
        zhipu_key = self.user_prefs.get_api_key('zhipu') or self.settings.zhipu.api_key.get_secret_value()
        if zhipu_key:
            info['zhipu'] = SummarizerInfo('zhipu', True, '智谱AI GLM')
        else:
            info['zhipu'] = SummarizerInfo('zhipu', False, '需要配置 API Key')
        return info
    def _get_exporter_info(self) -> dict[str, ExporterInfo]:
        """获取导出器可用性信息"""
        info = {}
        info['html'] = ExporterInfo('html', True)
        info['markdown'] = ExporterInfo('markdown', True)
        info['zip'] = ExporterInfo('zip', True)
        try:
            import docx
            info['word'] = ExporterInfo('word', True)
        except ImportError:
            info['word'] = ExporterInfo('word', False, '缺少 python-docx')
        return info
    def _setup_log_handler(self):
        """设置日志Handler"""
        if hasattr(self, 'log_text') and self.log_text:
            self._log_handler = GUILogHandler(self.log_text, self.root, low_memory_mode=self.user_prefs.low_memory_mode)
            self._log_handler_id = logger.add(self._log_handler.write, format='{time:HH:mm:ss} | {level:<8} | {message}', level='DEBUG', colorize=False)
            logger.info('🚀 应用已启动')
            # 如果已启用低内存模式，应用优化
            if self.user_prefs.low_memory_mode:
                self._apply_low_memory_optimizations()
                logger.info('📦 低内存模式已启用')
    def _init_system_settings(self):
        """初始化系统设置"""
        # 始终设置窗口关闭事件处理器（处理退出确认）
        self.root.protocol('WM_DELETE_WINDOW', self._on_window_close)
        
        if self.user_prefs.minimize_to_tray:
            logger.debug('已启用最小化到系统托盘')
        self._sync_autostart_status()
    def _sync_autostart_status(self):
        """同步开机自启动状态（检查实际快捷方式是否存在）"""
        startup_folder = Path.home() / 'AppData' / 'Roaming' / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
        shortcut_path = startup_folder / '微信文章总结器.lnk'
        actual_enabled = shortcut_path.exists()
        if self.user_prefs.auto_start_enabled!= actual_enabled:
            self.user_prefs.auto_start_enabled = actual_enabled
            logger.debug(f"开机自启动状态已同步: {('enabled' if actual_enabled else 'disabled')}")
    def _build_ui(self):
        """构建用户界面"""
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main_content()
        
        # 初始化全局Toast管理器 (2026 UI组件)
        self._toast_manager = init_toast_manager(
            self.root,
            position="top-right",
            theme=self._appearance_mode
        )
        
        # 初始化性能监控 (2026 UI组件)
        self._perf_monitor = PerformanceMonitor()
        if not self._is_low_memory_mode():
            # 仅在非低内存模式下启用性能监控
            self._perf_monitor.start_monitoring(
                on_memory_warning=self._on_memory_warning
            )
            logger.debug('性能监控已启动')
        
        # 初始化快捷键系统 (2026 UI组件)
        self._shortcut_manager = KeyboardShortcutManager(self.root)
        self._register_app_shortcuts()
        logger.debug('快捷键系统已初始化')
        
        # 初始化响应式布局系统 (2026 UI组件)
        self._breakpoint_manager = BreakpointManager(self.root)
        self._responsive_layout = ResponsiveLayout(self._breakpoint_manager)
        self._breakpoint_manager.on_breakpoint_change(self._on_breakpoint_change)
        logger.debug('响应式布局系统已初始化')
    
    def _on_memory_warning(self, memory_mb: float):
        """内存警告回调"""
        if memory_mb > 800:
            logger.warning(f'⚠️ 内存使用过高: {memory_mb:.1f} MB')
            if hasattr(self, '_toast_manager') and self._toast_manager:
                self._toast_manager.warning(f'内存使用过高: {memory_mb:.0f}MB')
    
    def _on_breakpoint_change(self, breakpoint: Breakpoint, width: int, height: int):
        """响应式布局断点变化回调 (2026 UI)
        
        根据窗口大小调整布局：
        - XS (<768px): 紧凑布局，隐藏部分元素
        - SM (768-1024px): 平板布局
        - MD (1024-1440px): 标准布局
        - LG (1440-1920px): 桌面布局
        - XL (>1920px): 宽屏布局
        
        Args:
            breakpoint: 当前断点
            width: 窗口宽度
            height: 窗口高度
        """
        logger.debug(f'响应式布局: 断点={breakpoint.value}, 尺寸={width}x{height}')
        
        # 根据断点调整侧边栏宽度
        if hasattr(self, 'sidebar') and self.sidebar:
            if breakpoint == Breakpoint.XS:
                # 移动端：隐藏侧边栏文字，只显示图标
                self.sidebar.configure(width=60)
            elif breakpoint == Breakpoint.SM:
                # 平板：稍窄侧边栏
                self.sidebar.configure(width=180)
            else:
                # 桌面：标准宽度
                self.sidebar.configure(width=220)
    
    def _register_app_shortcuts(self):
        """注册应用程序快捷键"""
        shortcuts = [
            Shortcut(
                id="goto_home",
                name="跳转首页",
                keys="Ctrl+1",
                callback=lambda: self._show_page(self.PAGE_HOME),
                group="导航",
                description="跳转到首页"
            ),
            Shortcut(
                id="goto_single",
                name="跳转单篇处理",
                keys="Ctrl+2",
                callback=lambda: self._show_page(self.PAGE_SINGLE),
                group="导航",
                description="跳转到单篇处理页面"
            ),
            Shortcut(
                id="goto_batch",
                name="跳转批量处理",
                keys="Ctrl+3",
                callback=lambda: self._show_page(self.PAGE_BATCH),
                group="导航",
                description="跳转到批量处理页面"
            ),
            Shortcut(
                id="goto_history",
                name="跳转历史记录",
                keys="Ctrl+4",
                callback=lambda: self._show_page(self.PAGE_HISTORY),
                group="导航",
                description="跳转到历史记录页面"
            ),
            Shortcut(
                id="goto_settings",
                name="跳转设置",
                keys="Ctrl+,",
                callback=lambda: self._show_page(self.PAGE_SETTINGS),
                group="导航",
                description="跳转到设置页面"
            ),
            Shortcut(
                id="toggle_theme",
                name="切换主题",
                keys="Ctrl+D",
                callback=self._toggle_theme,
                group="视图",
                description="切换深色/浅色主题"
            ),
        ]
        
        for shortcut in shortcuts:
            self._shortcut_manager.register(shortcut)
    
    def _toggle_theme(self):
        """切换主题"""
        current = self.theme_switch.get()
        new_theme = '浅色' if current == '深色' else '深色'
        self.theme_switch.set(new_theme)
        self._on_theme_change(new_theme)
    
    def _create_modern_input(
        self,
        master,
        placeholder: str = "",
        label: str = None,
        show_clear_button: bool = True,
        **kwargs
    ):
        """创建现代化输入框 (2026 UI设计)
        
        Args:
            master: 父容器
            placeholder: 占位符文本
            label: 浮动标签文本
            show_clear_button: 是否显示清除按钮
            **kwargs: 其他参数
            
        Returns:
            ModernInput: 现代化输入框实例
        """
        return ModernInput(
            master,
            placeholder=placeholder,
            label=label,
            show_clear_button=show_clear_button,
            theme=self._appearance_mode,
            **kwargs
        )
    
    def _build_sidebar(self):
        """构建左侧导航栏"""
        self.sidebar = ctk.CTkFrame(self.root, width=220, corner_radius=0, fg_color=(ModernColors.LIGHT_SIDEBAR, ModernColors.DARK_SIDEBAR))
        self.sidebar.grid(row=0, column=0, sticky='nswe')
        self.sidebar.grid_rowconfigure(10, weight=1)
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color='transparent')
        logo_frame.grid(row=0, column=0, padx=20, pady=(25, 30), sticky='ew')
        title_label = ctk.CTkLabel(logo_frame, text='📰 文章助手', font=self._get_font(22, 'bold'), text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT))
        title_label.pack(anchor='w')
        subtitle_label = ctk.CTkLabel(logo_frame, text='WeChat Article Summarizer', font=self._get_font(11), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY))
        subtitle_label.pack(anchor='w')
        self._nav_buttons = {}
        nav_items = [(self.PAGE_HOME, '🏠', '首页'), (self.PAGE_SINGLE, '📄', '单篇处理'), (self.PAGE_BATCH, '📚', '批量处理'), (self.PAGE_HISTORY, '📜', '历史记录'), (self.PAGE_SETTINGS, '⚙️', '设置')]
        for i, (page_id, icon, text) in enumerate(nav_items):
            btn = ctk.CTkButton(self.sidebar, text=f'  {icon}  {text}', font=self._get_font(14), height=45, anchor='w', corner_radius=Spacing.RADIUS_MD, fg_color='transparent', text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT), hover_color=('#e0e0e0', '#2a2a4a'), command=lambda p=page_id: self._show_page_animated(p))
            btn.grid(row=i + 1, column=0, padx=12, pady=4, sticky='ew')
            self._nav_buttons[page_id] = btn
        settings_frame = ctk.CTkFrame(self.sidebar, fg_color='transparent')
        settings_frame.grid(row=11, column=0, padx=15, pady=15, sticky='sew')
        theme_label = ctk.CTkLabel(settings_frame, text='🎨 外观主题', font=self._get_font(12), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY))
        theme_label.pack(anchor='w', pady=(0, 5))
        self.theme_switch = ctk.CTkSegmentedButton(settings_frame, values=['浅色', '深色'], command=self._on_theme_change, font=self._get_font(12))
        self.theme_switch.set('深色')
        self.theme_switch.pack(fill='x')
        
        # 紧凑状态栏 - 类似 VS Code 底部状态栏设计
        self._build_sidebar_status_bar(settings_frame)
        
        self.status_label = ctk.CTkLabel(settings_frame, text='● 就绪', font=self._get_font(11), text_color=ModernColors.SUCCESS)
        self.status_label.pack(anchor='w', pady=(10, 0))
    
    def _build_sidebar_status_bar(self, parent):
        """构建侧边栏底部状态栏 - 紧凑型状态指示器
        
        参考 VS Code 状态栏设计：
        - 状态栏位于底部，显示与工作区相关的信息
        - 使用紧凑的图标+文本形式
        - 点击可跳转到设置页查看详情
        """
        status_bar = ctk.CTkFrame(parent, fg_color='transparent', height=30)
        status_bar.pack(fill='x', pady=(12, 0))
        
        # 计算状态
        summarizer_count = sum(1 for info in self._summarizer_info.values() if info.available)
        summarizer_total = len(self._summarizer_info)
        exporter_count = sum(1 for info in self._exporter_info.values() if info.available)
        exporter_total = len(self._exporter_info)
        
        # 状态指示器容器
        indicators = ctk.CTkFrame(status_bar, fg_color='transparent')
        indicators.pack(fill='x')
        
        # 摘要器状态 - 紧凑形式
        summarizer_ok = summarizer_count > 0
        summarizer_color = ModernColors.SUCCESS if summarizer_ok else ModernColors.ERROR
        summarizer_btn = ctk.CTkButton(
            indicators,
            text=f'● {summarizer_count}/{summarizer_total}',
            font=self._get_font(10),
            height=22,
            width=55,
            corner_radius=Spacing.RADIUS_SM,
            fg_color='transparent',
            text_color=summarizer_color,
            hover_color=('#e0e0e0', '#2a2a4a'),
            command=lambda: self._show_page_animated(self.PAGE_SETTINGS)
        )
        summarizer_btn.pack(side='left', padx=(0, 4))
        # 添加提示
        self._create_tooltip(summarizer_btn, f'摘要器: {summarizer_count}/{summarizer_total} 可用\n点击查看详情')
        
        # 导出器状态
        exporter_ok = exporter_count > 0
        exporter_color = ModernColors.SUCCESS if exporter_ok else ModernColors.ERROR
        exporter_btn = ctk.CTkButton(
            indicators,
            text=f'● {exporter_count}/{exporter_total}',
            font=self._get_font(10),
            height=22,
            width=55,
            corner_radius=Spacing.RADIUS_SM,
            fg_color='transparent',
            text_color=exporter_color,
            hover_color=('#e0e0e0', '#2a2a4a'),
            command=lambda: self._show_page_animated(self.PAGE_SETTINGS)
        )
        exporter_btn.pack(side='left', padx=(0, 4))
        self._create_tooltip(exporter_btn, f'导出器: {exporter_count}/{exporter_total} 可用\n点击查看详情')
        
        # 缓存状态
        try:
            storage = self.container.storage
            if storage:
                stats = storage.get_stats()
                cache_count = stats.total_entries
            else:
                cache_count = 0
        except Exception:
            cache_count = 0
        
        cache_btn = ctk.CTkButton(
            indicators,
            text=f'🗃 {cache_count}',
            font=self._get_font(10),
            height=22,
            width=50,
            corner_radius=Spacing.RADIUS_SM,
            fg_color='transparent',
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
            hover_color=('#e0e0e0', '#2a2a4a'),
            command=lambda: self._show_page_animated(self.PAGE_HISTORY)
        )
        cache_btn.pack(side='left')
        self._create_tooltip(cache_btn, f'缓存: {cache_count} 条记录\n点击查看历史记录')
    
    def _create_tooltip(self, widget, text: str):
        """创建简单的工具提示
        
        Args:
            widget: 要添加提示的控件
            text: 提示文本
        """
        tooltip = None
        
        def show_tooltip(event):
            nonlocal tooltip
            if tooltip:
                return
            x = widget.winfo_rootx() + widget.winfo_width() + 5
            y = widget.winfo_rooty()
            
            tooltip = ctk.CTkToplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f'+{x}+{y}')
            tooltip.attributes('-topmost', True)
            
            label = ctk.CTkLabel(
                tooltip,
                text=text,
                font=self._get_font(10),
                fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
                corner_radius=Spacing.RADIUS_SM,
                padx=8,
                pady=4
            )
            label.pack()
        
        def hide_tooltip(event):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)
    def _build_main_content(self):
        """构建主内容区"""
        self.main_container = ctk.CTkFrame(self.root, corner_radius=0, fg_color=(ModernColors.LIGHT_BG, ModernColors.DARK_BG))
        self.main_container.grid(row=0, column=1, sticky='nswe')
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=0)
        self.content_area = ctk.CTkFrame(self.main_container, fg_color='transparent')
        self.content_area.grid(row=0, column=0, sticky='nswe', padx=20, pady=(20, 10))
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)
        self._build_home_page()
        self._build_single_page()
        self._build_batch_page()
        self._build_history_page()
        self._build_settings_page()
        self._build_log_panel()
    def _build_home_page(self):
        """构建首页"""
        frame = ctk.CTkFrame(self.content_area, fg_color='transparent')
        self._page_frames[self.PAGE_HOME] = frame
        welcome_frame = ctk.CTkFrame(frame, fg_color='transparent')
        welcome_frame.pack(fill='x', pady=(0, 30))
        ctk.CTkLabel(welcome_frame, text='👋 欢迎使用文章助手', font=self._get_font(28, 'bold'), text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT)).pack(anchor='w')
        ctk.CTkLabel(welcome_frame, text='快速抓取、总结和导出微信公众号文章', font=self._get_font(14), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY)).pack(anchor='w', pady=(5, 0))
        cards_frame = ctk.CTkFrame(frame, fg_color='transparent')
        cards_frame.pack(fill='x', pady=10)
        cards_frame.grid_columnconfigure((0, 1, 2), weight=1)
        cards = [('📄', '单篇处理', '抓取单篇文章并生成摘要', self.PAGE_SINGLE, ModernColors.INFO), ('📚', '批量处理', '批量处理多篇文章', self.PAGE_BATCH, ModernColors.SUCCESS), ('📜', '历史记录', '查看已处理的文章', self.PAGE_HISTORY, ModernColors.WARNING)]
        for i, (icon, title, desc, page, color) in enumerate(cards):
            card = self._create_animated_card(cards_frame, icon=icon, title=title, desc=desc, color=color, command=lambda p=page: self._show_page(p))
            card.grid(row=0, column=i, padx=10, pady=10, sticky='nsew')
        
        # 版权信息
        self._build_copyright_footer(frame)
    def _build_copyright_footer(self, parent):
        """构建版权信息组件
        
        标准版权声明格式：
        Copyright © [年份] [作者/所有者]. All rights reserved.
        """
        current_year = datetime.now().year
        
        # 版权信息容器
        copyright_frame = ctk.CTkFrame(
            parent,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            border_width=1,
            border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER)
        )
        copyright_frame.pack(fill='x', pady=20)
        
        # 内部容器
        inner = ctk.CTkFrame(copyright_frame, fg_color='transparent')
        inner.pack(fill='x', padx=20, pady=15)
        
        # 版权标志
        logo_label = ctk.CTkLabel(
            inner,
            text='©',
            font=ctk.CTkFont(size=24, weight='bold'),
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT)
        )
        logo_label.pack(side='left')
        
        # 版权文字容器
        text_frame = ctk.CTkFrame(inner, fg_color='transparent')
        text_frame.pack(side='left', padx=(12, 0), fill='x', expand=True)
        
        # 主版权声明
        copyright_text = f"Copyright © 2024-{current_year} WeChat Article Summarizer"
        main_label = ctk.CTkLabel(
            text_frame,
            text=copyright_text,
            font=ctk.CTkFont(size=12, weight='bold'),
            text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
            anchor='w'
        )
        main_label.pack(fill='x')
        
        # 权利声明
        rights_label = ctk.CTkLabel(
            text_frame,
            text="All rights reserved. | 版权所有，保留所有权利",
            font=ctk.CTkFont(size=11),
            text_color=(ModernColors.LIGHT_TEXT_MUTED, ModernColors.DARK_TEXT_MUTED),
            anchor='w'
        )
        rights_label.pack(fill='x', pady=(2, 0))
        
        # 开源许可证
        license_label = ctk.CTkLabel(
            text_frame,
            text="Licensed under MIT License | 开源许可证：MIT",
            font=ctk.CTkFont(size=10),
            text_color=(ModernColors.LIGHT_TEXT_MUTED, ModernColors.DARK_TEXT_MUTED),
            anchor='w'
        )
        license_label.pack(fill='x', pady=(2, 0))
        
        # 版本信息
        version_label = ctk.CTkLabel(
            inner,
            text=f"v{VERSION}",
            font=ctk.CTkFont(size=11),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY)
        )
        version_label.pack(side='right')
    
    def _build_tips_carousel_legacy(self, parent):
        """构建动态提示轮播组件 (已弃用 - 保留备用)
        
        采用 UX 最佳实践:
        - 自动轮播 + 手动切换
        - 简洁文案 (<180字符)
        - 分类标签 (快速开始/快捷键/进阶技巧)
        - 上下文相关提示
        """
        # 提示数据 - 分类组织
        self._tips_data = [
            # 快速开始类
            {
                'category': '🚀 快速开始',
                'category_en': '🚀 Quick Start',
                'icon': '📋',
                'title': '粘贴即用',
                'title_en': 'Paste to Start',
                'content': '复制微信文章链接后，直接粘贴到「单篇处理」输入框即可开始',
                'content_en': 'Copy a WeChat article URL and paste it into Single Article input',
                'color': ModernColors.INFO
            },
            {
                'category': '🚀 快速开始',
                'category_en': '🚀 Quick Start',
                'icon': '📚',
                'title': '批量处理',
                'title_en': 'Batch Processing',
                'content': '每行一个链接，支持同时处理数十篇文章，自动跳过无效链接',
                'content_en': 'One URL per line, process dozens of articles at once',
                'color': ModernColors.SUCCESS
            },
            {
                'category': '🚀 快速开始',
                'category_en': '🚀 Quick Start',
                'icon': '🤖',
                'title': 'AI 摘要',
                'title_en': 'AI Summary',
                'content': '配置 API 密钥后可使用 DeepSeek/OpenAI 生成高质量智能摘要',
                'content_en': 'Configure API keys to use DeepSeek/OpenAI for smart summaries',
                'color': ModernColors.GRADIENT_MID
            },
            {
                'category': '🚀 快速开始',
                'category_en': '🚀 Quick Start',
                'icon': '📂',
                'title': '从文件导入',
                'title_en': 'Import from File',
                'content': '在批量处理页面点击「从文件导入」，支持 .txt 文件批量导入链接',
                'content_en': 'Click "Import from File" in Batch page to load URLs from .txt file',
                'color': ModernColors.INFO
            },
            # 快捷键类
            {
                'category': '⌨️ 快捷键',
                'category_en': '⌨️ Shortcuts',
                'icon': '⌨️',
                'title': '快速切换',
                'title_en': 'Quick Switch',
                'content': 'Ctrl+1/2/3/4 快速切换页面，Ctrl+D 切换深色/浅色主题',
                'content_en': 'Ctrl+1/2/3/4 to switch pages, Ctrl+D to toggle dark/light theme',
                'color': ModernColors.WARNING
            },
            {
                'category': '⌨️ 快捷键',
                'category_en': '⌨️ Shortcuts',
                'icon': '📥',
                'title': '快速导出',
                'title_en': 'Quick Export',
                'content': 'Ctrl+E 导出当前文章，Ctrl+Shift+E 批量打包导出',
                'content_en': 'Ctrl+E to export, Ctrl+Shift+E for batch archive export',
                'color': ModernColors.SUCCESS
            },
            {
                'category': '⌨️ 快捷键',
                'category_en': '⌨️ Shortcuts',
                'icon': '📝',
                'title': '复制摘要',
                'title_en': 'Copy Summary',
                'content': '点击摘要框右上角的复制按钮，一键复制摘要内容到剪贴板',
                'content_en': 'Click copy button on summary box to copy content to clipboard',
                'color': ModernColors.INFO
            },
            # 进阶技巧类
            {
                'category': '💡 进阶技巧',
                'category_en': '💡 Pro Tips',
                'icon': '📦',
                'title': '多格式打包',
                'title_en': 'Multi-format Archive',
                'content': '支持 ZIP/7z/RAR 压缩格式，可选择部分文章打包导出',
                'content_en': 'Export as ZIP/7z/RAR, select specific articles to include',
                'color': ModernColors.INFO
            },
            {
                'category': '💡 进阶技巧',
                'category_en': '💡 Pro Tips',
                'icon': '🗃️',
                'title': '智能缓存',
                'title_en': 'Smart Cache',
                'content': '已处理文章自动缓存，重复链接秒速加载，节省流量和时间',
                'content_en': 'Processed articles are cached, duplicates load instantly',
                'color': ModernColors.WARNING
            },
            {
                'category': '💡 进阶技巧',
                'category_en': '💡 Pro Tips',
                'icon': '🌐',
                'title': '多语言支持',
                'title_en': 'Multi-language',
                'content': '在「设置」中切换界面语言，支持简体中文和英语',
                'content_en': 'Switch UI language in Settings, supports Chinese and English',
                'color': ModernColors.GRADIENT_END
            },
            {
                'category': '💡 进阶技巧',
                'category_en': '💡 Pro Tips',
                'icon': '📊',
                'title': '日志查看',
                'title_en': 'View Logs',
                'content': '屏幕底部可展开日志面板，查看详细处理进度和错误信息',
                'content_en': 'Expand log panel at bottom to view detailed progress and errors',
                'color': ModernColors.NEON_CYAN
            },
            # 导出功能类
            {
                'category': '📄 导出功能',
                'category_en': '📄 Export Features',
                'icon': '📝',
                'title': 'Word 导出',
                'title_en': 'Word Export',
                'content': '导出为 .docx 格式，保留文章标题、正文、图片和摘要内容',
                'content_en': 'Export as .docx with title, content, images and summary preserved',
                'color': ModernColors.INFO
            },
            {
                'category': '📄 导出功能',
                'category_en': '📄 Export Features',
                'icon': '📜',
                'title': 'Markdown 导出',
                'title_en': 'Markdown Export',
                'content': '导出为 .md 格式，适合笔记软件或 Git 仓库存档',
                'content_en': 'Export as .md format, ideal for note apps or Git repositories',
                'color': ModernColors.SUCCESS
            },
            {
                'category': '📄 导出功能',
                'category_en': '📄 Export Features',
                'icon': '🌐',
                'title': 'HTML 导出',
                'title_en': 'HTML Export',
                'content': '导出为完整网页格式，保留原文样式和图片，可离线查看',
                'content_en': 'Export as full webpage, preserves styling and images for offline viewing',
                'color': ModernColors.WARNING
            },
            # 效率技巧类
            {
                'category': '⚡ 效率技巧',
                'category_en': '⚡ Efficiency Tips',
                'icon': '⏱️',
                'title': '实时进度',
                'title_en': 'Real-time Progress',
                'content': '批量处理时可查看实时进度、已用时间、预估剩余和处理速率',
                'content_en': 'View real-time progress, elapsed time, ETA and processing speed',
                'color': ModernColors.INFO
            },
            {
                'category': '⚡ 效率技巧',
                'category_en': '⚡ Efficiency Tips',
                'icon': '🚨',
                'title': '任务中断',
                'title_en': 'Stop Processing',
                'content': '批量处理过程中可随时点击「停止」按钮，已处理的文章会保留',
                'content_en': 'Click "Stop" anytime during batch processing, completed articles are kept',
                'color': ModernColors.ERROR
            },
            {
                'category': '⚡ 效率技巧',
                'category_en': '⚡ Efficiency Tips',
                'icon': '🔄',
                'title': '刷新缓存',
                'title_en': 'Refresh Cache',
                'content': '在历史记录页点击「刷新」按钮可重新加载缓存列表',
                'content_en': 'Click "Refresh" in History page to reload cache list',
                'color': ModernColors.SUCCESS
            },
            {
                'category': '⚡ 效率技巧',
                'category_en': '⚡ Efficiency Tips',
                'icon': '🧹',
                'title': '清理缓存',
                'title_en': 'Clear Cache',
                'content': '在历史记录页点击「清空缓存」释放磁盘空间，需谨慎操作',
                'content_en': 'Click "Clear Cache" in History to free disk space, use with caution',
                'color': ModernColors.WARNING
            },
            # 系统设置类
            {
                'category': '⚙️ 系统设置',
                'category_en': '⚙️ System Settings',
                'icon': '🌅',
                'title': '主题切换',
                'title_en': 'Theme Toggle',
                'content': '点击侧边栏底部的月亮/太阳图标切换深色/浅色主题',
                'content_en': 'Click moon/sun icon at sidebar bottom to switch dark/light theme',
                'color': ModernColors.GRADIENT_MID
            },
            {
                'category': '⚙️ 系统设置',
                'category_en': '⚙️ System Settings',
                'icon': '💻',
                'title': '低内存模式',
                'title_en': 'Low Memory Mode',
                'content': '在设置中开启低内存模式，减少动画和日志缓存以节省内存',
                'content_en': 'Enable Low Memory Mode in Settings to reduce animations and cache',
                'color': ModernColors.WARNING
            },
            {
                'category': '⚙️ 系统设置',
                'category_en': '⚙️ System Settings',
                'icon': '📁',
                'title': '默认导出目录',
                'title_en': 'Default Export Path',
                'content': '在设置中配置默认导出目录，不再每次选择保存位置',
                'content_en': 'Set default export directory in Settings to skip folder selection',
                'color': ModernColors.SUCCESS
            },
            {
                'category': '⚙️ 系统设置',
                'category_en': '⚙️ System Settings',
                'icon': '📱',
                'title': '托盘模式',
                'title_en': 'Tray Mode',
                'content': '开启「最小化到托盘」后，关闭窗口时程序会在后台运行',
                'content_en': 'Enable "Minimize to Tray" to keep app running when window is closed',
                'color': ModernColors.NEON_CYAN
            },
            # 摘要技巧类
            {
                'category': '📝 摘要技巧',
                'category_en': '📝 Summary Tips',
                'icon': '🎯',
                'title': '选择摘要方法',
                'title_en': 'Choose Summary Method',
                'content': '简单摘要适合快速概览，AI 摘要适合深度分析和关键观点提取',
                'content_en': 'Simple summary for quick overview, AI summary for deep analysis',
                'color': ModernColors.GRADIENT_MID
            },
            {
                'category': '📝 摘要技巧',
                'category_en': '📝 Summary Tips',
                'icon': '📋',
                'title': '查看关键要点',
                'title_en': 'View Key Points',
                'content': '摘要结果中包含「关键要点」部分，快速了解文章核心内容',
                'content_en': 'Summary includes "Key Points" section for quick core content overview',
                'color': ModernColors.INFO
            },
            {
                'category': '📝 摘要技巧',
                'category_en': '📝 Summary Tips',
                'icon': '⚙️',
                'title': 'Ollama 本地服务',
                'title_en': 'Ollama Local Service',
                'content': '安装 Ollama 后可使用本地 AI 模型，无需云端 API，完全离线工作',
                'content_en': 'Install Ollama to use local AI models, no cloud API needed, fully offline',
                'color': ModernColors.SUCCESS
            },
            # 链接处理类
            {
                'category': '🔗 链接处理',
                'category_en': '🔗 URL Processing',
                'icon': '✅',
                'title': '链接验证',
                'title_en': 'URL Validation',
                'content': '输入链接时会实时验证格式，绿色勾表示有效链接',
                'content_en': 'URLs are validated in real-time, green check means valid link',
                'color': ModernColors.SUCCESS
            },
            {
                'category': '🔗 链接处理',
                'category_en': '🔗 URL Processing',
                'icon': '📋',
                'title': '剪贴板检测',
                'title_en': 'Clipboard Detection',
                'content': '复制微信链接后切换到程序，会自动识别并提示填入',
                'content_en': 'Copy WeChat URL then switch to app, it auto-detects and prompts to paste',
                'color': ModernColors.INFO
            },
            {
                'category': '🔗 链接处理',
                'category_en': '🔗 URL Processing',
                'icon': '📄',
                'title': '支持多种链接',
                'title_en': 'Multiple URL Formats',
                'content': '支持标准微信文章链接和短链接，自动识别并处理',
                'content_en': 'Supports standard WeChat article URLs and short links, auto-detected',
                'color': ModernColors.WARNING
            },
            # 使用建议类
            {
                'category': '💡 使用建议',
                'category_en': '💡 Usage Tips',
                'icon': '📈',
                'title': '先测试单篇',
                'title_en': 'Test Single First',
                'content': '建议先用单篇处理测试效果，确认满意后再批量处理',
                'content_en': 'Test with single article first, then batch process after confirming results',
                'color': ModernColors.INFO
            },
            {
                'category': '💡 使用建议',
                'category_en': '💡 Usage Tips',
                'icon': '📤',
                'title': '导出后核对',
                'title_en': 'Review After Export',
                'content': '导出后建议打开文件核对内容，确保图片和格式正确',
                'content_en': 'Review exported files to ensure images and formatting are correct',
                'color': ModernColors.WARNING
            },
            {
                'category': '💡 使用建议',
                'category_en': '💡 Usage Tips',
                'icon': '🔒',
                'title': 'API 密钥安全',
                'title_en': 'API Key Security',
                'content': 'API 密钥安全存储在本地，不会上传到任何服务器',
                'content_en': 'API keys stored securely on local device, never uploaded to any server',
                'color': ModernColors.SUCCESS
            },
            {
                'category': '💡 使用建议',
                'category_en': '💡 Usage Tips',
                'icon': '💾',
                'title': '定期备份',
                'title_en': 'Regular Backup',
                'content': '重要文章建议导出备份，缓存数据可能会被清理',
                'content_en': 'Export important articles as backup, cache data may be cleared',
                'color': ModernColors.WARNING
            },
            # 常见问题类
            {
                'category': '❓ 常见问题',
                'category_en': '❓ FAQ',
                'icon': '🔍',
                'title': '文章加载失败',
                'title_en': 'Article Load Failed',
                'content': '检查链接是否正确，部分文章可能已删除或需要登录查看',
                'content_en': 'Check if URL is correct, some articles may be deleted or require login',
                'color': ModernColors.WARNING
            },
            {
                'category': '❓ 常见问题',
                'category_en': '❓ FAQ',
                'icon': '🤖',
                'title': 'AI 摘要失败',
                'title_en': 'AI Summary Failed',
                'content': '检查 API 密钥是否正确，或服务是否可用，也可尝试其他摘要方法',
                'content_en': 'Check API key or service availability, try other summary methods',
                'color': ModernColors.ERROR
            },
            {
                'category': '❓ 常见问题',
                'category_en': '❓ FAQ',
                'icon': '📷',
                'title': '图片不显示',
                'title_en': 'Images Not Showing',
                'content': '部分图片可能有防盗链保护，导出时会尝试下载并嵌入',
                'content_en': 'Some images have hotlink protection, export will try to download and embed',
                'color': ModernColors.INFO
            },
        ]
        
        self._current_tip_index = 0
        self._tip_auto_switch_id = None
        
        # 主容器
        tip_card = ctk.CTkFrame(
            parent,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            border_width=1,
            border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER)
        )
        tip_card.pack(fill='x', pady=20)
        
        # 内部容器
        inner = ctk.CTkFrame(tip_card, fg_color='transparent')
        inner.pack(fill='x', padx=20, pady=15)
        
        # 顶部：标题 + 导航按钮
        header = ctk.CTkFrame(inner, fg_color='transparent')
        header.pack(fill='x')
        
        # 分类标签 (动态更新)
        self._tip_category_label = ctk.CTkLabel(
            header,
            text=self._tips_data[0]['category'],
            font=ctk.CTkFont(size=12, weight='bold'),
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT)
        )
        self._tip_category_label.pack(side='left')
        
        # 导航按钮容器
        nav_frame = ctk.CTkFrame(header, fg_color='transparent')
        nav_frame.pack(side='right')
        
        # 上一条按钮
        prev_btn = ctk.CTkButton(
            nav_frame,
            text='‹',
            width=28,
            height=28,
            corner_radius=Spacing.RADIUS_SM,
            fg_color='transparent',
            hover_color=(ModernColors.LIGHT_BG_SECONDARY, ModernColors.DARK_BG_SECONDARY),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
            font=ctk.CTkFont(size=16, weight='bold'),
            command=lambda: self._switch_tip(-1)
        )
        prev_btn.pack(side='left', padx=2)
        
        # 指示器 (如 1/8)
        self._tip_indicator_label = ctk.CTkLabel(
            nav_frame,
            text=f'1/{len(self._tips_data)}',
            font=ctk.CTkFont(size=11),
            text_color=(ModernColors.LIGHT_TEXT_MUTED, ModernColors.DARK_TEXT_MUTED)
        )
        self._tip_indicator_label.pack(side='left', padx=5)
        
        # 下一条按钮
        next_btn = ctk.CTkButton(
            nav_frame,
            text='›',
            width=28,
            height=28,
            corner_radius=Spacing.RADIUS_SM,
            fg_color='transparent',
            hover_color=(ModernColors.LIGHT_BG_SECONDARY, ModernColors.DARK_BG_SECONDARY),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
            font=ctk.CTkFont(size=16, weight='bold'),
            command=lambda: self._switch_tip(1)
        )
        next_btn.pack(side='left', padx=2)
        
        # 内容区域
        content_frame = ctk.CTkFrame(inner, fg_color='transparent')
        content_frame.pack(fill='x', pady=(12, 0))
        
        # 图标 + 标题
        title_row = ctk.CTkFrame(content_frame, fg_color='transparent')
        title_row.pack(fill='x')
        
        self._tip_icon_label = ctk.CTkLabel(
            title_row,
            text=self._tips_data[0]['icon'],
            font=ctk.CTkFont(size=20)
        )
        self._tip_icon_label.pack(side='left')
        
        self._tip_title_label = ctk.CTkLabel(
            title_row,
            text=self._tips_data[0]['title'],
            font=ctk.CTkFont(size=14, weight='bold'),
            text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT)
        )
        self._tip_title_label.pack(side='left', padx=(8, 0))
        
        # 颜色指示条
        self._tip_color_bar = ctk.CTkFrame(
            title_row,
            width=4,
            height=16,
            corner_radius=2,
            fg_color=self._tips_data[0]['color']
        )
        self._tip_color_bar.pack(side='right')
        
        # 内容文本
        self._tip_content_label = ctk.CTkLabel(
            content_frame,
            text=self._tips_data[0]['content'],
            font=ctk.CTkFont(size=12),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
            justify='left',
            anchor='w'
        )
        self._tip_content_label.pack(fill='x', pady=(8, 0))
        
        # 底部：快捷跳转按钮
        actions_frame = ctk.CTkFrame(inner, fg_color='transparent')
        actions_frame.pack(fill='x', pady=(15, 0))
        
        # 快捷按钮: (icon, 中文文本, 英文文本, 页面, 颜色)
        quick_actions = [
            ('📄', '单篇处理', 'Single Article', self.PAGE_SINGLE, ModernColors.INFO),
            ('⚙️', '配置 API', 'Configure API', self.PAGE_SETTINGS, ModernColors.GRADIENT_MID),
            ('📜', '历史记录', 'History', self.PAGE_HISTORY, ModernColors.WARNING),
        ]
        
        is_en = get_i18n().get_language() != 'zh_CN'
        for icon, text_zh, text_en, page, color in quick_actions:
            display_text = f'{icon} {text_en}' if is_en else f'{icon} {text_zh}'
            btn = ctk.CTkButton(
                actions_frame,
                text=display_text,
                font=ctk.CTkFont(size=11),
                height=28,
                corner_radius=Spacing.RADIUS_SM,
                fg_color='transparent',
                hover_color=(ModernColors.LIGHT_BG_SECONDARY, ModernColors.DARK_BG_SECONDARY),
                text_color=color,
                border_width=1,
                border_color=color,
                command=lambda p=page: self._show_page(p)
            )
            btn.pack(side='left', padx=(0, 8))
        
        # 启动自动轮播 (每 8 秒切换)
        self._start_tip_auto_switch()
        
        # 鼠标悬停时暂停轮播
        def on_enter(e):
            self._stop_tip_auto_switch()
            tip_card.configure(
                border_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT)
            )
        
        def on_leave(e):
            self._start_tip_auto_switch()
            tip_card.configure(
                border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER)
            )
        
        tip_card.bind('<Enter>', on_enter)
        tip_card.bind('<Leave>', on_leave)
        for widget in [inner, header, content_frame, actions_frame, title_row]:
            widget.bind('<Enter>', on_enter)
            widget.bind('<Leave>', on_leave)
    
    def _switch_tip(self, direction: int):
        """切换提示
        
        Args:
            direction: 1 下一条, -1 上一条
        """
        self._current_tip_index = (self._current_tip_index + direction) % len(self._tips_data)
        self._update_tip_display()
    
    def _update_tip_display(self):
        """更新提示显示"""
        tip = self._tips_data[self._current_tip_index]
        is_en = get_i18n().get_language() != 'zh_CN'
        
        self._tip_category_label.configure(
            text=tip['category_en'] if is_en else tip['category']
        )
        self._tip_indicator_label.configure(
            text=f'{self._current_tip_index + 1}/{len(self._tips_data)}'
        )
        self._tip_icon_label.configure(text=tip['icon'])
        self._tip_title_label.configure(
            text=tip['title_en'] if is_en else tip['title']
        )
        self._tip_content_label.configure(
            text=tip['content_en'] if is_en else tip['content']
        )
        self._tip_color_bar.configure(fg_color=tip['color'])
    
    def _start_tip_auto_switch(self):
        """启动自动轮播"""
        if self._tip_auto_switch_id:
            return
        
        def auto_switch():
            self._switch_tip(1)
            self._tip_auto_switch_id = self.root.after(8000, auto_switch)
        
        self._tip_auto_switch_id = self.root.after(8000, auto_switch)
    
    def _stop_tip_auto_switch(self):
        """停止自动轮播"""
        if self._tip_auto_switch_id:
            self.root.after_cancel(self._tip_auto_switch_id)
            self._tip_auto_switch_id = None

    def _create_animated_card(self, parent, icon: str, title: str, desc: str, color: str, command=None) -> ctk.CTkFrame:
        """创建带悬停动画的玻璃态卡片 - 2026 UI 趋势"""
        card = ctk.CTkFrame(parent, corner_radius=Spacing.RADIUS_LG, fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD), border_width=1, border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER))
        icon_label = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=42))
        icon_label.pack(pady=(30, 12))
        title_label = ctk.CTkLabel(card, text=title, font=self._get_font(18, 'bold'), text_color=color)
        title_label.pack()
        desc_label = ctk.CTkLabel(card, text=desc, font=self._get_font(12), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY))
        desc_label.pack(pady=(8, 20))
        btn = ctk.CTkButton(card, text='开始使用 →', font=self._get_font(13), corner_radius=Spacing.RADIUS_MD, height=40, fg_color=color, hover_color=self._adjust_color_brightness(color, 1.15), command=command)
        btn.pack(pady=(0, 30), padx=30, fill='x')
        def on_enter(e):
            card.configure(fg_color=(ModernColors.LIGHT_CARD_HOVER, ModernColors.DARK_CARD_HOVER), border_color=(color, color))
            title_label.configure(text_color=self._adjust_color_brightness(color, 1.2))
        def on_leave(e):
            card.configure(fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD), border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER))
            title_label.configure(text_color=color)
        card.bind('<Enter>', on_enter)
        card.bind('<Leave>', on_leave)
        for widget in [icon_label, title_label, desc_label]:
            widget.bind('<Enter>', on_enter)
            widget.bind('<Leave>', on_leave)
        return card
    def _adjust_color_brightness(self, hex_color: str, factor: float) -> str:
        """调整颜色亮度\n        \n        Args:\n            hex_color: 十六进制颜色 (#RRGGBB)\n            factor: 亮度因子 (>1 变亮, <1 变暗)\n        """
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
            return f'#{r:02x}{g:02x}{b:02x}'
        except Exception:
            return hex_color
    def _add_status_indicator(self, parent, label: str, value: str, is_ok: bool):
        """添加状态指示器 - 带悬停动画效果"""
        frame = ctk.CTkFrame(parent, fg_color=('#f8f9fc', '#1e1e2e'), corner_radius=Spacing.RADIUS_MD, border_width=1, border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER))
        frame.pack(side='left', padx=10, pady=5)
        inner_frame = ctk.CTkFrame(frame, fg_color='transparent')
        inner_frame.pack(padx=15, pady=10)
        color = ModernColors.SUCCESS if is_ok else ModernColors.ERROR
        hover_color = self._adjust_color_brightness(color, 1.2) if is_ok else ModernColors.ERROR
        status_label = ctk.CTkLabel(inner_frame, text=f'● {label}', font=ctk.CTkFont(size=12, weight='bold'), text_color=color)
        status_label.pack(anchor='w')
        value_label = ctk.CTkLabel(inner_frame, text=value, font=ctk.CTkFont(size=11), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY))
        value_label.pack(anchor='w')
        def on_enter(e):
            frame.configure(fg_color=(ModernColors.LIGHT_CARD_HOVER, ModernColors.DARK_CARD_HOVER), border_color=(color, color))
            status_label.configure(text_color=hover_color)
        def on_leave(e):
            frame.configure(fg_color=('#f8f9fc', '#1e1e2e'), border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER))
            status_label.configure(text_color=color)
        frame.bind('<Enter>', on_enter)
        frame.bind('<Leave>', on_leave)
        inner_frame.bind('<Enter>', on_enter)
        inner_frame.bind('<Leave>', on_leave)
        status_label.bind('<Enter>', on_enter)
        status_label.bind('<Leave>', on_leave)
        value_label.bind('<Enter>', on_enter)
        value_label.bind('<Leave>', on_leave)
    def _build_single_page(self):
        """构建单篇处理页面"""
        frame = ctk.CTkFrame(self.content_area, fg_color='transparent')
        self._page_frames[self.PAGE_SINGLE] = frame
        header = ctk.CTkFrame(frame, fg_color='transparent')
        header.pack(fill='x', pady=(0, 20))
        ctk.CTkLabel(header, text='📄 单篇文章处理', font=ctk.CTkFont(size=24, weight='bold')).pack(side='left')
        content = ctk.CTkFrame(frame, fg_color='transparent')
        content.pack(fill='both', expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)
        left_card = ctk.CTkFrame(content, corner_radius=Spacing.RADIUS_LG, fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD))
        left_card.grid(row=0, column=0, padx=(0, 10), sticky='nsew')
        ctk.CTkLabel(left_card, text='🔗 文章链接', font=ctk.CTkFont(size=14, weight='bold')).pack(anchor='w', padx=20, pady=(20, 8))
        # 使用现代化输入框组件 (2026 UI)
        self.url_entry = self._create_modern_input(
            left_card,
            placeholder='请输入微信公众号文章链接...',
            show_clear_button=True
        )
        self.url_entry.pack(fill='x', padx=20)
        self.url_status_label = ctk.CTkLabel(left_card, text='', font=ctk.CTkFont(size=11), anchor='w')
        self.url_status_label.pack(fill='x', padx=20, pady=(2, 0))
        self.url_entry.bind('<KeyRelease>', self._on_url_input_change)
        self.url_entry.bind('<FocusOut>', self._on_url_input_change)
        options_frame = ctk.CTkFrame(left_card, fg_color='transparent')
        options_frame.pack(fill='x', padx=20, pady=15)
        ctk.CTkLabel(options_frame, text='摘要方法:', font=ctk.CTkFont(size=13)).pack(side='left')
        available_methods = [name for name, info in self._summarizer_info.items() if info.available]
        if not available_methods:
            available_methods = ['simple']
        self.method_var = ctk.StringVar(value=available_methods[0])
        self.method_menu = ctk.CTkOptionMenu(options_frame, values=available_methods, variable=self.method_var, width=130, height=32, corner_radius=Spacing.RADIUS_MD, font=ctk.CTkFont(size=12))
        self.method_menu.pack(side='left', padx=(10, 20))
        self.summarize_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(options_frame, text='生成摘要', variable=self.summarize_var, font=ctk.CTkFont(size=13), corner_radius=Spacing.RADIUS_SM).pack(side='left')
        btn_frame = ctk.CTkFrame(left_card, fg_color='transparent')
        btn_frame.pack(fill='x', padx=20, pady=10)
        # 使用现代化按钮组件 (2026 UI)
        self.fetch_btn = self._create_modern_button(
            btn_frame, 
            text='🚀 开始处理', 
            command=self._on_fetch,
            variant='primary',
            size='large'
        )
        self.fetch_btn.pack(side='left', expand=True, fill='x', padx=(0, 5))
        self.export_btn = self._create_modern_button(
            btn_frame,
            text='📥 导出',
            command=self._on_export,
            variant='secondary',
            size='large'
        )
        self.export_btn.pack(side='left', expand=True, fill='x', padx=(5, 0))
        self.export_btn.configure(state='disabled')
        ctk.CTkLabel(left_card, text='📄 内容预览', font=ctk.CTkFont(size=14, weight='bold')).pack(anchor='w', padx=20, pady=(15, 8))
        self.preview_text = ctk.CTkTextbox(left_card, corner_radius=Spacing.RADIUS_MD, font=ctk.CTkFont(size=12))
        self.preview_text.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        right_card = ctk.CTkFrame(content, corner_radius=Spacing.RADIUS_LG, fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD))
        right_card.grid(row=0, column=1, padx=(10, 0), sticky='nsew')
        ctk.CTkLabel(right_card, text='📰 文章信息', font=ctk.CTkFont(size=14, weight='bold')).pack(anchor='w', padx=20, pady=(20, 10))
        info_frame = ctk.CTkFrame(right_card, corner_radius=Spacing.RADIUS_MD, fg_color=('#e8e8e8', 'gray20'))
        info_frame.pack(fill='x', padx=20)
        self.title_label = ctk.CTkLabel(info_frame, text='标题: -', font=ctk.CTkFont(size=12), anchor='w')
        self.title_label.pack(fill='x', padx=15, pady=(12, 4))
        self.author_label = ctk.CTkLabel(info_frame, text='公众号: -', font=ctk.CTkFont(size=12), anchor='w')
        self.author_label.pack(fill='x', padx=15, pady=4)
        self.word_count_label = ctk.CTkLabel(info_frame, text='字数: -', font=ctk.CTkFont(size=12), anchor='w')
        self.word_count_label.pack(fill='x', padx=15, pady=(4, 12))
        ctk.CTkLabel(right_card, text='📝 文章摘要', font=ctk.CTkFont(size=14, weight='bold')).pack(anchor='w', padx=20, pady=(20, 8))
        self.summary_text = ctk.CTkTextbox(right_card, height=150, corner_radius=Spacing.RADIUS_MD, font=ctk.CTkFont(size=12))
        self.summary_text.pack(fill='x', padx=20)
        ctk.CTkLabel(right_card, text='📌 关键要点', font=ctk.CTkFont(size=14, weight='bold')).pack(anchor='w', padx=20, pady=(15, 8))
        self.points_text = ctk.CTkTextbox(right_card, corner_radius=Spacing.RADIUS_MD, font=ctk.CTkFont(size=12))
        self.points_text.pack(fill='both', expand=True, padx=20, pady=(0, 20))
    def _build_batch_page(self):
        """构建批量处理页面"""
        frame = ctk.CTkFrame(self.content_area, fg_color='transparent')
        self._page_frames[self.PAGE_BATCH] = frame
        ctk.CTkLabel(frame, text='📚 批量文章处理', font=ctk.CTkFont(size=24, weight='bold')).pack(anchor='w', pady=(0, 20))
        content = ctk.CTkFrame(frame, fg_color='transparent')
        content.pack(fill='both', expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)
        left_card = ctk.CTkFrame(content, corner_radius=Spacing.RADIUS_LG, fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD))
        left_card.grid(row=0, column=0, padx=(0, 10), sticky='nsew')
        ctk.CTkLabel(left_card, text='🔗 URL列表', font=ctk.CTkFont(size=14, weight='bold')).pack(anchor='w', padx=20, pady=(20, 5))
        ctk.CTkLabel(left_card, text='每行输入一个URL，或从文件导入', font=ctk.CTkFont(size=11), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY)).pack(anchor='w', padx=20)
        self.batch_url_text = ctk.CTkTextbox(left_card, corner_radius=Spacing.RADIUS_MD, font=ctk.CTkFont(size=12))
        self.batch_url_text.pack(fill='both', expand=True, padx=20, pady=(10, 5))
        self.batch_url_status_label = ctk.CTkLabel(left_card, text='', font=ctk.CTkFont(size=11), anchor='w')
        self.batch_url_status_label.pack(fill='x', padx=20, pady=(0, 5))
        self.batch_url_text.bind('<KeyRelease>', self._on_batch_url_input_change)
        self.batch_url_text.bind('<FocusOut>', self._on_batch_url_input_change)
        btn_frame = ctk.CTkFrame(left_card, fg_color='transparent')
        btn_frame.pack(fill='x', padx=20, pady=(0, 10))
        # 使用现代化按钮组件 (2026 UI)
        import_btn = self._create_modern_button(btn_frame, text='📂 导入文件', command=self._on_import_urls, variant='ghost', size='small')
        import_btn.pack(side='left', padx=(0, 5))
        paste_btn = self._create_modern_button(btn_frame, text='📋 粘贴', command=self._on_paste_urls, variant='ghost', size='small')
        paste_btn.pack(side='left', padx=5)
        clear_btn = self._create_modern_button(btn_frame, text='🗑️ 清空', command=lambda: self.batch_url_text.delete('1.0', 'end'), variant='ghost', size='small')
        clear_btn.pack(side='left', padx=5)
        options_frame = ctk.CTkFrame(left_card, fg_color='transparent')
        options_frame.pack(fill='x', padx=20, pady=10)
        ctk.CTkLabel(options_frame, text='摘要方法:').pack(side='left')
        available_methods = [name for name, info in self._summarizer_info.items() if info.available]
        if not available_methods:
            available_methods = ['simple']
        self.batch_method_var = ctk.StringVar(value=available_methods[0])
        ctk.CTkOptionMenu(options_frame, values=available_methods, variable=self.batch_method_var, width=100, height=30).pack(side='left', padx=(10, 20))
        ctk.CTkLabel(options_frame, text='并发数:').pack(side='left')
        self.concurrency_var = ctk.StringVar(value='3')
        ctk.CTkEntry(options_frame, textvariable=self.concurrency_var, width=50, height=30).pack(side='left', padx=(10, 0))
        # 使用现代化按钮组件 (2026 UI)
        self.batch_start_btn = self._create_modern_button(
            left_card, 
            text='🚀 开始批量处理', 
            command=self._on_batch_process,
            variant='primary',
            size='large'
        )
        self.batch_start_btn.pack(fill='x', padx=20, pady=(5, 20))
        right_card = ctk.CTkFrame(content, corner_radius=Spacing.RADIUS_LG, fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD))
        right_card.grid(row=0, column=1, padx=(10, 0), sticky='nsew')
        ctk.CTkLabel(right_card, text='📋 处理结果', font=ctk.CTkFont(size=14, weight='bold')).pack(anchor='w', padx=20, pady=(20, 10))
        self.batch_result_frame = ctk.CTkScrollableFrame(right_card, corner_radius=Spacing.RADIUS_MD)
        self.batch_result_frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))
        # 使用现代化进度条组件 (2026 UI)
        self.batch_progress = LinearProgress(
            right_card,
            width=300,
            height=10,
            indeterminate=False,
            theme=self._appearance_mode
        )
        self.batch_progress.pack(fill='x', padx=20, pady=5)
        self.batch_progress.set(0)
        self.batch_status_label = ctk.CTkLabel(right_card, text='就绪', font=ctk.CTkFont(size=12, weight='bold'))
        self.batch_status_label.pack(padx=20, pady=(0, 5))
        progress_detail_frame = ctk.CTkFrame(right_card, fg_color=('#f0f0f0', '#1e1e2e'), corner_radius=Spacing.RADIUS_MD)
        progress_detail_frame.pack(fill='x', padx=20, pady=(0, 10))
        detail_inner = ctk.CTkFrame(progress_detail_frame, fg_color='transparent')
        detail_inner.pack(fill='x', padx=15, pady=10)
        detail_inner.grid_columnconfigure((0, 1, 2, 3), weight=1)
        elapsed_frame = ctk.CTkFrame(detail_inner, fg_color='transparent')
        elapsed_frame.grid(row=0, column=0, sticky='nsew', padx=5)
        ctk.CTkLabel(elapsed_frame, text='⏱️ 已用时间', font=ctk.CTkFont(size=10), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY)).pack()
        self.batch_elapsed_label = ctk.CTkLabel(elapsed_frame, text='00:00', font=ctk.CTkFont(size=14, weight='bold'), text_color=ModernColors.INFO)
        self.batch_elapsed_label.pack()
        eta_frame = ctk.CTkFrame(detail_inner, fg_color='transparent')
        eta_frame.grid(row=0, column=1, sticky='nsew', padx=5)
        ctk.CTkLabel(eta_frame, text='⏳ 预计剩余', font=ctk.CTkFont(size=10), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY)).pack()
        self.batch_eta_label = ctk.CTkLabel(eta_frame, text='--:--', font=ctk.CTkFont(size=14, weight='bold'), text_color=ModernColors.WARNING)
        self.batch_eta_label.pack()
        rate_frame = ctk.CTkFrame(detail_inner, fg_color='transparent')
        rate_frame.grid(row=0, column=2, sticky='nsew', padx=5)
        ctk.CTkLabel(rate_frame, text='🚀 处理速率', font=ctk.CTkFont(size=10), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY)).pack()
        self.batch_rate_label = ctk.CTkLabel(rate_frame, text='0.00 篇/秒', font=ctk.CTkFont(size=14, weight='bold'), text_color=ModernColors.SUCCESS)
        self.batch_rate_label.pack()
        count_frame = ctk.CTkFrame(detail_inner, fg_color='transparent')
        count_frame.grid(row=0, column=3, sticky='nsew', padx=5)
        ctk.CTkLabel(count_frame, text='📊 成功/失败', font=ctk.CTkFont(size=10), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY)).pack()
        self.batch_count_label = ctk.CTkLabel(count_frame, text='0 / 0', font=ctk.CTkFont(size=14, weight='bold'), text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT))
        self.batch_count_label.pack()
        export_label = ctk.CTkLabel(right_card, text='📤 导出选项', font=ctk.CTkFont(size=12, weight='bold'), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY))
        export_label.pack(anchor='w', padx=20, pady=(5, 5))
        # 使用 grid 布局确保所有按钮可见
        export_grid = ctk.CTkFrame(right_card, fg_color='transparent')
        export_grid.pack(fill='x', padx=20, pady=(0, 20))
        export_grid.grid_columnconfigure(0, weight=1)
        export_grid.grid_columnconfigure(1, weight=1)
        self.batch_export_word_btn = ctk.CTkButton(export_grid, text='📄 导出Word', height=38, corner_radius=Spacing.RADIUS_MD, fg_color=ModernColors.INFO, state='disabled', command=lambda: self._on_batch_export_format('word'))
        self.batch_export_word_btn.grid(row=0, column=0, sticky='ew', padx=(0, 3), pady=(0, 5))
        self.batch_export_md_btn = ctk.CTkButton(export_grid, text='📝 导出Markdown', height=38, corner_radius=Spacing.RADIUS_MD, fg_color=ModernColors.SUCCESS, state='disabled', command=lambda: self._on_batch_export_format('markdown'))
        self.batch_export_md_btn.grid(row=0, column=1, sticky='ew', padx=(3, 0), pady=(0, 5))
        self.batch_export_btn = ctk.CTkButton(export_grid, text='📦 压缩打包导出', height=38, corner_radius=Spacing.RADIUS_MD, fg_color=ModernColors.GRADIENT_MID, state='disabled', command=self._on_batch_export)
        self.batch_export_btn.grid(row=1, column=0, sticky='ew', padx=(0, 3), pady=(5, 0))
        self.batch_export_html_btn = ctk.CTkButton(export_grid, text='🌐 导出HTML', height=38, corner_radius=Spacing.RADIUS_MD, fg_color='gray50', state='disabled', command=lambda: self._on_batch_export_format('html'))
        self.batch_export_html_btn.grid(row=1, column=1, sticky='ew', padx=(3, 0), pady=(5, 0))
    def _build_history_page(self):
        """构建历史记录页面"""
        frame = ctk.CTkFrame(self.content_area, fg_color='transparent')
        self._page_frames[self.PAGE_HISTORY] = frame
        header = ctk.CTkFrame(frame, fg_color='transparent')
        header.pack(fill='x', pady=(0, 20))
        ctk.CTkLabel(header, text='📜 历史记录', font=ctk.CTkFont(size=24, weight='bold')).pack(side='left')
        ctk.CTkButton(header, text='🔄 刷新', width=80, height=35, corner_radius=8, fg_color='gray40', command=self._refresh_history).pack(side='right', padx=5)
        ctk.CTkButton(header, text='🗑️ 清空缓存', width=100, height=35, corner_radius=8, fg_color=ModernColors.ERROR, command=self._on_clear_cache).pack(side='right', padx=5)
        self.cache_stats_label = ctk.CTkLabel(header, text='', font=ctk.CTkFont(size=12), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY))
        self.cache_stats_label.pack(side='right', padx=20)
        list_card = ctk.CTkFrame(frame, corner_radius=15, fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD))
        list_card.pack(fill='both', expand=True)
        self.history_frame = ctk.CTkScrollableFrame(list_card, corner_radius=10)
        self.history_frame.pack(fill='both', expand=True, padx=15, pady=15)
        self._refresh_history()
    def _build_settings_page(self):
        """构建设置页面"""
        frame = ctk.CTkFrame(self.content_area, fg_color='transparent')
        self._page_frames[self.PAGE_SETTINGS] = frame
        header = ctk.CTkFrame(frame, fg_color='transparent')
        header.pack(fill='x', pady=(0, 20))
        ctk.CTkLabel(header, text='⚙️ 设置', font=ctk.CTkFont(size=24, weight='bold')).pack(side='left')
        settings_scroll = ctk.CTkScrollableFrame(frame, corner_radius=15, fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD))
        settings_scroll.pack(fill='both', expand=True)
        settings_card = settings_scroll
        summarizer_section = ctk.CTkFrame(settings_card, fg_color='transparent')
        summarizer_section.pack(fill='x', padx=30, pady=(20, 10))
        ctk.CTkLabel(summarizer_section, text='🤖 摘要服务状态', font=ctk.CTkFont(size=18, weight='bold'), text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT)).pack(anchor='w', pady=(0, 15))
        self.summarizer_status_frame = ctk.CTkFrame(summarizer_section, corner_radius=10, fg_color=('#e8e8e8', 'gray25'))
        self.summarizer_status_frame.pack(fill='x', pady=5)
        self._update_summarizer_status_display()
        ctk.CTkFrame(settings_card, height=2, fg_color=('#d0d0d0', 'gray40')).pack(fill='x', padx=30, pady=15)
        api_section = ctk.CTkFrame(settings_card, fg_color='transparent')
        api_section.pack(fill='x', padx=30, pady=10)
        ctk.CTkLabel(api_section, text='🔑 API 密钥配置', font=ctk.CTkFont(size=18, weight='bold'), text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT)).pack(anchor='w', pady=(0, 5))
        ctk.CTkLabel(api_section, text='配置 API 密钥后可使用对应的AI摘要服务，密钥将安全地保存在本地', font=ctk.CTkFont(size=12), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY)).pack(anchor='w', pady=(0, 15))
        self._api_key_entries = {}
        openai_frame = ctk.CTkFrame(api_section, fg_color='transparent')
        openai_frame.pack(fill='x', pady=8)
        ctk.CTkLabel(openai_frame, text='OpenAI:', font=ctk.CTkFont(size=14), width=100, anchor='w').pack(side='left')
        self._api_key_entries['openai'] = ctk.CTkEntry(openai_frame, placeholder_text='sk-... (用于GPT-4等模型)', height=38, corner_radius=8, font=ctk.CTkFont(size=12), show='•')
        self._api_key_entries['openai'].pack(side='left', fill='x', expand=True, padx=(0, 10))
        saved_openai_key = self.user_prefs.get_api_key('openai')
        if saved_openai_key:
            self._api_key_entries['openai'].insert(0, saved_openai_key)
        self._openai_show_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(openai_frame, text='显示', variable=self._openai_show_var, width=60, font=ctk.CTkFont(size=11), command=lambda: self._toggle_key_visibility('openai')).pack(side='left')
        # DeepSeek API 配置
        deepseek_frame = ctk.CTkFrame(api_section, fg_color='transparent')
        deepseek_frame.pack(fill='x', pady=8)
        ctk.CTkLabel(deepseek_frame, text='DeepSeek:', font=ctk.CTkFont(size=14), width=100, anchor='w').pack(side='left')
        self._api_key_entries['deepseek'] = ctk.CTkEntry(deepseek_frame, placeholder_text='sk-... (国产高性能模型，推荐)', height=38, corner_radius=8, font=ctk.CTkFont(size=12), show='•')
        self._api_key_entries['deepseek'].pack(side='left', fill='x', expand=True, padx=(0, 10))
        saved_deepseek_key = self.user_prefs.get_api_key('deepseek')
        if saved_deepseek_key:
            self._api_key_entries['deepseek'].insert(0, saved_deepseek_key)
        self._deepseek_show_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(deepseek_frame, text='显示', variable=self._deepseek_show_var, width=60, font=ctk.CTkFont(size=11), command=lambda: self._toggle_key_visibility('deepseek')).pack(side='left')
        anthropic_frame = ctk.CTkFrame(api_section, fg_color='transparent')
        anthropic_frame.pack(fill='x', pady=8)
        ctk.CTkLabel(anthropic_frame, text='Anthropic:', font=ctk.CTkFont(size=14), width=100, anchor='w').pack(side='left')
        self._api_key_entries['anthropic'] = ctk.CTkEntry(anthropic_frame, placeholder_text='sk-ant-... (用于Claude模型)', height=38, corner_radius=8, font=ctk.CTkFont(size=12), show='•')
        self._api_key_entries['anthropic'].pack(side='left', fill='x', expand=True, padx=(0, 10))
        saved_anthropic_key = self.user_prefs.get_api_key('anthropic')
        if saved_anthropic_key:
            self._api_key_entries['anthropic'].insert(0, saved_anthropic_key)
        self._anthropic_show_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(anthropic_frame, text='显示', variable=self._anthropic_show_var, width=60, font=ctk.CTkFont(size=11), command=lambda: self._toggle_key_visibility('anthropic')).pack(side='left')
        zhipu_frame = ctk.CTkFrame(api_section, fg_color='transparent')
        zhipu_frame.pack(fill='x', pady=8)
        ctk.CTkLabel(zhipu_frame, text='智谱AI:', font=ctk.CTkFont(size=14), width=100, anchor='w').pack(side='left')
        self._api_key_entries['zhipu'] = ctk.CTkEntry(zhipu_frame, placeholder_text='智谱AI API Key (用于GLM模型)', height=38, corner_radius=8, font=ctk.CTkFont(size=12), show='•')
        self._api_key_entries['zhipu'].pack(side='left', fill='x', expand=True, padx=(0, 10))
        saved_zhipu_key = self.user_prefs.get_api_key('zhipu')
        if saved_zhipu_key:
            self._api_key_entries['zhipu'].insert(0, saved_zhipu_key)
        self._zhipu_show_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(zhipu_frame, text='显示', variable=self._zhipu_show_var, width=60, font=ctk.CTkFont(size=11), command=lambda: self._toggle_key_visibility('zhipu')).pack(side='left')
        api_btn_frame = ctk.CTkFrame(api_section, fg_color='transparent')
        api_btn_frame.pack(fill='x', pady=(15, 5))
        ctk.CTkButton(api_btn_frame, text='💾 保存 API 密钥', width=150, height=38, corner_radius=8, fg_color=ModernColors.SUCCESS, command=self._save_api_keys).pack(side='left', padx=(0, 10))
        ctk.CTkButton(api_btn_frame, text='🗑️ 清除所有密钥', width=150, height=38, corner_radius=8, fg_color='gray40', hover_color=ModernColors.ERROR, command=self._clear_api_keys).pack(side='left')
        self.api_status_label = ctk.CTkLabel(api_btn_frame, text='', font=ctk.CTkFont(size=12), text_color=ModernColors.SUCCESS)
        self.api_status_label.pack(side='left', padx=20)
        ctk.CTkFrame(settings_card, height=2, fg_color=('#d0d0d0', 'gray40')).pack(fill='x', padx=30, pady=15)
        export_section = ctk.CTkFrame(settings_card, fg_color='transparent')
        export_section.pack(fill='x', padx=30, pady=10)
        ctk.CTkLabel(export_section, text='📁 导出设置', font=ctk.CTkFont(size=18, weight='bold'), text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT)).pack(anchor='w', pady=(0, 15))
        export_dir_frame = ctk.CTkFrame(export_section, fg_color='transparent')
        export_dir_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(export_dir_frame, text='默认导出目录:', font=ctk.CTkFont(size=14), width=140, anchor='w').pack(side='left')
        self.export_dir_entry = ctk.CTkEntry(export_dir_frame, placeholder_text='留空则每次手动选择...', height=40, corner_radius=8, font=ctk.CTkFont(size=13))
        self.export_dir_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        saved_dir = self.user_prefs.export_dir
        if saved_dir:
            self.export_dir_entry.insert(0, saved_dir)
        ctk.CTkButton(export_dir_frame, text='📂 浏览', width=80, height=40, corner_radius=8, fg_color=ModernColors.INFO, command=self._browse_export_dir).pack(side='left')
        remember_frame = ctk.CTkFrame(export_section, fg_color='transparent')
        remember_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(remember_frame, text='记住上次导出目录:', font=ctk.CTkFont(size=14), width=140, anchor='w').pack(side='left')
        self.remember_dir_var = ctk.BooleanVar(value=self.user_prefs.remember_export_dir)
        self.remember_dir_switch = ctk.CTkSwitch(remember_frame, text='启用后，导出时将自动打开上次使用的目录', variable=self.remember_dir_var, font=ctk.CTkFont(size=12), command=self._on_remember_dir_change)
        self.remember_dir_switch.pack(side='left')
        format_frame = ctk.CTkFrame(export_section, fg_color='transparent')
        format_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(format_frame, text='默认导出格式:', font=ctk.CTkFont(size=14), width=140, anchor='w').pack(side='left')
        self.default_format_var = ctk.StringVar(value=self.user_prefs.default_export_format)
        format_menu = ctk.CTkSegmentedButton(format_frame, values=['word', 'html', 'markdown'], variable=self.default_format_var, command=self._on_default_format_change, font=ctk.CTkFont(size=12))
        format_menu.pack(side='left')
        ctk.CTkFrame(settings_card, height=2, fg_color=('#d0d0d0', 'gray40')).pack(fill='x', padx=30, pady=15)
        system_section = ctk.CTkFrame(settings_card, fg_color='transparent')
        system_section.pack(fill='x', padx=30, pady=10)
        ctk.CTkLabel(system_section, text='⚙️ 系统设置', font=ctk.CTkFont(size=18, weight='bold'), text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT)).pack(anchor='w', pady=(0, 15))
        autostart_frame = ctk.CTkFrame(system_section, fg_color='transparent')
        autostart_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(autostart_frame, text='开机自启动:', font=ctk.CTkFont(size=14), width=140, anchor='w').pack(side='left')
        self.autostart_var = ctk.BooleanVar(value=self.user_prefs.auto_start_enabled)
        self.autostart_switch = ctk.CTkSwitch(autostart_frame, text='系统启动时自动运行本程序', variable=self.autostart_var, font=ctk.CTkFont(size=12), command=self._on_autostart_change)
        self.autostart_switch.pack(side='left')
        minimize_frame = ctk.CTkFrame(system_section, fg_color='transparent')
        minimize_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(minimize_frame, text='最小化到托盘:', font=ctk.CTkFont(size=14), width=140, anchor='w').pack(side='left')
        self.minimize_tray_var = ctk.BooleanVar(value=self.user_prefs.minimize_to_tray)
        self.minimize_tray_switch = ctk.CTkSwitch(minimize_frame, text='关闭窗口时最小化到系统托盘而不是退出', variable=self.minimize_tray_var, font=ctk.CTkFont(size=12), command=self._on_minimize_tray_change)
        self.minimize_tray_switch.pack(side='left')
        system_hint = ctk.CTkLabel(system_section, text='💡 提示：开启开机自启动后，程序将在后台静默运行', font=ctk.CTkFont(size=11), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY))
        system_hint.pack(anchor='w', pady=(5, 0))
        ctk.CTkFrame(settings_card, height=2, fg_color=('#d0d0d0', 'gray40')).pack(fill='x', padx=30, pady=15)
        # 性能设置部分
        perf_section = ctk.CTkFrame(settings_card, fg_color='transparent')
        perf_section.pack(fill='x', padx=30, pady=10)
        ctk.CTkLabel(perf_section, text='🚀 性能设置', font=ctk.CTkFont(size=18, weight='bold'), text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT)).pack(anchor='w', pady=(0, 15))
        # 内存状态显示
        memory_status_frame = ctk.CTkFrame(perf_section, fg_color='transparent')
        memory_status_frame.pack(fill='x', pady=5)
        ctk.CTkLabel(memory_status_frame, text='当前可用内存:', font=ctk.CTkFont(size=14), width=140, anchor='w').pack(side='left')
        available_mem = get_available_memory_gb()
        if available_mem is not None:
            mem_color = ModernColors.SUCCESS if available_mem >= LOW_MEMORY_THRESHOLD_GB else ModernColors.WARNING
            mem_text = f'{available_mem:.1f} GB'
            if available_mem < LOW_MEMORY_THRESHOLD_GB:
                mem_text += f' (低于 {LOW_MEMORY_THRESHOLD_GB:.0f} GB 阈值)'
        else:
            mem_color = ModernColors.LIGHT_TEXT_SECONDARY
            mem_text = '无法检测 (psutil 未安装)'
        self.memory_status_label = ctk.CTkLabel(memory_status_frame, text=mem_text, font=ctk.CTkFont(size=14, weight='bold'), text_color=mem_color)
        self.memory_status_label.pack(side='left')
        # 低内存模式开关
        low_memory_frame = ctk.CTkFrame(perf_section, fg_color='transparent')
        low_memory_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(low_memory_frame, text='低内存模式:', font=ctk.CTkFont(size=14), width=140, anchor='w').pack(side='left')
        self.low_memory_var = ctk.BooleanVar(value=self.user_prefs.low_memory_mode)
        self.low_memory_switch = ctk.CTkSwitch(low_memory_frame, text='减少内存占用（禁用部分动画、限制日志缓存）', variable=self.low_memory_var, font=ctk.CTkFont(size=12), command=self._on_low_memory_change)
        self.low_memory_switch.pack(side='left')
        perf_hint = ctk.CTkLabel(perf_section, text='💡 提示：当系统可用内存低于 4GB 时，建议开启低内存模式以获得更流畅的体验', font=ctk.CTkFont(size=11), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY))
        perf_hint.pack(anchor='w', pady=(5, 0))
        ctk.CTkFrame(settings_card, height=2, fg_color=('#d0d0d0', 'gray40')).pack(fill='x', padx=30, pady=15)
        # 语言设置部分
        lang_section = ctk.CTkFrame(settings_card, fg_color='transparent')
        lang_section.pack(fill='x', padx=30, pady=10)
        ctk.CTkLabel(lang_section, text='🌐 语言设置', font=ctk.CTkFont(size=18, weight='bold'), text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT)).pack(anchor='w', pady=(0, 15))
        lang_frame = ctk.CTkFrame(lang_section, fg_color='transparent')
        lang_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(lang_frame, text='界面语言:', font=ctk.CTkFont(size=14), width=140, anchor='w').pack(side='left')
        # 语言选择下拉框
        lang_values = ['跟随系统', '简体中文', 'English']
        lang_code_map = {'跟随系统': 'auto', '简体中文': 'zh_CN', 'English': 'en'}
        lang_display_map = {'auto': '跟随系统', 'zh_CN': '简体中文', 'en': 'English'}
        current_lang = self.user_prefs.language
        current_display = lang_display_map.get(current_lang, '跟随系统')
        self.language_var = ctk.StringVar(value=current_display)
        self.language_menu = ctk.CTkOptionMenu(
            lang_frame,
            values=lang_values,
            variable=self.language_var,
            width=180,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            command=lambda v: self._on_language_change(v, lang_code_map)
        )
        self.language_menu.pack(side='left')
        lang_hint = ctk.CTkLabel(lang_section, text='💡 提示：切换语言后需要重启应用才能完全生效', font=ctk.CTkFont(size=11), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY))
        lang_hint.pack(anchor='w', pady=(5, 0))
        ctk.CTkFrame(settings_card, height=2, fg_color=('#d0d0d0', 'gray40')).pack(fill='x', padx=30, pady=15)
        quick_section = ctk.CTkFrame(settings_card, fg_color='transparent')
        quick_section.pack(fill='x', padx=30, pady=10)
        ctk.CTkLabel(quick_section, text='📂 快捷操作', font=ctk.CTkFont(size=18, weight='bold'), text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT)).pack(anchor='w', pady=(0, 15))
        quick_btn_frame = ctk.CTkFrame(quick_section, fg_color='transparent')
        quick_btn_frame.pack(fill='x')
        ctk.CTkButton(quick_btn_frame, text='📁 打开导出目录', width=150, height=40, corner_radius=8, fg_color=ModernColors.SUCCESS, command=self._open_export_dir).pack(side='left', padx=(0, 10))
        ctk.CTkButton(quick_btn_frame, text='🗑️ 清空设置', width=150, height=40, corner_radius=8, fg_color='gray40', command=self._reset_export_settings).pack(side='left', padx=(0, 10))
        ctk.CTkButton(quick_btn_frame, text='🔄 刷新服务状态', width=150, height=40, corner_radius=8, fg_color='gray40', command=self._refresh_availability).pack(side='left')
        save_frame = ctk.CTkFrame(settings_card, fg_color='transparent')
        save_frame.pack(fill='x', padx=30, pady=20)
        ctk.CTkButton(save_frame, text='✔️ 保存设置', width=150, height=45, corner_radius=10, font=ctk.CTkFont(size=14, weight='bold'), fg_color=ModernColors.SUCCESS, command=self._save_settings).pack(side='right')
        info_frame = ctk.CTkFrame(settings_card, fg_color='transparent')
        info_frame.pack(fill='x', padx=30, pady=(0, 20))
        self.settings_status_label = ctk.CTkLabel(info_frame, text='', font=ctk.CTkFont(size=12), text_color=ModernColors.SUCCESS)
        self.settings_status_label.pack(anchor='w')
    def _browse_export_dir(self):
        """浏览选择导出目录"""
        current_dir = self.export_dir_entry.get().strip()
        initial_dir = current_dir if current_dir and Path(current_dir).exists() else str(Path.home())
        dir_path = filedialog.askdirectory(title='选择默认导出目录', initialdir=initial_dir)
        if dir_path:
            self.export_dir_entry.delete(0, 'end')
            self.export_dir_entry.insert(0, dir_path)
            logger.info(f'已选择导出目录: {dir_path}')
    def _on_remember_dir_change(self):
        """记住目录选项变更"""
        self.user_prefs.remember_export_dir = self.remember_dir_var.get()
        logger.info(f"记住导出目录: {('启用' if self.remember_dir_var.get() else '禁用')}")
    def _on_default_format_change(self, value: str):
        """默认格式变更"""
        self.user_prefs.default_export_format = value
        logger.info(f'默认导出格式: {value}')
    def _on_autostart_change(self):
        """开机自启动设置变更"""
        enabled = self.autostart_var.get()
        self.user_prefs.auto_start_enabled = enabled
        startup_folder = Path.home() / 'AppData' / 'Roaming' / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
        shortcut_path = startup_folder / '微信文章总结器.lnk'
        project_root = Path(__file__).parent.parent.parent.parent.parent
        vbs_path = project_root / 'start_silent.vbs'
        if enabled:
            try:
                import subprocess
                ps_script = f'\n$WshShell = New-Object -ComObject WScript.Shell\n$Shortcut = $WshShell.CreateShortcut(\"{shortcut_path}\")\n$Shortcut.TargetPath = \"{vbs_path}\"\n$Shortcut.WorkingDirectory = \"{project_root}\"\n$Shortcut.Description = \"微信文章总结器 - 开机自启动\"\n$Shortcut.Save()\n'
                result = subprocess.run(['powershell', '-Command', ps_script], capture_output=True, text=True)
                if result.returncode == 0:
                    self.settings_status_label.configure(text='✓ 已启用开机自启动', text_color=ModernColors.SUCCESS)
                    logger.success('已启用开机自启动')
                else:
                    raise Exception(result.stderr)
            except Exception as e:
                self.autostart_var.set(False)
                self.user_prefs.auto_start_enabled = False
                messagebox.showerror('错误', f'创建开机启动项失败: {e}')
                logger.error(f'创建开机启动项失败: {e}')
                return None
        else:
            try:
                if shortcut_path.exists():
                    shortcut_path.unlink()
                self.settings_status_label.configure(text='✓ 已禁用开机自启动', text_color=ModernColors.SUCCESS)
                logger.info('已禁用开机自启动')
            except Exception as e:
                self.autostart_var.set(True)
                self.user_prefs.auto_start_enabled = True
                messagebox.showerror('错误', f'删除开机启动项失败: {e}')
                logger.error(f'删除开机启动项失败: {e}')
    def _on_minimize_tray_change(self):
        """最小化到托盘设置变更"""
        enabled = self.minimize_tray_var.get()
        self.user_prefs.minimize_to_tray = enabled
        if enabled:
            self.settings_status_label.configure(text='✓ 已启用最小化到托盘', text_color=ModernColors.SUCCESS)
            logger.info('已启用最小化到系统托盘')
        else:
            self.settings_status_label.configure(text='✓ 已禁用最小化到托盘', text_color=ModernColors.SUCCESS)
            logger.info('已禁用最小化到系统托盘')
        # 注意：不再直接设置 protocol，统一由 _on_window_close 处理
    def _on_low_memory_change(self):
        """低内存模式设置变更"""
        enabled = self.low_memory_var.get()
        self.user_prefs.low_memory_mode = enabled
        self.user_prefs.low_memory_prompt_dismissed = False  # 重置提示状态
        if enabled:
            self._apply_low_memory_optimizations()
            self.settings_status_label.configure(text='✓ 已启用低内存模式', text_color=ModernColors.SUCCESS)
            logger.info('已启用低内存模式')
        else:
            self.settings_status_label.configure(text='✓ 已禁用低内存模式', text_color=ModernColors.SUCCESS)
            logger.info('已禁用低内存模式，重启后完全生效')
    def _on_language_change(self, display_value: str, lang_code_map: dict):
        """界面语言设置变更"""
        lang_code = lang_code_map.get(display_value, 'auto')
        self.user_prefs.language = lang_code
        set_language(lang_code)
        self.settings_status_label.configure(text=f'✓ 语言已设置为: {display_value}', text_color=ModernColors.SUCCESS)
        logger.info(f'界面语言已切换: {lang_code}')
        # 显示重启提示 - 使用新ToastManager (2026 UI组件)
        if hasattr(self, '_toast_manager') and self._toast_manager:
            self._toast_manager.info(f'语言已设置为 {display_value}，重启应用后完全生效')
        else:
            ToastNotification(
                self.root,
                '🌐 语言已切换',
                f'语言已设置为 {display_value}\n重启应用后完全生效',
                toast_type='info',
                duration_ms=3000
            )
    def _on_window_close(self):
        """窗口关闭事件处理器 - 统一处理退出逻辑
        
        处理以下场景：
        1. 有正在运行的任务 -> 显示确认对话框
        2. 无任务 + 已启用托盘 -> 最小化到托盘
        3. 无任务 + 未启用托盘 -> 直接退出
        """
        # 检查是否有正在运行的任务
        active_task = self._get_active_task_info()
        
        if active_task:
            # 有任务正在运行，显示确认对话框
            dialog = ExitConfirmDialog(
                self.root,
                title='任务正在进行中',
                message='当前有任务正在运行，确定要退出吗？',
                task_info=active_task,
                icon='warning'
            )
            
            result = dialog.get()
            
            if result == 'exit':
                # 用户选择强制退出
                logger.warning(f'用户强制退出，中断任务: {active_task}')
                self._force_exit()
            elif result == 'minimize':
                # 用户选择最小化到后台
                logger.info('用户选择后台运行')
                self._on_close_to_tray()
            else:
                # 用户取消，继续任务
                logger.debug('用户取消退出，继续任务')
        else:
            # 没有任务运行
            if self.user_prefs.minimize_to_tray:
                # 最小化到托盘
                self._on_close_to_tray()
            else:
                # 直接退出
                self._safe_exit()
    
    def _get_active_task_info(self) -> Optional[str]:
        """获取当前运行中的任务信息
        
        Returns:
            任务描述字符串，如果没有任务则返回 None
        """
        tasks = []
        
        # 检查批量处理状态
        if self._batch_processing_active:
            if hasattr(self, '_batch_progress_tracker') and self._batch_progress_tracker:
                tracker = self._batch_progress_tracker
                tasks.append(f'批量处理 ({tracker.current}/{tracker.total} 篇)')
            else:
                tasks.append('批量处理中')
        
        # 检查批量导出状态
        if self._batch_export_active:
            if hasattr(self, '_export_progress_tracker') and self._export_progress_tracker:
                tracker = self._export_progress_tracker
                tasks.append(f'批量导出 ({tracker.current}/{tracker.total} 篇)')
            elif hasattr(self, '_zip_progress_tracker') and self._zip_progress_tracker:
                tracker = self._zip_progress_tracker
                tasks.append(f'ZIP打包 ({tracker.current}/{tracker.total} 篇)')
            else:
                tasks.append('批量导出中')
        
        # 检查单篇处理状态
        if self._single_processing_active:
            tasks.append('单篇文章处理中')
        
        if tasks:
            return ' | '.join(tasks)
        return None
    
    def _force_exit(self):
        """强制退出应用（不等待任务完成）"""
        try:
            # 释放日志资源
            if self._log_handler_id:
                try:
                    logger.remove(self._log_handler_id)
                except Exception:
                    pass
            
            # 关闭窗口
            self.root.destroy()
        except Exception as e:
            logger.error(f'强制退出时出错: {e}')
            self.root.destroy()
    
    def _safe_exit(self):
        """安全退出应用（无任务运行时的正常退出）"""
        try:
            # 释放日志资源
            if self._log_handler_id:
                try:
                    logger.remove(self._log_handler_id)
                except Exception:
                    pass
            
            logger.info('应用正常退出')
            self.root.destroy()
        except Exception as e:
            logger.error(f'安全退出时出错: {e}')
            self.root.destroy()
    
    def _on_close_to_tray(self):
        """关闭窗口时最小化到托盘"""
        self.root.withdraw()
        logger.info('窗口已最小化到系统托盘')
        # 使用新ToastManager (2026 UI组件)
        try:
            if hasattr(self, '_toast_manager') and self._toast_manager:
                self._toast_manager.info('程序正在后台运行，双击托盘图标可恢复窗口')
            else:
                ToastNotification(self.root, '程序已最小化', '程序正在后台运行\n双击托盘图标可恢复窗口', 'info', duration_ms=3000)
        except Exception:
            return None
    def _restore_from_tray(self):
        """从托盘恢复窗口"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    def _open_export_dir(self):
        """打开导出目录"""
        export_dir = self.export_dir_entry.get().strip() or self.user_prefs.export_dir
        if not export_dir:
            export_dir = self.settings.export.default_output_dir
        if export_dir:
            path = Path(export_dir)
            if path.exists():
                import os
                os.startfile(str(path))
                logger.info(f'已打开目录: {path}')
            else:
                messagebox.showwarning('提示', f'目录不存在: {export_dir}')
        else:
            messagebox.showinfo('提示', '请先设置导出目录')
    def _reset_export_settings(self):
        """重置导出设置"""
        if not messagebox.askyesno('确认', '确定要重置所有导出设置吗？'):
            return None
        else:
            self.export_dir_entry.delete(0, 'end')
            self.remember_dir_var.set(True)
            self.default_format_var.set('word')
            self.user_prefs.export_dir = ''
            self.user_prefs.remember_export_dir = True
            self.user_prefs.default_export_format = 'word'
            self.settings_status_label.configure(text='✓ 设置已重置', text_color=ModernColors.SUCCESS)
            logger.info('导出设置已重置')
    def _save_settings(self):
        """保存设置"""
        export_dir = self.export_dir_entry.get().strip()
        if export_dir and (not Path(export_dir).exists()):
                if messagebox.askyesno('确认', f'目录不存在\n{export_dir}\n\n是否创建？'):
                    try:
                        Path(export_dir).mkdir(parents=True, exist_ok=True)
                        logger.info(f'已创建目录: {export_dir}')
                    except Exception as e:
                        messagebox.showerror('错误', f'创建目录失败: {e}')
                        return None
                else:
                    return None
        self.user_prefs.export_dir = export_dir
        self.user_prefs.remember_export_dir = self.remember_dir_var.get()
        self.user_prefs.default_export_format = self.default_format_var.get()
        self.settings_status_label.configure(text='✓ 设置已保存', text_color=ModernColors.SUCCESS)
        self._set_status('设置已保存', ModernColors.SUCCESS)
        logger.success('设置已保存')
    def _update_summarizer_status_display(self):
        """更新摘要器状态显示"""
        for widget in self.summarizer_status_frame.winfo_children():
            widget.destroy()
        for name, info in self._summarizer_info.items():
            row_frame = ctk.CTkFrame(self.summarizer_status_frame, fg_color='transparent')
            row_frame.pack(fill='x', padx=15, pady=4)
            icon = '✓' if info.available else '✗'
            color = ModernColors.SUCCESS if info.available else ModernColors.ERROR
            display_names = {'simple': '简单摘要', 'textrank': 'TextRank', 'ollama': 'Ollama', 'openai': 'OpenAI', 'deepseek': 'DeepSeek', 'anthropic': 'Anthropic', 'zhipu': '智谱AI'}
            display_name = display_names.get(name, name)
            ctk.CTkLabel(row_frame, text=f'{icon} {display_name}', font=ctk.CTkFont(size=13, weight='bold' if info.available else 'normal'), text_color=color, width=120, anchor='w').pack(side='left')
            ctk.CTkLabel(row_frame, text=info.reason, font=ctk.CTkFont(size=11), text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY), anchor='w').pack(side='left', padx=(10, 0))
    def _toggle_key_visibility(self, provider: str):
        """切换API密钥可见性"""
        entry = self._api_key_entries.get(provider)
        if not entry:
            return None
        else:
            show_var = getattr(self, f'_{provider}_show_var', None)
            if show_var and show_var.get():
                entry.configure(show='')
            else:
                entry.configure(show='•')
    def _save_api_keys(self):
        """保存API密钥"""
        saved_count = 0
        api_keys = {}
        for provider, entry in self._api_key_entries.items():
            key = entry.get().strip()
            self.user_prefs.set_api_key(provider, key)
            if key:
                saved_count += 1
                api_keys[provider] = key
        # 重新加载 Container 的摘要器，使新密钥生效
        container = get_container()
        container.reload_summarizers(api_keys)
        self._summarizer_info = self._get_summarizer_info()
        self._update_summarizer_status_display()
        self._refresh_summarizer_menus()
        if saved_count > 0:
            self.api_status_label.configure(text=f'✓ 已保存 {saved_count} 个 API 密钥', text_color=ModernColors.SUCCESS)
            logger.success(f'已保存 {saved_count} 个 API 密钥')
        else:
            self.api_status_label.configure(text='✓ 密钥已清除', text_color=ModernColors.WARNING)
            logger.info('API 密钥已清除')
        self._set_status('API密钥已更新', ModernColors.SUCCESS)
    def _clear_api_keys(self):
        """清除所有API密钥"""
        if not messagebox.askyesno('确认', '确定要清除所有API密钥吗？'):
            return None
        else:
            for provider, entry in self._api_key_entries.items():
                entry.delete(0, 'end')
                self.user_prefs.set_api_key(provider, '')
            self._summarizer_info = self._get_summarizer_info()
            self._update_summarizer_status_display()
            self._refresh_summarizer_menus()
            self.api_status_label.configure(text='✓ 所有密钥已清除', text_color=ModernColors.WARNING)
            logger.info('所有 API 密钥已清除')
    def _refresh_summarizer_menus(self):
        """刷新摘要方法下拉菜单"""
        available_methods = [name for name, info in self._summarizer_info.items() if info.available]
        if not available_methods:
            available_methods = ['simple']
        if hasattr(self, 'method_menu'):
            self.method_menu.configure(values=available_methods)
            if self.method_var.get() not in available_methods:
                self.method_var.set(available_methods[0])
        if hasattr(self, 'batch_method_var'):
            if self.batch_method_var.get() not in available_methods:
                self.batch_method_var.set(available_methods[0])
    def _build_log_panel(self):
        """构建日志面板"""
        self.log_panel = ctk.CTkFrame(self.main_container, corner_radius=Spacing.RADIUS_LG, fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD))
        self.log_panel.grid(row=1, column=0, sticky='ew', padx=20, pady=(0, 15))
        header = ctk.CTkFrame(self.log_panel, fg_color='transparent')
        header.pack(fill='x', padx=15, pady=(10, 5))
        self.log_toggle_btn = ctk.CTkButton(header, text='📋 日志 ▼', font=self._get_font(12), width=80, height=25, fg_color='transparent', hover_color=('gray80', 'gray30'), text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT), command=self._toggle_log_panel_animated)
        self.log_toggle_btn.pack(side='left')
        ctk.CTkButton(header, text='清空', font=self._get_font(11), width=50, height=25, fg_color='transparent', hover_color=('gray80', 'gray30'), command=self._clear_log).pack(side='left', padx=5)
        ctk.CTkButton(header, text='复制', font=self._get_font(11), width=50, height=25, fg_color='transparent', hover_color=('gray80', 'gray30'), command=self._copy_log).pack(side='left')
        self.log_text = ctk.CTkTextbox(self.log_panel, height=120, corner_radius=Spacing.RADIUS_MD, font=('Consolas', 11), state='disabled')
        self.log_text.pack(fill='x', padx=15, pady=(0, 10))
        self._log_expanded = True
    def _show_page(self, page_id: str):
        """切换页面"""
        for frame in self._page_frames.values():
            frame.grid_forget()
        if page_id in self._page_frames:
            self._page_frames[page_id].grid(row=0, column=0, sticky='nsew')
        for pid, btn in self._nav_buttons.items():
            if pid == page_id:
                btn.configure(fg_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT), text_color='white')
            else:
                btn.configure(fg_color='transparent', text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT))
        self._current_page = page_id
    def _show_page_animated(self, page_id: str):
        """带平滑滑动动画的页面切换"""
        if self._current_page == page_id:
            return None
        
        old_page = self._page_frames.get(self._current_page)
        new_page = self._page_frames.get(page_id)
        
        if not new_page:
            return None
        
        # 如果低内存模式，禁用动画
        if self._is_low_memory_mode():
            self._show_page(page_id)
            return
        
        # 确定滑动方向：基于页面顺序
        page_order = [self.PAGE_HOME, self.PAGE_SINGLE, self.PAGE_BATCH, self.PAGE_HISTORY, self.PAGE_SETTINGS]
        try:
            old_idx = page_order.index(self._current_page)
            new_idx = page_order.index(page_id)
            direction = TransitionManager.DIRECTION_LEFT if new_idx > old_idx else TransitionManager.DIRECTION_RIGHT
        except ValueError:
            direction = TransitionManager.DIRECTION_LEFT
        
        # 更新导航按钮状态 (立即更新，不等动画完成)
        self._update_nav_buttons_animated(page_id)
        
        # 记录新页面
        old_current = self._current_page
        self._current_page = page_id
        
        def on_complete():
            page_names = {self.PAGE_HOME: '首页', self.PAGE_SINGLE: '单篇处理', self.PAGE_BATCH: '批量处理', self.PAGE_HISTORY: '历史记录', self.PAGE_SETTINGS: '设置'}
            page_name = page_names.get(page_id, page_id)
            self._animate_status_change(f'已切换到{page_name}')
        
        # 执行滑动过渡
        TransitionManager.slide_transition(
            self.root,
            self.content_area,
            old_page,
            new_page,
            direction=direction,
            on_complete=on_complete
        )
    
    def _fade_in_page(self, page_id: str):
        """淡入新页面并更新导航按钮状态 (兼容旧代码)"""
        new_page = self._page_frames.get(page_id)
        if not new_page:
            return None
        else:
            new_page.grid(row=0, column=0, sticky='nsew')
            self._update_nav_buttons_animated(page_id)
            self._current_page = page_id
            page_names = {self.PAGE_HOME: '首页', self.PAGE_SINGLE: '单篇处理', self.PAGE_BATCH: '批量处理', self.PAGE_HISTORY: '历史记录', self.PAGE_SETTINGS: '设置'}
            page_name = page_names.get(page_id, page_id)
            self._animate_status_change(f'已切换到{page_name}')
    def _update_nav_buttons_animated(self, active_page_id: str):
        """带平滑过渡动画更新导航按钮状态"""
        for pid, btn in self._nav_buttons.items():
            if pid == active_page_id:
                btn.configure(fg_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT), text_color='white', hover_color=(ModernColors.LIGHT_ACCENT_HOVER, ModernColors.DARK_ACCENT_HOVER))
            else:
                btn.configure(fg_color='transparent', text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT), hover_color=('#e0e0e0', '#2a2a4a'))
    def _animate_status_change(self, text: str):
        """动画状态变化"""
        self._set_status(text, ModernColors.INFO)
        self.root.after(1500, lambda: self._set_status('就绪', ModernColors.SUCCESS))
    def _on_theme_change(self, value: str):
        """主题切换"""
        mode = 'light' if value == '浅色' else 'dark'
        ctk.set_appearance_mode(mode)
        self._appearance_mode = mode
        
        # 同步更新 Windows 11 标题栏颜色
        Windows11StyleHelper.update_titlebar_color(self.root, mode)
        
        self._animate_status_change(f'已切换到{value}主题')
    def _toggle_log_panel(self):
        """切换日志面板"""
        if self._log_expanded:
            self.log_text.pack_forget()
            self.log_toggle_btn.configure(text='📋 日志 ▶')
            self._log_expanded = False
        else:
            self.log_text.pack(fill='x', padx=15, pady=(0, 10))
            self.log_toggle_btn.configure(text='📋 日志 ▼')
            self._log_expanded = True
    def _toggle_log_panel_animated(self):
        """带动画的日志面板切换"""
        if self._log_expanded:
            self._animate_log_collapse()
        else:
            self._animate_log_expand()
    def _animate_log_expand(self):
        """日志面板展开动画"""
        self.log_text.configure(height=1)
        self.log_text.pack(fill='x', padx=15, pady=(0, 10))
        self.log_toggle_btn.configure(text='📋 日志 ▼')
        self._log_expanded = True
        def update_height(h):
            try:
                self.log_text.configure(height=int(h))
            except Exception:
                return None
        AnimationHelper.animate_value(self.root, 1, 120, 200, update_height, easing=AnimationHelper.ease_out_cubic)
    def _animate_log_collapse(self):
        """日志面板收起动画"""
        def update_height(h):
            try:
                self.log_text.configure(height=int(h))
            except Exception:
                return None
        def on_complete():
            self.log_text.pack_forget()
            self.log_toggle_btn.configure(text='📋 日志 ▶')
            self._log_expanded = False
        AnimationHelper.animate_value(self.root, 120, 1, 200, update_height, easing=AnimationHelper.ease_out_cubic, on_complete=on_complete)
    def _clear_log(self):
        """清空日志"""
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.configure(state='disabled')
    def _copy_log(self):
        """复制日志"""
        content = self.log_text.get('1.0', 'end').strip()
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self._set_status('已复制到剪贴板', ModernColors.SUCCESS)
    def _set_status(self, text: str, color: str=ModernColors.SUCCESS, pulse: bool=False):
        """设置状态 - 支持脉冲动画效果\n        \n        Args:\n            text: 状态文本\n            color: 状态颜色\n            pulse: 是否启用脉冲动画（用于进行中的状态）\n        """
        self.status_label.configure(text=f'● {text}', text_color=color)
        if hasattr(self, '_pulse_animation_id') and self._pulse_animation_id:
                try:
                    self.root.after_cancel(self._pulse_animation_id)
                except Exception:
                    pass
                self._pulse_animation_id = None
        if pulse:
            self._start_pulse_animation(color)
    def _start_pulse_animation(self, base_color: str):
        """启动状态脉冲动画 - 交替明暗显示进行中"""
        self._pulse_phase = 0
        bright_color = self._adjust_color_brightness(base_color, 1.4)
        dim_color = self._adjust_color_brightness(base_color, 0.7)
        def pulse_step():
            if not hasattr(self, '_pulse_phase'):
                return None
            else:
                self._pulse_phase = (self._pulse_phase + 1) % 60
                import math
                t = (math.sin(self._pulse_phase * math.pi / 30) + 1) / 2
                try:
                    br = int(bright_color.lstrip('#')[0:2], 16)
                    bg = int(bright_color.lstrip('#')[2:4], 16)
                    bb = int(bright_color.lstrip('#')[4:6], 16)
                    dr = int(dim_color.lstrip('#')[0:2], 16)
                    dg = int(dim_color.lstrip('#')[2:4], 16)
                    db = int(dim_color.lstrip('#')[4:6], 16)
                    r = int(dr + (br - dr) * t)
                    g = int(dg + (bg - dg) * t)
                    b = int(db + (bb - db) * t)
                    current_color = f'#{r:02x}{g:02x}{b:02x}'
                    self.status_label.configure(text_color=current_color)
                except Exception:
                    pass
                self._pulse_animation_id = self.root.after(50, pulse_step)
        pulse_step()
    def _stop_pulse_animation(self):
        """停止脉冲动画"""
        if hasattr(self, '_pulse_animation_id') and self._pulse_animation_id:
                try:
                    self.root.after_cancel(self._pulse_animation_id)
                except Exception:
                    pass
                self._pulse_animation_id = None
    def _refresh_availability(self):
        """刷新可用性"""
        self._summarizer_info = self._get_summarizer_info()
        self._exporter_info = self._get_exporter_info()
        if hasattr(self, 'summarizer_status_frame'):
            self._update_summarizer_status_display()
        self._refresh_summarizer_menus()
        logger.info('已刷新服务状态')
        self._set_status('已刷新', ModernColors.SUCCESS)
    def _is_valid_wechat_url(self, url: str) -> bool:
        """检查是否为有效的微信公众号链接"""
        import re
        patterns = ['https?://mp\\.weixin\\.qq\\.com/s[/?]', 'https?://mp\\.weixin\\.qq\\.com/s/[\\w\\-]+']
        for pattern in patterns:
            if re.match(pattern, url.strip()):
                return True
        return False
    def _on_url_input_change(self, event=None):
        """单篇处理URL输入变化时的验证"""
        url = self.url_entry.get().strip()
        if not url:
            self.url_status_label.configure(text='', text_color='gray')
            return None
        else:
            if self._is_valid_wechat_url(url):
                self.url_status_label.configure(text='✓ 有效的微信公众号链接', text_color=ModernColors.SUCCESS)
            else:
                self.url_status_label.configure(text='✗ 请输入有效的微信公众号文章链接', text_color=ModernColors.ERROR)
    def _on_batch_url_input_change(self, event=None):
        """批量处理URL输入变化时的验证和去重"""
        content = self.batch_url_text.get('1.0', 'end').strip()
        if not content:
            self.batch_url_status_label.configure(text='', text_color='gray')
            return None
        else:
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            if not lines:
                self.batch_url_status_label.configure(text='', text_color='gray')
                return None
            else:
                valid_urls = []
                invalid_urls = []
                for url in lines:
                    if self._is_valid_wechat_url(url):
                        valid_urls.append(url)
                    else:
                        if url.startswith('http'):
                            invalid_urls.append(url)
                unique_urls = []
                duplicate_count = 0
                seen = set()
                for url in valid_urls:
                    if url in seen:
                        duplicate_count += 1
                    else:
                        seen.add(url)
                        unique_urls.append(url)
                if duplicate_count > 0:
                    cursor_pos = self.batch_url_text.index('insert')
                    self.batch_url_text.delete('1.0', 'end')
                    self.batch_url_text.insert('1.0', '\n'.join(unique_urls))
                    messagebox.showinfo('已自动去重', f'检测到 {duplicate_count} 个重复链接\n已自动删除重复项')
                    logger.info(f'已自动删除 {duplicate_count} 个重复链接')
                total_count = len(unique_urls)
                invalid_count = len(invalid_urls)
                if total_count > 0 and invalid_count == 0:
                    self.batch_url_status_label.configure(text=f'✓ 共 {total_count} 个有效链接', text_color=ModernColors.SUCCESS)
                    return None
                else:
                    if total_count > 0 and invalid_count > 0:
                        self.batch_url_status_label.configure(text=f'✓ {total_count} 个有效 | ✗ {invalid_count} 个无效', text_color=ModernColors.WARNING)
                    else:
                        self.batch_url_status_label.configure(text='✗ 未找到有效的微信公众号链接', text_color=ModernColors.ERROR)
    def _on_fetch(self):
        """处理抓取"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning('提示', '请输入文章URL')
            return None
        else:
            if not self._is_valid_wechat_url(url) and (not messagebox.askyesno('提示', '输入的链接可能不是有效的微信公众号链接\n\n是否继续处理？')):
                    return None
            
            # 设置任务状态（用于退出确认）
            self._single_processing_active = True
            
            self.fetch_btn.configure(state='disabled')
            self._set_status('正在抓取...', ModernColors.INFO, pulse=True)
            logger.info(f'开始抓取: {url}')
            threading.Thread(target=self._fetch_article, args=(url,), daemon=True).start()
    def _fetch_article(self, url: str):
        """后台抓取"""
        try:
            article = self.container.fetch_use_case.execute(url)
            logger.info(f'抓取成功: {article.title}')
            if self.summarize_var.get():
                method = self.method_var.get()
                try:
                    logger.info(f'正在生成摘要 ({method})...')
                    summary = self.container.summarize_use_case.execute(article, method=method)
                    article.attach_summary(summary)
                    logger.success('摘要生成完成')
                except Exception as e:
                    logger.warning(f'摘要生成失败: {e}')
            self.current_article = article
            self.root.after(0, lambda: self._display_result(article))
        except Exception as e:
            logger.error(f'处理失败: {e}')
            self.root.after(0, lambda: self._show_error(str(e)))
    def _display_result(self, article: 'Article'):
        """显示结果"""
        # 清除任务状态
        self._single_processing_active = False
        
        self.title_label.configure(text=f'标题: {article.title}')
        self.author_label.configure(text=f"公众号: {article.account_name or '未知'}")
        self.word_count_label.configure(text=f'字数: {article.word_count}')
        self.preview_text.delete('1.0', 'end')
        preview = article.content_text[:2000] + '...' if len(article.content_text) > 2000 else article.content_text
        self.preview_text.insert('1.0', preview)
        self.summary_text.delete('1.0', 'end')
        if article.summary:
            self.summary_text.insert('1.0', article.summary.content)
            self.points_text.delete('1.0', 'end')
            if article.summary.key_points:
                points = '\n'.join((f'• {p}' for p in article.summary.key_points))
                self.points_text.insert('1.0', points)
        self.export_btn.configure(state='normal')
        self.fetch_btn.configure(state='normal')
        self._set_status('处理完成', ModernColors.SUCCESS, pulse=False)
    def _show_error(self, message: str):
        """显示错误"""
        # 清除任务状态
        self._single_processing_active = False
        
        self.fetch_btn.configure(state='normal')
        self._set_status('处理失败', ModernColors.ERROR, pulse=False)
        messagebox.showerror('错误', message)
    def _check_export_dir_configured(self) -> bool:
        """检查导出目录是否已配置
        
        如果未配置导出目录，弹窗提醒用户设置。
        
        Returns:
            bool: True 如果已配置或用户选择继续，False 如果用户选择去设置
        """
        # 检查用户偏好中的导出目录
        user_export_dir = self.user_prefs.export_dir
        
        # 检查配置文件中的默认目录
        default_export_dir = self.settings.export.default_output_dir if hasattr(self.settings, 'export') else None
        
        # 如果两者都未配置，则提醒用户
        if not user_export_dir and not default_export_dir:
            result = messagebox.askyesno(
                '导出目录未设置',
                '您尚未设置默认导出目录。\n\n'
                '建议在「设置」页面配置导出目录，这样每次导出时会自动定位到该目录。\n\n'
                '是否继续导出？\n'
                '\n· 点击「是」继续导出（每次需手动选择位置）'
                '\n· 点击「否」前往设置页配置导出目录',
                icon='warning'
            )
            
            if not result:
                # 用户选择去设置
                self._show_page_animated(self.PAGE_SETTINGS)
                # 显示提示
                if hasattr(self, '_toast_manager') and self._toast_manager:
                    self._toast_manager.info('请在下方「导出设置」中配置默认导出目录')
                return False
        
        return True
    
    def _on_export(self):
        """导出"""
        if not self.current_article:
            return None
        
        # 检查导出目录配置
        if not self._check_export_dir_configured():
            return None
        
        export_window = ctk.CTkToplevel(self.root)
        export_window.title('导出选项')
        export_window.geometry('400x350')
        export_window.transient(self.root)
        ctk.CTkLabel(export_window, text='📥 选择导出格式', font=ctk.CTkFont(size=18, weight='bold')).pack(pady=20)
        
        def export_as(target: str):
            export_window.destroy()
            if target == 'word':
                self._show_word_preview()
            else:
                self._do_export(target)
        
        for name, info in self._exporter_info.items():
            btn_text = f"{('✓' if info.available else '✗')} {name.upper()}"
            if name == 'word' and info.available:
                btn_text += ' (预览)'
            btn = ctk.CTkButton(export_window, text=btn_text, font=ctk.CTkFont(size=14), height=45, corner_radius=10, fg_color=ModernColors.INFO if info.available else 'gray50', state='normal' if info.available else 'disabled', command=lambda t=name: export_as(t))
            btn.pack(fill='x', padx=30, pady=5)
            if not info.available and info.reason:
                ctk.CTkLabel(export_window, text=info.reason, font=ctk.CTkFont(size=11), text_color='gray').pack()
    def _show_word_preview(self):
        """Word预览 - 模拟最终Word文档布局"""
        if not self.current_article:
            return None
        else:
            article = self.current_article
            logger.info(f'打开Word预览: {article.title}')
            preview_window = ctk.CTkToplevel(self.root)
            preview_window.title(f'Word文档预览 - {article.title[:30]}...')
            preview_window.geometry('800x750')
            preview_window.transient(self.root)
            toolbar = ctk.CTkFrame(preview_window, height=40, fg_color='transparent')
            toolbar.pack(fill='x', padx=15, pady=(10, 5))
            ctk.CTkLabel(toolbar, text='📄 Word文档预览', font=ctk.CTkFont(size=16, weight='bold')).pack(side='left')
            ctk.CTkLabel(toolbar, text='以下预览与最终生成的Word文档布局一致', font=ctk.CTkFont(size=11), text_color='gray').pack(side='right')
            doc_container = ctk.CTkFrame(preview_window, corner_radius=5, fg_color=('#f0f0f0', '#2a2a2a'))
            doc_container.pack(fill='both', expand=True, padx=15, pady=5)
            doc_scroll = ctk.CTkScrollableFrame(doc_container, fg_color=('white', '#1e1e1e'), corner_radius=0)
            doc_scroll.pack(fill='both', expand=True, padx=20, pady=20)
            ctk.CTkLabel(doc_scroll, text=article.title, font=ctk.CTkFont(size=20, weight='bold'), wraplength=650, justify='center').pack(pady=(20, 10))
            meta_items = []
            if article.account_name:
                meta_items.append(f'公众号: {article.account_name}')
            if article.author:
                meta_items.append(f'作者: {article.author}')
            if article.publish_time:
                meta_items.append(f'发布时间: {article.publish_time_str}')
            meta_items.append(f'字数: {article.word_count}')
            ctk.CTkLabel(doc_scroll, text=' | '.join(meta_items), font=ctk.CTkFont(size=10), text_color='gray').pack()
            ctk.CTkLabel(doc_scroll, text=f'原文链接: {str(article.url)}', font=ctk.CTkFont(size=9), text_color=('#07C160', '#4CAF50'), cursor='hand2').pack(pady=(5, 10))
            ctk.CTkLabel(doc_scroll, text='────────────────────────────────────────────────────────────', text_color='gray').pack()
            if article.summary:
                ctk.CTkLabel(doc_scroll, text='📝 文章摘要', font=ctk.CTkFont(size=14, weight='bold'), text_color=('#07C160', '#4CAF50')).pack(anchor='w', padx=20, pady=(15, 8))
                summary_frame = ctk.CTkFrame(doc_scroll, fg_color=('#f8f9fa', '#2a2a2a'), corner_radius=8)
                summary_frame.pack(fill='x', padx=20, pady=5)
                ctk.CTkLabel(summary_frame, text=article.summary.content, font=ctk.CTkFont(size=11), wraplength=620, justify='left', anchor='w').pack(fill='x', padx=15, pady=10)
                if article.summary.key_points:
                    ctk.CTkLabel(doc_scroll, text='📌 关键要点', font=ctk.CTkFont(size=12, weight='bold')).pack(anchor='w', padx=20, pady=(15, 5))
                    for point in article.summary.key_points:
                        ctk.CTkLabel(doc_scroll, text=f'  • {point}', font=ctk.CTkFont(size=11), wraplength=620, justify='left', anchor='w').pack(fill='x', padx=25, pady=2)
                ctk.CTkLabel(doc_scroll, text='────────────────────────────────────────────────────────────', text_color='gray').pack(pady=10)
            ctk.CTkLabel(doc_scroll, text='📄 正文内容', font=ctk.CTkFont(size=14, weight='bold'), text_color=('#07C160', '#4CAF50')).pack(anchor='w', padx=20, pady=(10, 8))
            content_preview = self._build_content_preview_with_images(article)
            content_label = ctk.CTkLabel(doc_scroll, text=content_preview, font=ctk.CTkFont(size=11), wraplength=650, justify='left', anchor='w')
            content_label.pack(fill='x', padx=20, pady=5)
            images = self._extract_images_from_article(article)
            if images:
                img_info_frame = ctk.CTkFrame(doc_scroll, fg_color=('#e8f5e9', '#1b5e20'), corner_radius=8)
                img_info_frame.pack(fill='x', padx=20, pady=15)
                ctk.CTkLabel(img_info_frame, text=f'🖼️ 文档将包含 {len(images)} 张图片', font=ctk.CTkFont(size=11)).pack(pady=8)
            ctk.CTkLabel(doc_scroll, text='────────────────────────────────────────────────────────────', text_color='gray').pack(pady=(20, 5))
            footer_text = f"文章ID: {article.id} | 抓取时间: {article.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            ctk.CTkLabel(doc_scroll, text=footer_text, font=ctk.CTkFont(size=8), text_color='gray').pack()
            ctk.CTkLabel(doc_scroll, text='由 WeChat Article Summarizer 生成', font=ctk.CTkFont(size=8), text_color='gray').pack(pady=(0, 20))
            btn_frame = ctk.CTkFrame(preview_window, fg_color='transparent')
            btn_frame.pack(fill='x', padx=15, pady=10)
            def do_export():
                preview_window.destroy()
                self._do_export('word')
            ctk.CTkButton(btn_frame, text='🔗 查看原文', width=100, height=38, corner_radius=8, fg_color='gray40', command=lambda: webbrowser.open(str(article.url))).pack(side='left')
            ctk.CTkButton(btn_frame, text='取消', width=80, height=38, corner_radius=8, fg_color='gray40', command=preview_window.destroy).pack(side='right', padx=(5, 0))
            ctk.CTkButton(btn_frame, text='✓ 确认导出Word', width=150, height=38, corner_radius=8, fg_color=ModernColors.SUCCESS, command=do_export).pack(side='right')
    def _build_content_preview_with_images(self, article: 'Article') -> str:
        """构建带图片位置标记的内容预览"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(article.content_html, 'html.parser')
            content_container = soup.find(id='js_content') or soup.find(class_='rich_media_content') or soup.body or soup
            result_parts = []
            img_counter = [0]
            def process_element(element, depth=0):
                from bs4 import NavigableString
                if isinstance(element, NavigableString):
                    text = str(element).strip()
                    if text and len(text) > 1:
                            result_parts.append(text)
                    return None
                else:
                    tag_name = getattr(element, 'name', None)
                    if not tag_name or tag_name in ['script', 'style', 'meta', 'link', 'noscript']:
                        return None
                    else:
                        if tag_name == 'img':
                            img_counter[0] += 1
                            img_url = element.get('data-src') or element.get('src') or ''
                            if 'emoji' not in img_url.lower() and 'emotion' not in img_url.lower():
                                    result_parts.append(f'\n\n[图片 {img_counter[0]}]\n\n')
                            return None
                        else:
                            if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                                text = element.get_text(strip=True)
                                if text:
                                    result_parts.append(f'\n\n【{text}】\n\n')
                                return None
                            else:
                                if tag_name == 'p':
                                    for img in element.find_all('img'):
                                        img_counter[0] += 1
                                        img_url = img.get('data-src') or img.get('src') or ''
                                        if 'emoji' not in img_url.lower() and 'emotion' not in img_url.lower():
                                                result_parts.append(f'\n\n[图片 {img_counter[0]}]\n\n')
                                    text = element.get_text(strip=True)
                                    if text:
                                        result_parts.append(f'\n    {text}\n')
                                    return None
                                else:
                                    if tag_name in ['ul', 'ol']:
                                        for li in element.find_all('li', recursive=False):
                                            text = li.get_text(strip=True)
                                            if text:
                                                result_parts.append(f'\n  • {text}')
                                        result_parts.append('\n')
                                        return None
                                    else:
                                        if tag_name == 'blockquote':
                                            text = element.get_text(strip=True)
                                            if text:
                                                result_parts.append(f'\n    「{text}」\n')
                                            return None
                                        else:
                                            if tag_name == 'table':
                                                result_parts.append('\n\n┌────────── 表格 ──────────┐\n')
                                                rows = element.find_all('tr')
                                                for row_idx, row in enumerate(rows):
                                                    cells = row.find_all(['td', 'th'])
                                                    row_texts = []
                                                    for cell in cells:
                                                        cell_text = cell.get_text(strip=True)
                                                        if len(cell_text) > 20:
                                                            cell_text = cell_text[:17] + '...'
                                                        row_texts.append(cell_text)
                                                    if row_texts:
                                                        row_str = ' │ '.join(row_texts)
                                                        result_parts.append(f'│ {row_str} │\n')
                                                        if row_idx == 0:
                                                            result_parts.append('├──────────────────────────────┤\n')
                                                result_parts.append('└──────────────────────────────┘\n\n')
                                            else:
                                                if hasattr(element, 'children'):
                                                    for child in element.children:
                                                        process_element(child, depth + 1)
            process_element(content_container)
            preview = ''.join(result_parts)
            import re
            preview = re.sub('\\n{3,}', '\n\n', preview)
            if len(preview) > 3000:
                preview = preview[:3000] + '\n\n... (预览已截断，完整内容将包含在Word文档中) ...'
            return preview.strip()
        except Exception as e:
            logger.warning(f'构建内容预览失败: {e}')
            text = article.content_text
            if len(text) > 3000:
                text = text[:3000] + '\n\n... (预览已截断) ...'
            return text
    def _extract_images_from_article(self, article: 'Article') -> list[str]:
        """提取图片"""
        images = []
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(article.content_html, 'html.parser')
            for img in soup.find_all('img'):
                img_url = img.get('data-src') or img.get('src')
                if img_url and img_url.startswith('http'):
                    images.append(img_url)
        except Exception as e:
            logger.warning(f'提取图片失败: {e}')
        return images
    def _do_export(self, target: str):
        """执行导出"""
        if not self.current_article:
            return None
        else:
            logger.info(f'开始导出: {target}')
            ext_map = {'html': ('.html', 'HTML文件', '*.html'), 'markdown': ('.md', 'Markdown文件', '*.md'), 'word': ('.docx', 'Word文档', '*.docx'), 'zip': ('.zip', 'ZIP文件', '*.zip')}
            ext_info = ext_map.get(target, ('.html', 'HTML文件', '*.html'))
            initial_dir = None
            if self.user_prefs.remember_export_dir and self.user_prefs.export_dir:
                dir_path = Path(self.user_prefs.export_dir)
                if dir_path.exists():
                    initial_dir = str(dir_path)
            if not initial_dir:
                default_dir = self.settings.export.default_output_dir
                if default_dir and Path(default_dir).exists():
                    initial_dir = default_dir
            path = filedialog.asksaveasfilename(defaultextension=ext_info[0], filetypes=[(ext_info[1], ext_info[2])], initialfile=f'{self.current_article.title[:30]}{ext_info[0]}', initialdir=initial_dir)
            if not path:
                logger.info('导出已取消')
                return None
            else:
                if self.user_prefs.remember_export_dir:
                    export_dir = str(Path(path).parent)
                    if export_dir!= self.user_prefs.export_dir:
                        self.user_prefs.export_dir = export_dir
                        logger.info(f'已记住导出目录: {export_dir}')
                self.export_btn.configure(state='disabled')
                self._set_status('正在导出...', ModernColors.INFO)
                def do_export():
                    try:
                        logger.info(f'导出路径: {path}')
                        result = self.container.export_use_case.execute(self.current_article, target=target, path=path)
                        logger.success(f'导出成功: {result}')
                        self.root.after(0, lambda: self._export_complete(True, str(result)))
                    except Exception as e:
                        logger.error(f'导出失败: {e}')
                        self.root.after(0, lambda: self._export_complete(False, str(e)))
                threading.Thread(target=do_export, daemon=True).start()
    def _export_complete(self, success: bool, message: str):
        """导出完成"""
        self.export_btn.configure(state='normal')
        if success:
            self._set_status('导出完成', ModernColors.SUCCESS)
            messagebox.showinfo('成功', f'导出成功: {message}')
        else:
            self._set_status('导出失败', ModernColors.ERROR)
            messagebox.showerror('错误', f'导出失败: {message}')
    def _on_import_urls(self):
        """导入URL"""
        path = filedialog.askopenfilename(filetypes=[('Text files', '*.txt'), ('All files', '*.*')])
        if not path:
            return None
        else:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.batch_url_text.delete('1.0', 'end')
                self.batch_url_text.insert('1.0', content)
                logger.info(f'已导入URL文件: {path}')
            except Exception as e:
                messagebox.showerror('错误', f'读取失败: {e}')
    def _on_paste_urls(self):
        """粘贴URL"""
        try:
            content = self.root.clipboard_get()
            self.batch_url_text.insert('end', content)
        except Exception:
            messagebox.showwarning('提示', '剪贴板为空')
    def _on_batch_process(self):
        """批量处理"""
        content = self.batch_url_text.get('1.0', 'end').strip()
        if not content:
            messagebox.showwarning('提示', '请输入URL')
            return None
        else:
            urls = [line.strip() for line in content.split('\n') if line.strip()]
            if not urls:
                messagebox.showwarning('提示', '未找到有效URL')
                return None
            else:
                self._start_batch_processing(urls)
    def _start_batch_processing(self, urls: List[str]):
        """开始批量处理"""
        self.batch_urls = urls
        self.batch_results = []
        self._batch_progress_tracker = BatchProgressTracker(total=len(urls), smoothing_factor=0.3, log_interval=1)
        self._batch_progress_tracker.set_callback(self._on_batch_progress_update)
        self.batch_start_btn.configure(state='disabled')
        self.batch_progress.set(0)
        self.batch_status_label.configure(text=f'正在处理 0/{len(urls)} 篇...')
        self.batch_elapsed_label.configure(text='00:00')
        self.batch_eta_label.configure(text='--:--')
        self.batch_rate_label.configure(text='计算中...')
        self.batch_count_label.configure(text='0 / 0')
        
        # 设置任务状态（用于退出确认）
        self._batch_processing_active = True
        
        logger.info(f'🚀 开始批量处理 {len(urls)} 篇文章')
        for widget in self.batch_result_frame.winfo_children():
            widget.destroy()
        threading.Thread(target=self._batch_process_worker, daemon=True).start()
    def _on_batch_progress_update(self, info: ProgressInfo):
        """进度更新回调（在工作线程中调用）"""
        self.root.after(0, lambda: self._update_batch_progress_ui(info))
    def _update_batch_progress_ui(self, info: ProgressInfo):
        """更新批量处理的GUI进度显示（在主线程中调用）"""
        progress_value = info.percentage / 100.0
        self.batch_progress.set(progress_value)
        self.batch_status_label.configure(text=f'正在处理 {info.progress_text} ({info.percentage_text})')
        self.batch_elapsed_label.configure(text=info.elapsed_formatted)
        self.batch_eta_label.configure(text=info.eta_formatted)
        self.batch_rate_label.configure(text=info.rate_formatted)
        if hasattr(self, '_batch_progress_tracker'):
            tracker = self._batch_progress_tracker
            self.batch_count_label.configure(text=f'{tracker.success_count} / {tracker.failure_count}')
    def _batch_process_worker(self):
        """批量处理工作线程"""
        method = self.batch_method_var.get()
        total = len(self.batch_urls)
        tracker = self._batch_progress_tracker
        for i, url in enumerate(self.batch_urls):
            short_url = url[:50] + '...' if len(url) > 50 else url
            try:
                article = self.container.fetch_use_case.execute(url)
                try:
                    summary = self.container.summarize_use_case.execute(article, method=method)
                    article.attach_summary(summary)
                except Exception as e:
                    logger.warning(f'摘要失败: {e}')
                self.batch_results.append(article)
                tracker.update_success(current_item=article.title[:30])
                self.root.after(0, lambda a=article: self._add_batch_result_item(a, True))
            except Exception as e:
                logger.error(f'处理失败 {short_url}: {e}')
                tracker.update_failure(current_item=short_url, error=str(e))
                self.root.after(0, lambda u=url, err=str(e): self._add_batch_result_item_error(u, err))
        tracker.finish()
        self.root.after(0, self._batch_process_complete)
    def _update_batch_progress(self, value: float, status: str):
        """更新批量进度（兼容旧接口）"""
        self.batch_progress.set(value)
        self.batch_status_label.configure(text=status)
    def _add_batch_result_item(self, article: 'Article', success: bool):
        """添加批量结果项"""
        frame = ctk.CTkFrame(self.batch_result_frame, corner_radius=8, fg_color=('#e8e8e8', 'gray25'))
        frame.pack(fill='x', pady=3)
        icon = '✓' if success else '✗'
        color = ModernColors.SUCCESS if success else ModernColors.ERROR
        title = article.title[:35] + '...' if len(article.title) > 35 else article.title
        ctk.CTkLabel(frame, text=f'{icon} {title}', anchor='w', text_color=color).pack(side='left', padx=10, pady=8, fill='x', expand=True)
    def _add_batch_result_item_error(self, url: str, error: str):
        """添加错误项"""
        frame = ctk.CTkFrame(self.batch_result_frame, corner_radius=8, fg_color=('#e8e8e8', 'gray25'))
        frame.pack(fill='x', pady=3)
        short_url = url[:25] + '...' if len(url) > 25 else url
        ctk.CTkLabel(frame, text=f'✗ {short_url}', anchor='w', text_color=ModernColors.ERROR).pack(side='left', padx=10, pady=8)
        ctk.CTkLabel(frame, text=error[:30], text_color='gray', font=ctk.CTkFont(size=11)).pack(side='right', padx=10, pady=8)
    def _batch_process_complete(self):
        """批量处理完成"""
        # 清除任务状态
        self._batch_processing_active = False
        
        self.batch_start_btn.configure(state='normal')
        self.batch_progress.set(1.0)
        success_count = len(self.batch_results)
        total = len(self.batch_urls)
        self.batch_status_label.configure(text=f'完成: {success_count}/{total} 篇成功')
        logger.success(f'批量处理完成: {success_count}/{total}')
        if self.batch_results:
            self.batch_export_btn.configure(state='normal')
            self.batch_export_md_btn.configure(state='normal')
            self.batch_export_word_btn.configure(state='normal')
            self.batch_export_html_btn.configure(state='normal')
    def _on_batch_export(self):
        """批量压缩导出 - 支持多格式和文章选择"""
        if not self.batch_results:
            return None
        
        # 检查导出目录配置
        if not self._check_export_dir_configured():
            return None
        
        # 显示批量压缩导出对话框
        dialog = BatchArchiveExportDialog(self.root, self.batch_results)
        result = dialog.get()
        
        if not result:
            return None  # 用户取消
        
        # 执行多格式压缩导出
        self._do_archive_export(
            articles=result['articles'],
            archive_format=result['format'],
            path=result['path']
        )
    
    def _do_archive_export(self, articles: list, archive_format: str, path: str):
        """执行多格式压缩导出（带进度跟踪）
        
        Args:
            articles: 要导出的文章列表
            archive_format: 压缩格式 ('zip', '7z', 'rar')
            path: 输出路径
        """
        self._disable_export_buttons()
        self._archive_export_articles = articles  # 保存要导出的文章
        self._archive_progress_tracker = BatchProgressTracker(
            total=len(articles), 
            smoothing_factor=0.3, 
            log_interval=1
        )
        self._archive_progress_tracker.set_callback(self._on_export_progress_update)
        self.batch_progress.set(0)
        
        format_names = {'zip': 'ZIP', '7z': '7z', 'rar': 'RAR'}
        format_name = format_names.get(archive_format, archive_format.upper())
        
        self.batch_status_label.configure(text=f'正在打包 0/{len(articles)} 篇为 {format_name}...')
        self.batch_elapsed_label.configure(text='00:00')
        self.batch_eta_label.configure(text='--:--')
        self.batch_rate_label.configure(text='计算中...')
        self.batch_count_label.configure(text='0 / 0')
        
        # 设置任务状态（用于退出确认）
        self._batch_export_active = True
        
        logger.info(f'📦 开始导出 {len(articles)} 篇文章为 {format_name} 压缩包')
        threading.Thread(
            target=self._archive_export_worker, 
            args=(articles, archive_format, path), 
            daemon=True
        ).start()
    
    def _archive_export_worker(self, articles: list, archive_format: str, path: str):
        """工作线程：执行多格式压缩导出"""
        try:
            from ...infrastructure.adapters.exporters import MultiFormatArchiveExporter
            
            tracker = self._archive_progress_tracker
            
            def progress_callback(current: int, total: int, item_name: str):
                if current > tracker.current:
                    tracker.update_success(current_item=item_name)
            
            # 创建多格式压缩导出器
            exporter = MultiFormatArchiveExporter()
            result = exporter.export_batch(
                articles=articles,
                path=path,
                archive_format=archive_format,
                progress_callback=progress_callback
            )
            
            tracker.finish()
            self.root.after(0, lambda: self._archive_export_complete(result, archive_format))
        except Exception as e:
            logger.error(f'压缩导出失败: {e}')
            self.root.after(0, lambda: self._archive_export_error(str(e)))
    
    def _archive_export_complete(self, result: str, archive_format: str):
        """处理压缩导出完成"""
        # 清除任务状态
        self._batch_export_active = False
        
        self._enable_export_buttons()
        self.batch_progress.set(1.0)
        
        format_names = {'zip': 'ZIP', '7z': '7z', 'rar': 'RAR'}
        format_name = format_names.get(archive_format, archive_format.upper())
        
        self.batch_status_label.configure(text=f'{format_name} 导出完成')
        logger.success(f'批量导出成功: {result}')
        messagebox.showinfo('成功', f'导出成功: {result}')
    
    def _archive_export_error(self, error: str):
        """处理压缩导出错误"""
        # 清除任务状态
        self._batch_export_active = False
        
        self._enable_export_buttons()
        self.batch_status_label.configure(text='压缩导出失败')
        messagebox.showerror('错误', f'导出失败: {error}')
    def _on_batch_export_format(self, target: str):
        """批量导出指定格式"""
        if not self.batch_results:
            return None
        
        # 检查导出目录配置
        if not self._check_export_dir_configured():
            return None
        
        if target == 'word':
            self._show_batch_word_preview()
            return None
        else:
            dir_path = filedialog.askdirectory(title='选择输出目录')
            if not dir_path:
                return None
            else:
                self._do_batch_export(target, dir_path)
    def _do_batch_export(self, target: str, dir_path: str):
        """执行批量导出（在后台线程中执行）"""
        self._disable_export_buttons()
        self._export_progress_tracker = BatchProgressTracker(total=len(self.batch_results), smoothing_factor=0.3, log_interval=1)
        self._export_progress_tracker.set_callback(self._on_export_progress_update)
        self.batch_progress.set(0)
        self.batch_status_label.configure(text=f'正在导出 0/{len(self.batch_results)} 篇...')
        self.batch_elapsed_label.configure(text='00:00')
        self.batch_eta_label.configure(text='--:--')
        self.batch_rate_label.configure(text='计算中...')
        self.batch_count_label.configure(text='0 / 0')
        
        # 设置任务状态（用于退出确认）
        self._batch_export_active = True
        
        logger.info(f'📤 开始批量导出 {len(self.batch_results)} 篇文章为 {target.upper()} 格式')
        threading.Thread(target=self._batch_export_worker, args=(target, dir_path), daemon=True).start()
    def _on_export_progress_update(self, info: ProgressInfo):
        """导出进度更新回调"""
        self.root.after(0, lambda: self._update_export_progress_ui(info))
    def _update_export_progress_ui(self, info: ProgressInfo):
        """更新导出进度GUI显示"""
        progress_value = info.percentage / 100.0
        self.batch_progress.set(progress_value)
        self.batch_status_label.configure(text=f'正在导出 {info.progress_text} ({info.percentage_text})')
        self.batch_elapsed_label.configure(text=info.elapsed_formatted)
        self.batch_eta_label.configure(text=info.eta_formatted)
        self.batch_rate_label.configure(text=info.rate_formatted)
        if hasattr(self, '_export_progress_tracker'):
            tracker = self._export_progress_tracker
            self.batch_count_label.configure(text=f'{tracker.success_count} / {tracker.failure_count}')
    def _batch_export_worker(self, target: str, dir_path: str):
        """批量导出工作线程"""
        try:
            output_dir = Path(dir_path)
            tracker = self._export_progress_tracker
            ext_map = {'markdown': '.md', 'html': '.html', 'word': '.docx'}
            ext = ext_map.get(target, '.html')
            for article in self.batch_results:
                try:
                    safe_title = ''.join((c for c in article.title[:50] if c.isalnum() or c in ' _-')).strip()
                    file_path = output_dir / f'{safe_title}{ext}'
                    self.container.export_use_case.execute(article, target=target, path=str(file_path))
                    tracker.update_success(current_item=article.title[:30])
                except Exception as e:
                    logger.warning(f'导出失败 {article.title}: {e}')
                    tracker.update_failure(current_item=article.title[:30], error=str(e))
            tracker.finish()
            self.root.after(0, lambda: self._batch_export_complete(tracker.success_count, tracker.failure_count, dir_path))
        except Exception as e:
            logger.error(f'导出失败: {e}')
            self.root.after(0, lambda: self._batch_export_error(str(e)))
    def _batch_export_complete(self, success_count: int, failure_count: int, dir_path: str):
        """批量导出完成"""
        # 清除任务状态
        self._batch_export_active = False
        
        self._enable_export_buttons()
        self.batch_progress.set(1.0)
        self.batch_status_label.configure(text=f'导出完成: {success_count} 成功, {failure_count} 失败')
        total = success_count + failure_count
        logger.success(f'批量导出完成: {success_count}/{total}')
        messagebox.showinfo('成功', f'导出完成: {success_count}/{total} 篇\n输出目录: {dir_path}')
    def _batch_export_error(self, error: str):
        """批量导出出错"""
        # 清除任务状态
        self._batch_export_active = False
        
        self._enable_export_buttons()
        self.batch_status_label.configure(text='导出失败')
        messagebox.showerror('错误', f'导出失败: {error}')
    def _disable_export_buttons(self):
        """禁用所有导出按钮"""
        self.batch_export_btn.configure(state='disabled')
        self.batch_export_md_btn.configure(state='disabled')
        self.batch_export_word_btn.configure(state='disabled')
        self.batch_export_html_btn.configure(state='disabled')
    def _enable_export_buttons(self):
        """启用所有导出按钮"""
        if self.batch_results:
            self.batch_export_btn.configure(state='normal')
            self.batch_export_md_btn.configure(state='normal')
            self.batch_export_word_btn.configure(state='normal')
            self.batch_export_html_btn.configure(state='normal')
    def _show_batch_word_preview(self):
        """显示批量 Word 导出预览窗口（带翻页功能）- 与单篇预览样式一致"""
        if not self.batch_results:
            return None
        else:
            preview_window = ctk.CTkToplevel(self.root)
            preview_window.title(f'Word 导出预览 - 共 {len(self.batch_results)} 篇文章')
            preview_window.geometry('800x750')
            preview_window.transient(self.root)
            preview_window.update_idletasks()
            x = self.root.winfo_rootx() + (self.root.winfo_width() - 800) // 2
            y = self.root.winfo_rooty() + (self.root.winfo_height() - 750) // 2
            preview_window.geometry(f'+{x}+{y}')
            current_page = [0]
            total_pages = len(self.batch_results)
            toolbar = ctk.CTkFrame(preview_window, height=40, fg_color='transparent')
            toolbar.pack(fill='x', padx=15, pady=(10, 5))
            ctk.CTkLabel(toolbar, text='📄 Word文档预览', font=ctk.CTkFont(size=16, weight='bold')).pack(side='left')
            ctk.CTkLabel(toolbar, text='以下预览与最终生成的Word文档布局一致', font=ctk.CTkFont(size=11), text_color='gray').pack(side='right')
            nav_bar = ctk.CTkFrame(preview_window, height=40, fg_color='transparent')
            nav_bar.pack(fill='x', padx=15, pady=(0, 5))
            def go_next():
                if current_page[0] < total_pages - 1:
                    current_page[0] += 1
                    update_preview()
            def go_prev():
                if current_page[0] > 0:
                    current_page[0] -= 1
                    update_preview()
            prev_btn = ctk.CTkButton(nav_bar, text='◀ 上一篇', width=90, height=32, corner_radius=8, fg_color='gray40', command=go_prev)
            prev_btn.pack(side='left', padx=2)
            page_frame = ctk.CTkFrame(nav_bar, fg_color='transparent')
            page_frame.pack(side='left', expand=True)
            page_label = ctk.CTkLabel(page_frame, text=f'第 1 篇 / 共 {total_pages} 篇', font=ctk.CTkFont(size=13))
            page_label.pack()
            next_btn = ctk.CTkButton(nav_bar, text='下一篇 ▶', width=90, height=32, corner_radius=8, fg_color='gray40', command=go_next)
            next_btn.pack(side='right', padx=2)
            doc_container = ctk.CTkFrame(preview_window, corner_radius=5, fg_color=('#f0f0f0', '#2a2a2a'))
            doc_container.pack(fill='both', expand=True, padx=15, pady=5)
            doc_scroll = ctk.CTkScrollableFrame(doc_container, fg_color=('white', '#1e1e1e'), corner_radius=0)
            doc_scroll.pack(fill='both', expand=True, padx=20, pady=20)
            def update_preview():
                for widget in doc_scroll.winfo_children():
                    widget.destroy()
                article = self.batch_results[current_page[0]]
                page_label.configure(text=f'第 {current_page[0] + 1} 篇 / 共 {total_pages} 篇')
                prev_btn.configure(state='normal' if current_page[0] > 0 else 'disabled')
                next_btn.configure(state='normal' if current_page[0] < total_pages - 1 else 'disabled')
                ctk.CTkLabel(doc_scroll, text=article.title, font=ctk.CTkFont(size=20, weight='bold'), wraplength=650, justify='center').pack(pady=(20, 10))
                meta_items = []
                if article.account_name:
                    meta_items.append(f'公众号: {article.account_name}')
                if article.author:
                    meta_items.append(f'作者: {article.author}')
                if article.publish_time:
                    meta_items.append(f'发布时间: {article.publish_time_str}')
                meta_items.append(f'字数: {article.word_count}')
                ctk.CTkLabel(doc_scroll, text=' | '.join(meta_items), font=ctk.CTkFont(size=10), text_color='gray').pack()
                link_label = ctk.CTkLabel(doc_scroll, text=f'原文链接: {str(article.url)}', font=ctk.CTkFont(size=9), text_color=('#07C160', '#4CAF50'), cursor='hand2')
                link_label.pack(pady=(5, 10))
                link_label.bind('<Button-1>', lambda e: webbrowser.open(str(article.url)))
                ctk.CTkLabel(doc_scroll, text='────────────────────────────────────────────────────────────', text_color='gray').pack()
                if article.summary:
                    ctk.CTkLabel(doc_scroll, text='📝 文章摘要', font=ctk.CTkFont(size=14, weight='bold'), text_color=('#07C160', '#4CAF50')).pack(anchor='w', padx=20, pady=(15, 8))
                    summary_frame = ctk.CTkFrame(doc_scroll, fg_color=('#f8f9fa', '#2a2a2a'), corner_radius=8)
                    summary_frame.pack(fill='x', padx=20, pady=5)
                    ctk.CTkLabel(summary_frame, text=article.summary.content, font=ctk.CTkFont(size=11), wraplength=620, justify='left', anchor='w').pack(fill='x', padx=15, pady=10)
                    if article.summary.key_points:
                        ctk.CTkLabel(doc_scroll, text='📌 关键要点', font=ctk.CTkFont(size=12, weight='bold')).pack(anchor='w', padx=20, pady=(15, 5))
                        for point in article.summary.key_points:
                            ctk.CTkLabel(doc_scroll, text=f'  • {point}', font=ctk.CTkFont(size=11), wraplength=620, justify='left', anchor='w').pack(fill='x', padx=25, pady=2)
                    ctk.CTkLabel(doc_scroll, text='────────────────────────────────────────────────────────────', text_color='gray').pack(pady=10)
                ctk.CTkLabel(doc_scroll, text='📄 正文内容', font=ctk.CTkFont(size=14, weight='bold'), text_color=('#07C160', '#4CAF50')).pack(anchor='w', padx=20, pady=(10, 8))
                content_preview = self._build_content_preview_with_images(article)
                content_label = ctk.CTkLabel(doc_scroll, text=content_preview, font=ctk.CTkFont(size=11), wraplength=650, justify='left', anchor='w')
                content_label.pack(fill='x', padx=20, pady=5)
                images = self._extract_images_from_article(article)
                if images:
                    img_info_frame = ctk.CTkFrame(doc_scroll, fg_color=('#e8f5e9', '#1b5e20'), corner_radius=8)
                    img_info_frame.pack(fill='x', padx=20, pady=15)
                    ctk.CTkLabel(img_info_frame, text=f'🖼️ 文档将包含 {len(images)} 张图片', font=ctk.CTkFont(size=11)).pack(pady=8)
                ctk.CTkLabel(doc_scroll, text='────────────────────────────────────────────────────────────', text_color='gray').pack(pady=(20, 5))
                footer_text = f"文章 {current_page[0] + 1}/{total_pages} | ID: {article.id} | 抓取时间: {article.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                ctk.CTkLabel(doc_scroll, text=footer_text, font=ctk.CTkFont(size=8), text_color='gray').pack()
                ctk.CTkLabel(doc_scroll, text='由 WeChat Article Summarizer 生成', font=ctk.CTkFont(size=8), text_color='gray').pack(pady=(0, 20))
            update_preview()
            btn_frame = ctk.CTkFrame(preview_window, fg_color='transparent')
            btn_frame.pack(fill='x', padx=15, pady=10)
            def open_current_url():
                article = self.batch_results[current_page[0]]
                webbrowser.open(str(article.url))
            def do_export():
                dir_path = filedialog.askdirectory(title='选择输出目录')
                if dir_path:
                    preview_window.destroy()
                    self._do_batch_export('word', dir_path)
            ctk.CTkButton(btn_frame, text='🔗 查看当前原文', width=120, height=38, corner_radius=8, fg_color='gray40', command=open_current_url).pack(side='left')
            ctk.CTkButton(btn_frame, text='取消', width=80, height=38, corner_radius=8, fg_color='gray40', command=preview_window.destroy).pack(side='right', padx=(5, 0))
            ctk.CTkButton(btn_frame, text=f'✓ 导出全部 {total_pages} 篇为 Word', width=200, height=38, corner_radius=8, fg_color=ModernColors.SUCCESS, font=ctk.CTkFont(size=14, weight='bold'), command=do_export).pack(side='right')
            def on_key(event):
                if event.keysym == 'Left':
                    go_prev()
                else:
                    if event.keysym == 'Right':
                        go_next()
            preview_window.bind('<Left>', on_key)
            preview_window.bind('<Right>', on_key)
    def _refresh_history(self):
        """刷新历史"""
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        storage = self.container.storage
        if not storage:
            ctk.CTkLabel(self.history_frame, text='缓存存储不可用', text_color='gray').pack(pady=30)
            return None
        else:
            try:
                stats = storage.get_stats()
                self.cache_stats_label.configure(text=f'缓存: {stats.total_entries} 条 | {stats.total_size_bytes / 1024:.1f} KB')
                articles = storage.list_recent(limit=50)
                if not articles:
                    ctk.CTkLabel(self.history_frame, text='暂无历史记录', text_color='gray').pack(pady=30)
                else:
                    for article in articles:
                        self._add_history_item(article)
            except Exception as e:
                logger.error(f'加载历史失败: {e}')
                ctk.CTkLabel(self.history_frame, text=f'加载失败: {e}', text_color=ModernColors.ERROR).pack(pady=30)
    def _add_history_item(self, article: 'Article'):
        """添加历史项"""
        frame = ctk.CTkFrame(self.history_frame, corner_radius=10, fg_color=('#e8e8e8', 'gray25'))
        frame.pack(fill='x', pady=4)
        title = article.title[:45] + '...' if len(article.title) > 45 else article.title
        ctk.CTkLabel(frame, text=title, anchor='w', font=ctk.CTkFont(size=13)).pack(side='left', padx=15, pady=10, fill='x', expand=True)
        if article.created_at:
            time_str = article.created_at.strftime('%m-%d %H:%M')
            ctk.CTkLabel(frame, text=time_str, text_color='gray', font=ctk.CTkFont(size=11)).pack(side='left', padx=5)
        ctk.CTkButton(frame, text='查看', width=60, height=28, corner_radius=6, font=ctk.CTkFont(size=11), fg_color=ModernColors.INFO, command=lambda a=article: self._view_history_article(a)).pack(side='right', padx=5, pady=8)
        ctk.CTkButton(frame, text='删除', width=60, height=28, corner_radius=6, font=ctk.CTkFont(size=11), fg_color='gray40', hover_color=ModernColors.ERROR, command=lambda a=article: self._delete_history_article(a)).pack(side='right', padx=2, pady=8)
    def _view_history_article(self, article: 'Article'):
        """查看历史文章"""
        self.current_article = article
        self._show_page(self.PAGE_SINGLE)
        self._display_result(article)
        self.url_entry.delete(0, 'end')
        self.url_entry.insert(0, str(article.url))
    def _delete_history_article(self, article: 'Article'):
        """删除历史文章"""
        if not messagebox.askyesno('确认', f'删除 "{article.title[:25]}..." ?'):
            return None
        try:
            storage = self.container.storage
            if storage:
                storage.delete(article.id)
                self._refresh_history()
                logger.info(f'已删除: {article.title}')
        except Exception as e:
            messagebox.showerror('错误', f'删除失败: {e}')
    def _on_clear_cache(self):
        """清空缓存"""
        if not messagebox.askyesno('确认', '确定清空所有缓存？此操作不可撤销。'):
            return None
        try:
            storage = self.container.storage
            if storage:
                count = storage.clear_all()
                self._refresh_history()
                logger.info(f'已清空 {count} 条缓存')
                messagebox.showinfo('成功', f'已清空 {count} 条缓存')
        except Exception as e:
            messagebox.showerror('错误', f'清空失败: {e}')
    def run(self):
        """运行GUI"""
        self.root.mainloop()
def run_gui():
    """启动GUI"""
    if not _ctk_available:
        print('错误: customtkinter未安装')
        print('请运行: pip install customtkinter')
        return None
    else:
        app = WechatSummarizerGUI()
        app.run()
if __name__ == '__main__':
    run_gui()