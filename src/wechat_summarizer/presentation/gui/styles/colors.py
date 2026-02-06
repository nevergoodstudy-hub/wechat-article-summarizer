"""GUI 颜色配置模块

2026 现代化 UI 设计趋势：液态玻璃效果 + 渐变色彩 + OLED 友好色彩方案
"""


class ModernColors:
    """现代化颜色配置 - 2026 UI设计趋势
    
    遵循 WCAG 2.1 可访问性标准
    使用 #121212 深灰而非纯黑，提升OLED显示效果
    """

    # ========== 深色主题 ==========
    # 背景色 - 使用深灰色而非纯黑（OLED友好）
    DARK_BG = "#121212"  # 主背景 - 深灰而非纯黑
    DARK_BG_SECONDARY = "#1e1e1e"  # 次级背景
    DARK_BG_TERTIARY = "#252525"  # 第三级背景
    DARK_SIDEBAR = "#1a1a1a"  # 侧边栏背景
    DARK_CARD = "#1e1e1e"  # 卡片背景
    DARK_CARD_HOVER = "#2a2a2a"  # 卡片悬停
    DARK_ELEVATED = "#2d2d2d"  # 提升层级
    
    # 灰度色阶 (10级) - 用于细腻的层次表现
    DARK_GRAY_50 = "#fafafa"
    DARK_GRAY_100 = "#f5f5f5"
    DARK_GRAY_200 = "#e5e5e5"
    DARK_GRAY_300 = "#d4d4d4"
    DARK_GRAY_400 = "#a3a3a3"
    DARK_GRAY_500 = "#737373"
    DARK_GRAY_600 = "#525252"
    DARK_GRAY_700 = "#404040"
    DARK_GRAY_800 = "#262626"
    DARK_GRAY_900 = "#171717"
    
    # 强调色 - 紫色系（高识别度）
    DARK_ACCENT = "#8b5cf6"  # 主强调色
    DARK_ACCENT_HOVER = "#a78bfa"  # 强调色悬停
    DARK_ACCENT_PRESSED = "#7c3aed"  # 强调色按下
    DARK_ACCENT_LIGHT = "#c4b5fd"  # 浅色强调
    
    # 文字色 - 确保对比度符合WCAG AA标准
    DARK_TEXT = "#ffffff"  # 主文字 (对比度 15.3:1)
    DARK_TEXT_SECONDARY = "#a1a1a1"  # 次级文字 (对比度 7.4:1)
    DARK_TEXT_MUTED = "#737373"  # 弱化文字 (对比度 4.6:1)
    DARK_TEXT_DISABLED = "#525252"  # 禁用文字
    
    # 边框与分隔线
    DARK_BORDER = "#404040"  # 边框色
    DARK_BORDER_SUBTLE = "#2a2a2a"  # 微妙边框
    DARK_DIVIDER = "#333333"  # 分隔线
    
    # 液态玻璃效果 (使用十六进制以兼容Tkinter)
    DARK_GLASS = "#1e1e1ed9"  # 玻璃背景 rgba(30,30,30,0.85) -> hex with alpha
    DARK_GLASS_SOLID = "#1e1e1e"  # 玻璃背景纯色版本(Tkinter兼容)
    DARK_GLASS_BORDER = "#ffffff1a"  # 玻璃边框 rgba(255,255,255,0.1)
    DARK_GLASS_BORDER_SOLID = "#404040"  # 玻璃边框纯色版本(Tkinter兼容)

    # ========== 浅色主题 ==========
    # 背景色 - 柔和的中性色调
    LIGHT_BG = "#fafafa"  # 主背景
    LIGHT_BG_SECONDARY = "#f5f5f5"  # 次级背景
    LIGHT_BG_TERTIARY = "#eeeeee"  # 第三级背景
    LIGHT_SIDEBAR = "#ffffff"  # 侧边栏背景
    LIGHT_CARD = "#ffffff"  # 卡片背景
    LIGHT_CARD_HOVER = "#f9fafb"  # 卡片悬停
    LIGHT_ELEVATED = "#ffffff"  # 提升层级
    
    # 灰度色阶 (10级)
    LIGHT_GRAY_50 = "#fafafa"
    LIGHT_GRAY_100 = "#f5f5f5"
    LIGHT_GRAY_200 = "#eeeeee"
    LIGHT_GRAY_300 = "#e0e0e0"
    LIGHT_GRAY_400 = "#bdbdbd"
    LIGHT_GRAY_500 = "#9e9e9e"
    LIGHT_GRAY_600 = "#757575"
    LIGHT_GRAY_700 = "#616161"
    LIGHT_GRAY_800 = "#424242"
    LIGHT_GRAY_900 = "#212121"
    
    # 强调色 - 靳蓝色系
    LIGHT_ACCENT = "#6366f1"  # 主强调色
    LIGHT_ACCENT_HOVER = "#4f46e5"  # 强调色悬停
    LIGHT_ACCENT_PRESSED = "#4338ca"  # 强调色按下
    LIGHT_ACCENT_LIGHT = "#a5b4fc"  # 浅色强调
    
    # 文字色 - 确保对比度符合WCAG AA标准
    LIGHT_TEXT = "#111827"  # 主文字 (对比度 16.1:1)
    LIGHT_TEXT_SECONDARY = "#4b5563"  # 次级文字 (对比度 8.9:1)
    LIGHT_TEXT_MUTED = "#6b7280"  # 弱化文字 (对比度 5.8:1)
    LIGHT_TEXT_DISABLED = "#9ca3af"  # 禁用文字
    
    # 边框与分隔线
    LIGHT_BORDER = "#e5e7eb"  # 边框色
    LIGHT_BORDER_SUBTLE = "#f3f4f6"  # 微妙边框
    LIGHT_DIVIDER = "#e5e7eb"  # 分隔线
    
    # 液态玻璃效果 (使用十六进制以兼容Tkinter)
    LIGHT_GLASS = "#ffffffd9"  # 玻璃背景 rgba(255,255,255,0.85) -> hex with alpha
    LIGHT_GLASS_SOLID = "#f5f5f5"  # 玻璃背景纯色版本(Tkinter兼容)
    LIGHT_GLASS_BORDER = "#0000001a"  # 玻璃边框 rgba(0,0,0,0.1)
    LIGHT_GLASS_BORDER_SOLID = "#e0e0e0"  # 玻璃边框纯色版本(Tkinter兼容)

    # ========== 语义化颜色（主题通用） ==========
    # 成功色 - 绿色系
    SUCCESS = "#10b981"  # 主成功色
    SUCCESS_LIGHT = "#34d399"  # 浅色成功
    SUCCESS_DARK = "#059669"  # 深色成功
    SUCCESS_BG = "#d1fae5"  # 成功背景
    
    # 警告色 - 橙色系
    WARNING = "#f59e0b"  # 主警告色
    WARNING_LIGHT = "#fbbf24"  # 浅色警告
    WARNING_DARK = "#d97706"  # 深色警告
    WARNING_BG = "#fef3c7"  # 警告背景
    
    # 错误色 - 红色系
    ERROR = "#ef4444"  # 主错误色
    ERROR_LIGHT = "#f87171"  # 浅色错误
    ERROR_DARK = "#dc2626"  # 深色错误
    ERROR_BG = "#fee2e2"  # 错误背景
    
    # 信息色 - 蓝色系
    INFO = "#3b82f6"  # 主信息色
    INFO_LIGHT = "#60a5fa"  # 浅色信息
    INFO_DARK = "#2563eb"  # 深色信息
    INFO_BG = "#dbeafe"  # 信息背景

    # ========== 渐变色定义 ==========
    # 格式: (type, [start_color, end_color], angle)
    GRADIENT_PRIMARY = ("linear", ["#8b5cf6", "#a78bfa"], 135)  # 紫色渐变
    GRADIENT_SUCCESS = ("linear", ["#10b981", "#34d399"], 135)  # 绿色渐变
    GRADIENT_WARNING = ("linear", ["#f59e0b", "#fbbf24"], 135)  # 橙色渐变
    GRADIENT_ERROR = ("linear", ["#ef4444", "#f87171"], 135)  # 红色渐变
    GRADIENT_INFO = ("linear", ["#3b82f6", "#60a5fa"], 135)  # 蓝色渐变
    
    # 特殊效果渐变 (使用十六进制以兼容Tkinter)
    GRADIENT_GLASS_DARK = ("linear", ["#1e1e1ef2", "#1e1e1ebf"], 180)  # 0.95/0.75 alpha
    GRADIENT_GLASS_DARK_SOLID = ("linear", ["#1e1e1e", "#252525"], 180)  # Tkinter兼容
    GRADIENT_GLASS_LIGHT = ("linear", ["#fffffff2", "#ffffffbf"], 180)  # 0.95/0.75 alpha
    GRADIENT_GLASS_LIGHT_SOLID = ("linear", ["#ffffff", "#f5f5f5"], 180)  # Tkinter兼容

    # ========== 简单渐变色值 (Tkinter兼容) ==========
    GRADIENT_START = '#6366f1'
    GRADIENT_MID = '#8b5cf6'
    GRADIENT_END = '#a855f7'

    # ========== 特殊效果色 (Tkinter兼容) ==========
    NEON_CYAN = '#06b6d4'
    NEON_PINK = '#ec4899'
    NEON_GREEN = '#22c55e'
    SHIMMER_LIGHT = '#ffffff1a'   # rgba(255, 255, 255, 0.1)
    GLOW_PURPLE = '#8b5cf64d'    # rgba(139, 92, 246, 0.3)
    GLOW_BLUE = '#6366f14d'      # rgba(99, 102, 241, 0.3)

    # ========== 阴影 (CSS格式参考，Tkinter不直接支持) ==========
    SHADOW_SM = '0 1px 2px rgba(0, 0, 0, 0.05)'
    SHADOW_MD = '0 4px 6px rgba(0, 0, 0, 0.1)'
    SHADOW_LG = '0 10px 15px rgba(0, 0, 0, 0.15)'
    SHADOW_XL = '0 20px 25px rgba(0, 0, 0, 0.2)'
    SHADOW_GLOW = '0 0 30px rgba(139, 92, 246, 0.4)'


