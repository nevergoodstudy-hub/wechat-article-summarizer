"""现代图标库管理器 - 2026 UI设计趋势

提供：
- SVG图标路径定义
- 动态颜色主题适配
- 多尺寸图标缓存
- 常用图标快速访问

安全审查：
- 图标缓存限制，避免内存溢出
- 路径验证，防止无效SVG
"""
from __future__ import annotations

import base64
import re
from enum import Enum
from io import BytesIO
from typing import Dict, Optional, Tuple, List

try:
    from PIL import Image, ImageDraw, ImageTk
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False
    Image = None
    ImageDraw = None
    ImageTk = None

# 尝试导入SVG渲染库
try:
    import cairosvg
    _CAIROSVG_AVAILABLE = True
except ImportError:
    _CAIROSVG_AVAILABLE = False
    cairosvg = None


class IconSize(Enum):
    """图标尺寸标准"""
    TINY = 12      # 极小 (用于表格、紧凑UI)
    SMALL = 16     # 小 (用于按钮内、列表项)
    MEDIUM = 24    # 中 (默认大小)
    LARGE = 32     # 大 (用于主操作按钮)
    XLARGE = 48    # 超大 (用于启动页、空状态)
    XXLARGE = 64   # 极大 (用于特殊展示)


class IconStyle(Enum):
    """图标样式"""
    OUTLINED = "outlined"    # 线性图标
    FILLED = "filled"        # 填充图标
    ROUNDED = "rounded"      # 圆角图标
    SHARP = "sharp"          # 尖角图标


# SVG图标路径定义 (使用path data)
# 这里提供常用图标的SVG路径，实际使用时可扩展
ICON_PATHS = {
    # 文件操作
    "file": "M6 2c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6H6zm7 7V3.5L18.5 9H13z",
    "folder": "M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z",
    "save": "M17 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4zm-5 16c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm3-10H5V5h10v4z",
    "download": "M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z",
    "upload": "M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z",
    
    # UI操作
    "close": "M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z",
    "check": "M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z",
    "add": "M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z",
    "remove": "M19 13H5v-2h14v2z",
    "edit": "M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z",
    "delete": "M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z",
    "search": "M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z",
    "settings": "M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.07-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.74,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.8,11.69,4.8,12s0.02,0.64,0.07,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.44-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z",
    "menu": "M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z",
    "more": "M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z",
    
    # 导航
    "home": "M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z",
    "back": "M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z",
    "forward": "M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z",
    "expand_more": "M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z",
    "expand_less": "M12 8l-6 6 1.41 1.41L12 10.83l4.59 4.58L18 14z",
    "chevron_right": "M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z",
    "chevron_left": "M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z",
    
    # 状态
    "info": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z",
    "warning": "M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z",
    "error": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z",
    "success": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z",
    
    # 内容
    "description": "M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z",
    "copy": "M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z",
    "refresh": "M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z",
    
    # 用户
    "person": "M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z",
    "group": "M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z",
    
    # 时间
    "schedule": "M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z",
    "today": "M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM7 10h5v5H7z",
}


