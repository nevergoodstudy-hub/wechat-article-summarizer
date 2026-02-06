"""字体系统管理器 - 2026 UI设计趋势

提供：
- 统一字体规范
- 可变字重系统
- 行高/字距优化
- 多语言字体回退

安全审查：
- 字体加载异常处理
- 跨平台兼容性
"""
from __future__ import annotations

import platform
from enum import Enum
from typing import Tuple, Optional


class FontWeight(Enum):
    """字重标准"""
    THIN = 100        # 极细
    EXTRA_LIGHT = 200 # 特细
    LIGHT = 300       # 细
    REGULAR = 400     # 常规
    MEDIUM = 500      # 中等
    SEMI_BOLD = 600   # 半粗
    BOLD = 700        # 粗
    EXTRA_BOLD = 800  # 特粗
    BLACK = 900       # 黑体


class FontSize(Enum):
    """字号标准"""
    XS = 10    # 极小 (辅助信息、时间戳)
    SM = 12    # 小 (次要文本、标签)
    BASE = 14  # 基础 (正文)
    MD = 16    # 中 (强调文本)
    LG = 18    # 大 (小标题)
    XL = 20    # 特大 (副标题)
    XXL = 24   # 超大 (标题)
    XXXL = 32  # 极大 (主标题)
    HUGE = 48  # 巨大 (展示标题)


class LineHeight(Enum):
    """行高标准 (相对值)"""
    TIGHT = 1.2    # 紧凑 (标题)
    NORMAL = 1.5   # 正常 (正文)
    RELAXED = 1.8  # 宽松 (长文本)
    LOOSE = 2.0    # 很宽松 (特殊场景)


class LetterSpacing(Enum):
    """字距标准 (em单位)"""
    TIGHTER = -0.05  # 更紧
    TIGHT = -0.025   # 紧
    NORMAL = 0       # 正常
    WIDE = 0.025     # 宽
    WIDER = 0.05     # 更宽
    WIDEST = 0.1     # 最宽


class FontFamily:
    """字体家族
    
    按照优先级提供多语言回退字体。
    """
    
    # 主字体 - 优先使用Inter (2026流行的现代字体)
    PRIMARY = [
        "Inter",
        "SF Pro Display",      # macOS
        "Segoe UI",            # Windows 11
        "-apple-system",       # macOS
        "BlinkMacSystemFont",  # macOS
        "Helvetica Neue",      # macOS
        "Arial",               # 通用
        "sans-serif"           # 回退
    ]
    
    # 单等宽字体 - 用于代码、数字
    MONOSPACE = [
        "JetBrains Mono",
        "Fira Code",
        "SF Mono",             # macOS
        "Cascadia Code",       # Windows
        "Menlo",               # macOS
        "Monaco",              # macOS
        "Consolas",            # Windows
        "Courier New",         # 通用
        "monospace"            # 回退
    ]
    
    # 中文字体回退
    CJK = [
        "PingFang SC",         # macOS 简中
        "Microsoft YaHei UI",  # Windows 简中
        "Microsoft YaHei",     # Windows 简中
        "Noto Sans CJK SC",    # Linux 简中
        "Source Han Sans SC",  # 思源黑体
        "SimHei",              # Windows 简中
        "sans-serif"           # 回退
    ]
    
    # 结合西文+中文
    COMBINED = PRIMARY + CJK