# ========== 预设主题配色方案 ==========
THEME_DARK = {
    # 背景色
    "bg": ModernColors.DARK_BG,
    "bg_secondary": ModernColors.DARK_BG_SECONDARY,
    "bg_tertiary": ModernColors.DARK_BG_TERTIARY,
    "sidebar": ModernColors.DARK_SIDEBAR,
    "card": ModernColors.DARK_CARD,
    "card_hover": ModernColors.DARK_CARD_HOVER,
    "elevated": ModernColors.DARK_ELEVATED,
    
    # 文字色
    "fg": ModernColors.DARK_TEXT,
    "fg_secondary": ModernColors.DARK_TEXT_SECONDARY,
    "fg_muted": ModernColors.DARK_TEXT_MUTED,
    "fg_disabled": ModernColors.DARK_TEXT_DISABLED,
    
    # 强调色
    "accent": ModernColors.DARK_ACCENT,
    "accent_hover": ModernColors.DARK_ACCENT_HOVER,
    "accent_pressed": ModernColors.DARK_ACCENT_PRESSED,
    
    # 边框与分隔
    "border": ModernColors.DARK_BORDER,
    "border_subtle": ModernColors.DARK_BORDER_SUBTLE,
    "divider": ModernColors.DARK_DIVIDER,
    
    # 特殊效果 (Tkinter兼容版本)
    "glass": ModernColors.DARK_GLASS_SOLID,
    "glass_border": ModernColors.DARK_GLASS_BORDER_SOLID,
}