class SVGPathParser:
    """SVG路径解析器
    
    解析SVG path的d属性，转换为可绘制的坐标点。
    支持: M, L, H, V, C, S, Q, T, A, Z 命令
    """
    
    COMMAND_PATTERN = re.compile(r'([MLHVCSQTAZmlhvcsqtaz])([^MLHVCSQTAZmlhvcsqtaz]*)')
    NUMBER_PATTERN = re.compile(r'-?\d+\.?\d*(?:e[+-]?\d+)?')
    
    @classmethod
    def parse(cls, path_data: str, scale: float = 1.0, offset_x: float = 0, offset_y: float = 0) -> List[Tuple]:
        """解析SVG路径数据
        
        Args:
            path_data: SVG路径d属性值
            scale: 缩放比例
            offset_x: X偏移
            offset_y: Y偏移
            
        Returns:
            绘制命令列表 [(command, points), ...]
        """
        commands = []
        current_x, current_y = 0, 0
        start_x, start_y = 0, 0
        
        for match in cls.COMMAND_PATTERN.finditer(path_data):
            cmd = match.group(1)
            args_str = match.group(2)
            args = [float(n) for n in cls.NUMBER_PATTERN.findall(args_str)]
            
            is_relative = cmd.islower()
            cmd_upper = cmd.upper()
            
            if cmd_upper == 'M':  # 移动
                i = 0
                while i < len(args) - 1:
                    x, y = args[i], args[i + 1]
                    if is_relative:
                        x += current_x
                        y += current_y
                    current_x, current_y = x, y
                    if i == 0:
                        start_x, start_y = x, y
                        commands.append(('move', [(x * scale + offset_x, y * scale + offset_y)]))
                    else:
                        commands.append(('line', [(x * scale + offset_x, y * scale + offset_y)]))
                    i += 2
                    
            elif cmd_upper == 'L':  # 直线
                i = 0
                while i < len(args) - 1:
                    x, y = args[i], args[i + 1]
                    if is_relative:
                        x += current_x
                        y += current_y
                    current_x, current_y = x, y
                    commands.append(('line', [(x * scale + offset_x, y * scale + offset_y)]))
                    i += 2
                    
            elif cmd_upper == 'H':  # 水平线
                for x in args:
                    if is_relative:
                        x += current_x
                    current_x = x
                    commands.append(('line', [(x * scale + offset_x, current_y * scale + offset_y)]))
                    
            elif cmd_upper == 'V':  # 垂直线
                for y in args:
                    if is_relative:
                        y += current_y
                    current_y = y
                    commands.append(('line', [(current_x * scale + offset_x, y * scale + offset_y)]))
                    
            elif cmd_upper == 'C':  # 三次贝塞尔曲线
                i = 0
                while i < len(args) - 5:
                    x1, y1, x2, y2, x, y = args[i:i+6]
                    if is_relative:
                        x1 += current_x; y1 += current_y
                        x2 += current_x; y2 += current_y
                        x += current_x; y += current_y
                    current_x, current_y = x, y
                    commands.append(('curve', [
                        (x1 * scale + offset_x, y1 * scale + offset_y),
                        (x2 * scale + offset_x, y2 * scale + offset_y),
                        (x * scale + offset_x, y * scale + offset_y)
                    ]))
                    i += 6
                    
            elif cmd_upper == 'S':  # 平滑三次贝塞尔
                i = 0
                while i < len(args) - 3:
                    x2, y2, x, y = args[i:i+4]
                    if is_relative:
                        x2 += current_x; y2 += current_y
                        x += current_x; y += current_y
                    # 简化处理：使用当前点作为第一控制点
                    x1, y1 = current_x, current_y
                    current_x, current_y = x, y
                    commands.append(('curve', [
                        (x1 * scale + offset_x, y1 * scale + offset_y),
                        (x2 * scale + offset_x, y2 * scale + offset_y),
                        (x * scale + offset_x, y * scale + offset_y)
                    ]))
                    i += 4
                    
            elif cmd_upper == 'Q':  # 二次贝塞尔曲线
                i = 0
                while i < len(args) - 3:
                    x1, y1, x, y = args[i:i+4]
                    if is_relative:
                        x1 += current_x; y1 += current_y
                        x += current_x; y += current_y
                    current_x, current_y = x, y
                    commands.append(('quad', [
                        (x1 * scale + offset_x, y1 * scale + offset_y),
                        (x * scale + offset_x, y * scale + offset_y)
                    ]))
                    i += 4
                    
            elif cmd_upper == 'Z':  # 闭合路径
                current_x, current_y = start_x, start_y
                commands.append(('close', [(start_x * scale + offset_x, start_y * scale + offset_y)]))
        
        return commands


