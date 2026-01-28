"""知识图谱查看器组件

支持 GraphRAG 知识图谱的可视化展示。
使用 Canvas 绘制节点和边，支持交互操作。
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

from ..styles.colors import ModernColors

if TYPE_CHECKING:
    from ....application.ports.outbound import KnowledgeGraph

# 延迟导入 CTk
_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False
    ctk = None


@dataclass
class NodePosition:
    """节点位置"""

    x: float
    y: float
    vx: float = 0.0  # 速度 x
    vy: float = 0.0  # 速度 y


class GraphViewerComponent:
    """知识图谱查看器组件

    使用力导向布局算法可视化知识图谱。
    """

    def __init__(
        self,
        master: Any,
        width: int = 800,
        height: int = 600,
        theme: str = "dark",
    ) -> None:
        """初始化图谱查看器

        Args:
            master: 父组件
            width: 画布宽度
            height: 画布高度
            theme: 主题 ("dark" 或 "light")
        """
        if not _ctk_available:
            raise ImportError("需要安装 customtkinter: pip install customtkinter")

        self.master = master
        self.width = width
        self.height = height
        self.theme = theme

        # 节点和边数据
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: list[dict[str, Any]] = []
        self.node_positions: dict[str, NodePosition] = {}

        # 画布元素 ID
        self.node_items: dict[str, int] = {}
        self.edge_items: list[int] = []
        self.label_items: dict[str, int] = {}

        # 交互状态
        self.selected_node: str | None = None
        self.dragging: bool = False
        self.drag_node: str | None = None

        # 回调
        self.on_node_click: Callable[[str, dict], None] | None = None
        self.on_node_hover: Callable[[str, dict], None] | None = None

        # 创建界面
        self._create_widgets()

    def _create_widgets(self) -> None:
        """创建界面组件"""
        # 主框架
        self.frame = ctk.CTkFrame(self.master)

        # 工具栏
        self.toolbar = ctk.CTkFrame(self.frame, height=40)
        self.toolbar.pack(fill="x", padx=5, pady=5)

        # 缩放控件
        ctk.CTkLabel(self.toolbar, text="缩放:").pack(side="left", padx=5)
        self.zoom_slider = ctk.CTkSlider(
            self.toolbar,
            from_=0.5,
            to=2.0,
            number_of_steps=15,
            command=self._on_zoom_change,
        )
        self.zoom_slider.set(1.0)
        self.zoom_slider.pack(side="left", padx=5)

        # 重置布局按钮
        self.reset_btn = ctk.CTkButton(
            self.toolbar,
            text="重置布局",
            width=80,
            command=self._reset_layout,
        )
        self.reset_btn.pack(side="right", padx=5)

        # 统计标签
        self.stats_label = ctk.CTkLabel(
            self.toolbar,
            text="节点: 0 | 边: 0",
        )
        self.stats_label.pack(side="right", padx=20)

        # 画布
        bg_color = ModernColors.DARK_BG if self.theme == "dark" else ModernColors.LIGHT_BG
        self.canvas = ctk.CTkCanvas(
            self.frame,
            width=self.width,
            height=self.height,
            bg=bg_color,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)

        # 绑定事件
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)

    def pack(self, **kwargs: Any) -> None:
        """打包组件"""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """网格布局"""
        self.frame.grid(**kwargs)

    def load_knowledge_graph(self, kg: "KnowledgeGraph") -> None:
        """加载知识图谱

        Args:
            kg: 知识图谱对象
        """
        # 清空现有数据
        self.nodes.clear()
        self.edges.clear()
        self.node_positions.clear()

        # 加载节点
        for entity_id, entity in kg.entities.items():
            self.nodes[entity_id] = {
                "id": entity_id,
                "name": entity.name,
                "type": entity.type,
                "description": entity.description,
            }

        # 加载边
        for rel_id, rel in kg.relationships.items():
            self.edges.append({
                "id": rel_id,
                "source": rel.source_id,
                "target": rel.target_id,
                "type": rel.type,
            })

        # 初始化布局
        self._init_layout()
        self._update_stats()
        self._render()

    def load_from_dict(
        self,
        entities: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
    ) -> None:
        """从字典数据加载

        Args:
            entities: 实体列表
            relationships: 关系列表
        """
        self.nodes.clear()
        self.edges.clear()
        self.node_positions.clear()

        for entity in entities:
            entity_id = entity.get("id", entity.get("name"))
            self.nodes[entity_id] = {
                "id": entity_id,
                "name": entity.get("name", ""),
                "type": entity.get("type", ""),
                "description": entity.get("description", ""),
            }

        for rel in relationships:
            self.edges.append({
                "id": rel.get("id", f"{rel['source']}-{rel['target']}"),
                "source": rel.get("source_id", rel.get("source")),
                "target": rel.get("target_id", rel.get("target")),
                "type": rel.get("type", "相关"),
            })

        self._init_layout()
        self._update_stats()
        self._render()

    def _init_layout(self) -> None:
        """初始化节点布局（随机放置）"""
        cx, cy = self.width / 2, self.height / 2
        radius = min(self.width, self.height) * 0.35

        for i, node_id in enumerate(self.nodes.keys()):
            angle = 2 * math.pi * i / max(len(self.nodes), 1)
            x = cx + radius * math.cos(angle) + random.uniform(-50, 50)
            y = cy + radius * math.sin(angle) + random.uniform(-50, 50)
            self.node_positions[node_id] = NodePosition(x=x, y=y)

    def _force_directed_layout(self, iterations: int = 50) -> None:
        """力导向布局算法"""
        k = math.sqrt(self.width * self.height / max(len(self.nodes), 1))
        temp = self.width / 10

        for _ in range(iterations):
            # 斥力
            for v in self.nodes:
                pos_v = self.node_positions[v]
                pos_v.vx, pos_v.vy = 0, 0

                for u in self.nodes:
                    if u != v:
                        pos_u = self.node_positions[u]
                        dx = pos_v.x - pos_u.x
                        dy = pos_v.y - pos_u.y
                        dist = max(math.sqrt(dx * dx + dy * dy), 0.01)
                        force = k * k / dist

                        pos_v.vx += dx / dist * force
                        pos_v.vy += dy / dist * force

            # 引力（边）
            for edge in self.edges:
                source, target = edge["source"], edge["target"]
                if source in self.node_positions and target in self.node_positions:
                    pos_s = self.node_positions[source]
                    pos_t = self.node_positions[target]

                    dx = pos_t.x - pos_s.x
                    dy = pos_t.y - pos_s.y
                    dist = max(math.sqrt(dx * dx + dy * dy), 0.01)
                    force = dist * dist / k

                    pos_s.vx += dx / dist * force
                    pos_s.vy += dy / dist * force
                    pos_t.vx -= dx / dist * force
                    pos_t.vy -= dy / dist * force

            # 更新位置
            for v in self.nodes:
                pos = self.node_positions[v]
                disp = math.sqrt(pos.vx * pos.vx + pos.vy * pos.vy)
                if disp > 0:
                    pos.x += pos.vx / disp * min(disp, temp)
                    pos.y += pos.vy / disp * min(disp, temp)

                # 边界约束
                margin = 50
                pos.x = max(margin, min(self.width - margin, pos.x))
                pos.y = max(margin, min(self.height - margin, pos.y))

            temp *= 0.95

    def _render(self) -> None:
        """渲染图谱"""
        self.canvas.delete("all")
        self.node_items.clear()
        self.edge_items.clear()
        self.label_items.clear()

        # 颜色配置
        is_dark = self.theme == "dark"
        edge_color = ModernColors.DARK_BORDER if is_dark else ModernColors.LIGHT_BORDER
        text_color = ModernColors.DARK_TEXT if is_dark else ModernColors.LIGHT_TEXT

        # 类型颜色映射
        type_colors = {
            "人物": "#ef4444",
            "组织": "#3b82f6",
            "地点": "#10b981",
            "技术": "#8b5cf6",
            "概念": "#f59e0b",
            "事件": "#ec4899",
        }

        # 绘制边
        for edge in self.edges:
            source, target = edge["source"], edge["target"]
            if source in self.node_positions and target in self.node_positions:
                pos_s = self.node_positions[source]
                pos_t = self.node_positions[target]
                item = self.canvas.create_line(
                    pos_s.x, pos_s.y, pos_t.x, pos_t.y,
                    fill=edge_color,
                    width=1,
                    arrow="last",
                    arrowshape=(8, 10, 4),
                )
                self.edge_items.append(item)

        # 绘制节点
        node_radius = 20
        for node_id, node in self.nodes.items():
            if node_id not in self.node_positions:
                continue

            pos = self.node_positions[node_id]
            color = type_colors.get(node["type"], ModernColors.DARK_ACCENT)

            # 节点圆形
            item = self.canvas.create_oval(
                pos.x - node_radius,
                pos.y - node_radius,
                pos.x + node_radius,
                pos.y + node_radius,
                fill=color,
                outline="white" if is_dark else "#333",
                width=2,
            )
            self.node_items[node_id] = item

            # 节点标签
            label = self.canvas.create_text(
                pos.x,
                pos.y + node_radius + 12,
                text=node["name"][:8] + ("..." if len(node["name"]) > 8 else ""),
                fill=text_color,
                font=("Segoe UI", 10),
            )
            self.label_items[node_id] = label

    def _update_stats(self) -> None:
        """更新统计信息"""
        self.stats_label.configure(
            text=f"节点: {len(self.nodes)} | 边: {len(self.edges)}"
        )

    def _reset_layout(self) -> None:
        """重置布局"""
        self._init_layout()
        self._force_directed_layout()
        self._render()

    def _on_zoom_change(self, value: float) -> None:
        """缩放变化"""
        # TODO: 实现缩放功能
        pass

    def _on_click(self, event: Any) -> None:
        """点击事件"""
        node_id = self._find_node_at(event.x, event.y)
        if node_id:
            self.selected_node = node_id
            self.drag_node = node_id
            self.dragging = True
            if self.on_node_click:
                self.on_node_click(node_id, self.nodes[node_id])

    def _on_drag(self, event: Any) -> None:
        """拖拽事件"""
        if self.dragging and self.drag_node:
            pos = self.node_positions[self.drag_node]
            pos.x = event.x
            pos.y = event.y
            self._render()

    def _on_release(self, event: Any) -> None:
        """释放事件"""
        self.dragging = False
        self.drag_node = None

    def _on_motion(self, event: Any) -> None:
        """鼠标移动事件"""
        node_id = self._find_node_at(event.x, event.y)
        if node_id and self.on_node_hover:
            self.on_node_hover(node_id, self.nodes[node_id])

    def _find_node_at(self, x: float, y: float, radius: float = 25) -> str | None:
        """查找指定位置的节点"""
        for node_id, pos in self.node_positions.items():
            dx = x - pos.x
            dy = y - pos.y
            if dx * dx + dy * dy <= radius * radius:
                return node_id
        return None