class Typography:
    """字体系统管理器
    
    提供统一的字体配置和获取方法。
    """
    
    def __init__(self):
        """初始化字体系统"""
        self._system = self._detect_system()
    
    @staticmethod
    def _detect_system() -> str:
        """检测操作系统
        
        Returns:
            系统类型: 'windows', 'mac', 'linux'
        """
        system = platform.system().lower()
        if 'darwin' in system:
            return 'mac'
        elif 'win' in system:
            return 'windows'
        else:
            return 'linux'
    
    def get_font_family(
        self,
        monospace: bool = False,
        include_cjk: bool = True
    ) -> str:
        """获取字体家族字符串
        
        Args:
            monospace: 是否使用等宽字体
            include_cjk: 是否包含中文字体
            
        Returns:
            字体家族字符串 (逗号分隔)
        """
        if monospace:
            fonts = FontFamily.MONOSPACE.copy()
        elif include_cjk:
            fonts = FontFamily.COMBINED.copy()
        else:
            fonts = FontFamily.PRIMARY.copy()
        
        return ", ".join(fonts)
    
    def get_primary_font(self) -> str:
        """获取主要字体名称
        
        根据操作系统返回最佳可用字体。
        
        Returns:
            字体名称
        """
        if self._system == 'mac':
            return "SF Pro Display"
        elif self._system == 'windows':
            return "Segoe UI"
        else:
            return "Inter"
    
    def get_monospace_font(self) -> str:
        """获取等宽字体名称
        
        Returns:
            等宽字体名称
        """
        if self._system == 'mac':
            return "SF Mono"
        elif self._system == 'windows':
            return "Cascadia Code"
        else:
            return "JetBrains Mono"
    
    @staticmethod
    def get_font_config(
        size: FontSize = FontSize.BASE,
        weight: FontWeight = FontWeight.REGULAR,
        line_height: Optional[LineHeight] = None
    ) -> dict:
        """获取字体配置字典
        
        Args:
            size: 字号
            weight: 字重
            line_height: 行高
            
        Returns:
            字体配置字典 (包含 size, weight 等)
        """
        config = {
            'size': size.value,
            'weight': weight.value,
        }
        
        if line_height:
            config['line_height'] = line_height.value
        
        return config
    
    def create_font_tuple(
        self,
        size: FontSize = FontSize.BASE,
        weight: FontWeight = FontWeight.REGULAR,
        monospace: bool = False
    ) -> Tuple[str, int, str]:
        """创建Tkinter字体元组
        
        Args:
            size: 字号
            weight: 字重
            monospace: 是否使用等宽字体
            
        Returns:
            (font_family, size, weight_str)
        """
        if monospace:
            font_family = self.get_monospace_font()
        else:
            font_family = self.get_primary_font()
        
        # 映射字重到Tkinter字重字符串
        weight_map = {
            FontWeight.THIN: "normal",
            FontWeight.EXTRA_LIGHT: "normal",
            FontWeight.LIGHT: "normal",
            FontWeight.REGULAR: "normal",
            FontWeight.MEDIUM: "normal",
            FontWeight.SEMI_BOLD: "bold",
            FontWeight.BOLD: "bold",
            FontWeight.EXTRA_BOLD: "bold",
            FontWeight.BLACK: "bold",
        }
        
        weight_str = weight_map.get(weight, "normal")
        
        return (font_family, size.value, weight_str)


# 全局字体系统实例
_typography = Typography()


# 便捷函数
def get_font(
    size: FontSize = FontSize.BASE,
    weight: FontWeight = FontWeight.REGULAR,
    monospace: bool = False
) -> Tuple[str, int, str]:
    """快速获取字体
    
    Args:
        size: 字号
        weight: 字重
        monospace: 是否等宽
        
    Returns:
        字体元组
    """
    return _typography.create_font_tuple(size, weight, monospace)


def get_font_family(monospace: bool = False, include_cjk: bool = True) -> str:
    """快速获取字体家族
    
    Args:
        monospace: 是否等宽
        include_cjk: 是否包含中文
        
    Returns:
        字体家族字符串
    """
    return _typography.get_font_family(monospace, include_cjk)