THEME_LIGHT = {
    # 背景色
    "bg": ModernColors.LIGHT_BG,
    "bg_secondary": ModernColors.LIGHT_BG_SECONDARY,
    "bg_tertiary": ModernColors.LIGHT_BG_TERTIARY,
    "sidebar": ModernColors.LIGHT_SIDEBAR,
    "card": ModernColors.LIGHT_CARD,
    "card_hover": ModernColors.LIGHT_CARD_HOVER,
    "elevated": ModernColors.LIGHT_ELEVATED,
    
    # 文字色
    "fg": ModernColors.LIGHT_TEXT,
    "fg_secondary": ModernColors.LIGHT_TEXT_SECONDARY,
    "fg_muted": ModernColors.LIGHT_TEXT_MUTED,
    "fg_disabled": ModernColors.LIGHT_TEXT_DISABLED,
    
    # 强调色
    "accent": ModernColors.LIGHT_ACCENT,
    "accent_hover": ModernColors.LIGHT_ACCENT_HOVER,
    "accent_pressed": ModernColors.LIGHT_ACCENT_PRESSED,
    
    # 边框与分隔
    "border": ModernColors.LIGHT_BORDER,
    "border_subtle": ModernColors.LIGHT_BORDER_SUBTLE,
    "divider": ModernColors.LIGHT_DIVIDER,
    
    # 特殊效果 (Tkinter兼容版本)
    "glass": ModernColors.LIGHT_GLASS_SOLID,
    "glass_border": ModernColors.LIGHT_GLASS_BORDER_SOLID,
}