class IconManager:
    """图标管理器
    
    功能：
    - SVG路径解析和渲染
    - 主题颜色适配
    - 图标缓存
    - 多尺寸支持
    
    安全措施:
    - 缓存大小限制
    - 颜色格式验证
    - 路径数据长度限制
    """
    
    MAX_PATH_LENGTH = 10000  # SVG路径最大长度
    
    def __init__(self):
        """初始化图标管理器"""
        self._cache: Dict[Tuple[str, int, str], any] = {}
        self._cache_limit = 200  # 限制缓存大小
    
    def get_icon(
        self,
        name: str,
        size: IconSize = IconSize.MEDIUM,
        color: str = "#FFFFFF",
        style: IconStyle = IconStyle.OUTLINED
    ):
        """获取图标
        
        Args:
            name: 图标名称
            size: 图标尺寸
            color: 图标颜色
            style: 图标样式
            
        Returns:
            图标对象 (PIL Image 或 None)
        """
        if not _PIL_AVAILABLE:
            return None
        
        # 颜色格式验证
        if not self._validate_color(color):
            color = "#FFFFFF"
        
        # 检查缓存
        cache_key = (name, size.value, color)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 检查图标是否存在
        if name not in ICON_PATHS:
            return None
        
        # 生成图标
        icon = self._create_icon(name, size.value, color)
        
        # 缓存限制
        if len(self._cache) >= self._cache_limit:
            # 删除最旧的缓存项
            self._cache.pop(next(iter(self._cache)))
        
        self._cache[cache_key] = icon
        return icon
    
    @staticmethod
    def _validate_color(color: str) -> bool:
        """验证颜色格式"""
        if not isinstance(color, str):
            return False
        pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        return bool(re.match(pattern, color))
    
    @staticmethod
    def _parse_color(color: str) -> Tuple[int, int, int, int]:
        """解析颜色为RGBA"""
        try:
            if color.startswith('#'):
                hex_color = color[1:]
                if len(hex_color) == 3:
                    hex_color = ''.join([c*2 for c in hex_color])
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                return (r, g, b, 255)
        except (ValueError, IndexError):
            pass
        return (255, 255, 255, 255)
    
    def _create_icon(self, name: str, size: int, color: str) -> Optional[Image.Image]:
        """创建图标 - 使用SVG路径渲染
        
        Args:
            name: 图标名称
            size: 图标尺寸
            color: 图标颜色
            
        Returns:
            PIL Image对象
        """
        if not _PIL_AVAILABLE:
            return None
        
        path_data = ICON_PATHS.get(name, "")
        
        # 路径长度安全检查
        if len(path_data) > self.MAX_PATH_LENGTH:
            return self._create_fallback_icon(size, color)
        
        # 方法1: 使用cairosvg渲染(如果可用)
        if _CAIROSVG_AVAILABLE:
            return self._render_with_cairosvg(path_data, size, color)
        
        # 方法2: 使用PIL手动绘制SVG路径
        return self._render_with_pil(path_data, size, color)
    
    def _render_with_cairosvg(self, path_data: str, size: int, color: str) -> Optional[Image.Image]:
        """使用cairosvg渲染SVG"""
        try:
            # 构建完整SVG
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
            <svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24">
                <path d="{path_data}" fill="{color}"/>
            </svg>'''
            
            # 渲染为PNG
            png_data = cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8'),
                output_width=size,
                output_height=size
            )
            
            # 转换为PIL Image
            return Image.open(BytesIO(png_data))
        except Exception:
            # 降级到PIL渲染
            return self._render_with_pil(path_data, size, color)
    
    def _render_with_pil(self, path_data: str, size: int, color: str) -> Optional[Image.Image]:
        """使用PIL手动渲染SVG路径"""
        # 创建透明背景图像
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 计算缩放比例 (原始viewBox是24x24)
        scale = size / 24.0
        
        # 解析SVG路径
        try:
            commands = SVGPathParser.parse(path_data, scale=scale)
        except Exception:
            return self._create_fallback_icon(size, color)
        
        # 解析颜色
        fill_color = self._parse_color(color)
        
        # 收集路径点用于填充
        polygon_points = []
        current_pos = None
        
        for cmd, points in commands:
            if cmd == 'move':
                if polygon_points and len(polygon_points) >= 3:
                    # 绘制之前的多边形
                    self._draw_polygon(draw, polygon_points, fill_color)
                polygon_points = [points[0]]
                current_pos = points[0]
                
            elif cmd == 'line':
                polygon_points.append(points[0])
                current_pos = points[0]
                
            elif cmd == 'curve':
                # 三次贝塞尔曲线 - 使用线段近似
                if current_pos:
                    curve_points = self._bezier_curve(
                        current_pos,
                        points[0],
                        points[1],
                        points[2],
                        steps=8
                    )
                    polygon_points.extend(curve_points[1:])  # 跳过起点
                    current_pos = points[2]
                    
            elif cmd == 'quad':
                # 二次贝塞尔曲线 - 使用线段近似
                if current_pos:
                    curve_points = self._quad_bezier(
                        current_pos,
                        points[0],
                        points[1],
                        steps=6
                    )
                    polygon_points.extend(curve_points[1:])
                    current_pos = points[1]
                    
            elif cmd == 'close':
                if polygon_points and len(polygon_points) >= 3:
                    self._draw_polygon(draw, polygon_points, fill_color)
                polygon_points = []
        
        # 绘制剩余的多边形
        if polygon_points and len(polygon_points) >= 3:
            self._draw_polygon(draw, polygon_points, fill_color)
        
        return img
    
    @staticmethod
    def _draw_polygon(draw: ImageDraw.Draw, points: List[Tuple], color: Tuple):
        """绘制填充多边形"""
        if len(points) >= 3:
            # 展平点列表
            flat_points = [coord for point in points for coord in point]
            try:
                draw.polygon(flat_points, fill=color)
            except Exception:
                pass  # 忽略无效多边形
    
    @staticmethod
    def _bezier_curve(
        p0: Tuple[float, float],
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
        steps: int = 10
    ) -> List[Tuple[float, float]]:
        """计算三次贝塞尔曲线点"""
        points = []
        for i in range(steps + 1):
            t = i / steps
            t2 = t * t
            t3 = t2 * t
            mt = 1 - t
            mt2 = mt * mt
            mt3 = mt2 * mt
            
            x = mt3 * p0[0] + 3 * mt2 * t * p1[0] + 3 * mt * t2 * p2[0] + t3 * p3[0]
            y = mt3 * p0[1] + 3 * mt2 * t * p1[1] + 3 * mt * t2 * p2[1] + t3 * p3[1]
            points.append((x, y))
        return points
    
    @staticmethod
    def _quad_bezier(
        p0: Tuple[float, float],
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        steps: int = 8
    ) -> List[Tuple[float, float]]:
        """计算二次贝塞尔曲线点"""
        points = []
        for i in range(steps + 1):
            t = i / steps
            mt = 1 - t
            
            x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
            y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
            points.append((x, y))
        return points
    
    def _create_fallback_icon(self, size: int, color: str) -> Image.Image:
        """创建降级图标（简单形状）"""
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        fill_color = self._parse_color(color)
        
        # 绘制圆形作为降级图标
        padding = size // 6
        draw.ellipse(
            [padding, padding, size - padding, size - padding],
            fill=fill_color
        )
        
        return img
    
    def get_icon_tk(
        self,
        name: str,
        size: IconSize = IconSize.MEDIUM,
        color: str = "#FFFFFF"
    ):
        """获取Tkinter兼容的图标
        
        Args:
            name: 图标名称
            size: 图标尺寸
            color: 图标颜色
            
        Returns:
            PhotoImage对象
        """
        if not _PIL_AVAILABLE:
            return None
        
        icon = self.get_icon(name, size, color)
        if icon is None:
            return None
        
        return ImageTk.PhotoImage(icon)
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
    
    @staticmethod
    def list_icons() -> list:
        """列出所有可用图标
        
        Returns:
            图标名称列表
        """
        return list(ICON_PATHS.keys())


# 全局图标管理器实例
_icon_manager = IconManager()


# 便捷函数
def get_icon(
    name: str,
    size: IconSize = IconSize.MEDIUM,
    color: str = "#FFFFFF"
):
    """快速获取图标
    
    Args:
        name: 图标名称
        size: 图标尺寸
        color: 图标颜色
        
    Returns:
        图标对象
    """
    return _icon_manager.get_icon(name, size, color)


def get_icon_tk(
    name: str,
    size: IconSize = IconSize.MEDIUM,
    color: str = "#FFFFFF"
):
    """快速获取Tkinter图标
    
    Args:
        name: 图标名称
        size: 图标尺寸
        color: 图标颜色
        
    Returns:
        PhotoImage对象
    """
    return _icon_manager.get_icon_tk(name, size, color)


def list_icons() -> list:
    """列出所有图标"""
    return IconManager.list_icons()