# 预定义字体配置 - 常用组合
class TextStyles:
    """预定义文本样式"""
    
    # 标题
    HEADING_1 = (FontSize.XXXL, FontWeight.BOLD)
    HEADING_2 = (FontSize.XXL, FontWeight.BOLD)
    HEADING_3 = (FontSize.XL, FontWeight.SEMI_BOLD)
    HEADING_4 = (FontSize.LG, FontWeight.SEMI_BOLD)
    
    # 正文
    BODY_LARGE = (FontSize.MD, FontWeight.REGULAR)
    BODY = (FontSize.BASE, FontWeight.REGULAR)
    BODY_SMALL = (FontSize.SM, FontWeight.REGULAR)
    
    # 标签
    LABEL_LARGE = (FontSize.MD, FontWeight.MEDIUM)
    LABEL = (FontSize.BASE, FontWeight.MEDIUM)
    LABEL_SMALL = (FontSize.SM, FontWeight.MEDIUM)
    
    # 按钮
    BUTTON_LARGE = (FontSize.MD, FontWeight.SEMI_BOLD)
    BUTTON = (FontSize.BASE, FontWeight.SEMI_BOLD)
    BUTTON_SMALL = (FontSize.SM, FontWeight.SEMI_BOLD)
    
    # 辅助文本
    CAPTION = (FontSize.SM, FontWeight.REGULAR)
    OVERLINE = (FontSize.XS, FontWeight.MEDIUM)
    
    # 代码/等宽
    CODE_LARGE = (FontSize.MD, FontWeight.REGULAR)
    CODE = (FontSize.BASE, FontWeight.REGULAR)
    CODE_SMALL = (FontSize.SM, FontWeight.REGULAR)


def get_text_style(style: Tuple[FontSize, FontWeight], monospace: bool = False) -> Tuple[str, int, str]:
    """根据预定义样式获取字体
    
    Args:
        style: 预定义样式 (来自 TextStyles)
        monospace: 是否使用等宽字体
        
    Returns:
        字体元组
    """
    size, weight = style
    return get_font(size, weight, monospace)


class ChineseFonts:
    """中文字体配置 - 支持Windows系统

    提供 Windows 环境下最佳中文字体检测和回退机制。
    与 FontFamily.CJK / Typography 互补：
    - ChineseFonts 通过 tkinter.font.families() 实时检测可用字体
    - Typography 提供跨平台的字体家族字符串
    """
    CHINESE_FONT_FAMILIES = [
        'Microsoft YaHei UI', 'Microsoft YaHei', 'SimHei',
        'SimSun', 'NSimSun', 'KaiTi', 'FangSong', 'Arial',
    ]
    SIZE_TITLE = 24
    SIZE_HEADING = 18
    SIZE_SUBHEADING = 16
    SIZE_NORMAL = 14
    SIZE_SMALL = 12
    SIZE_TINY = 11
    _detected_font = None

    @classmethod
    def get_best_font(cls) -> str:
        """检测并返回最佳可用中文字体"""
        if cls._detected_font:
            return cls._detected_font
        try:
            import tkinter as tk
            from tkinter import font as tkfont
            temp_root = tk.Tk()
            temp_root.withdraw()
            available_fonts = set(tkfont.families())
            temp_root.destroy()
            for font_name in cls.CHINESE_FONT_FAMILIES:
                if font_name in available_fonts:
                    cls._detected_font = font_name
                    return font_name
        except Exception:
            pass
        cls._detected_font = 'Microsoft YaHei UI'
        return cls._detected_font


# 使用示例文档字符串
"""使r
使用示例:

from .typography import (
    get_font, 
    get_text_style, 
    TextStyles, 
    FontSize, 
    FontWeight
)

# 方式1: 直接获取字体
heading_font = get_font(FontSize.XXL, FontWeight.BOLD)
body_font = get_font(FontSize.BASE, FontWeight.REGULAR)
code_font = get_font(FontSize.BASE, FontWeight.REGULAR, monospace=True)

# 方式2: 使用预定义样式
h1_font = get_text_style(TextStyles.HEADING_1)
body_font = get_text_style(TextStyles.BODY)
button_font = get_text_style(TextStyles.BUTTON)

# 在Tkinter/CustomTkinter中使用
label = ctk.CTkLabel(
    master,
    text="标题",
    font=get_text_style(TextStyles.HEADING_1)
)

button = ctk.CTkButton(
    master,
    text="按钮",
    font=get_text_style(TextStyles.BUTTON)
)
"""