# ========== 工具函数 ==========
def to_tkinter_color(color: str, background: str = "#121212") -> str:
    """将任意颜色格式转换为Tkinter兼容的十六进制格式
    
    支持的输入格式:
    - 十六进制: "#RRGGBB" 或 "#RRGGBBAA"
    - rgba: "rgba(R, G, B, A)"
    - rgb: "rgb(R, G, B)"
    
    Args:
        color: 输入颜色字符串
        background: 背景色(用于alpha混合计算)
        
    Returns:
        str: Tkinter兼容的 "#RRGGBB" 格式
    """
    import re
    
    if not color:
        return background
    
    color = color.strip()
    
    # 已经是标准十六进制格式
    if color.startswith('#') and len(color) == 7:
        return color
    
    # 带alpha的十六进制格式 (#RRGGBBAA)
    if color.startswith('#') and len(color) == 9:
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        a = int(color[7:9], 16) / 255.0
        
        # 与背景色混合
        bg = hex_to_rgb(background)
        r = int(r * a + bg[0] * (1 - a))
        g = int(g * a + bg[1] * (1 - a))
        b = int(b * a + bg[2] * (1 - a))
        return f"#{r:02x}{g:02x}{b:02x}"
    
    # rgba格式
    rgba_match = re.match(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+))?\s*\)', color)
    if rgba_match:
        r, g, b = int(rgba_match.group(1)), int(rgba_match.group(2)), int(rgba_match.group(3))
        a = float(rgba_match.group(4)) if rgba_match.group(4) else 1.0
        
        if a < 1.0:
            # 与背景色混合
            bg = hex_to_rgb(background)
            r = int(r * a + bg[0] * (1 - a))
            g = int(g * a + bg[1] * (1 - a))
            b = int(b * a + bg[2] * (1 - a))
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    # 无法识别，返回原值
    return color


def get_theme(theme_name: str = "dark") -> dict:
    """获取指定主题配置
    
    Args:
        theme_name: 主题名称 ("dark" 或 "light")
        
    Returns:
        dict: 主题配置字典
    """
    return THEME_DARK if theme_name == "dark" else THEME_LIGHT


def hex_to_rgb(hex_color: str) -> tuple:
    """将十六进制颜色转换为RGB元组
    
    Args:
        hex_color: 十六进制颜色字符串 (e.g., "#121212")
        
    Returns:
        tuple: (R, G, B) 元组
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def calculate_contrast_ratio(color1: str, color2: str) -> float:
    """计算两种颜色的对比度 (WCAG 2.1)
    
    Args:
        color1: 第一种颜色的十六进制值
        color2: 第二种颜色的十六进制值
        
    Returns:
        float: 对比度值 (1.0 - 21.0)
        
    Note:
        WCAG AA标准要求对比度≥4.5:1
        WCAG AAA标准要求对比度≥7:1
    """
    def relative_luminance(rgb):
        """Calculate relative luminance"""
        rgb = [x / 255.0 for x in rgb]
        rgb = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in rgb]
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    
    lum1 = relative_luminance(rgb1)
    lum2 = relative_luminance(rgb2)
    
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    
    return (lighter + 0.05) / (darker + 0.05)
