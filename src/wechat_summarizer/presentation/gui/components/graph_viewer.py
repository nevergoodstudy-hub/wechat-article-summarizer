"""Compatibility entrypoint for the knowledge graph viewer component."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ..styles.colors import ModernColors
from .graph_viewer_data import (
    graph_data_from_dicts,
    graph_data_from_knowledge_graph,
)
from .graph_viewer_interaction import find_node_at
from .graph_viewer_layout import apply_force_directed_layout, initialize_layout
from .graph_viewer_models import NodePosition
from .graph_viewer_render import render_graph
from .graph_viewer_runtime import _ctk_available, ctk, require_ctk

if TYPE_CHECKING:
    from ....application.ports.outbound import KnowledgeGraph


class GraphViewerComponent:
    """Knowledge graph viewer component using a force-directed canvas layout."""

    def __init__(
        self,
        master: Any,
        width: int = 800,
        height: int = 600,
        theme: str = "dark",
    ) -> None:
        ctk_runtime = require_ctk()
        self.master = master
        self.width = width
        self.height = height
        self.theme = theme

        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: list[dict[str, Any]] = []
        self.node_positions: dict[str, NodePosition] = {}

        self.node_items: dict[str, int] = {}
        self.edge_items: list[int] = []
        self.label_items: dict[str, int] = {}

        self.selected_node: str | None = None
        self.dragging: bool = False
        self.drag_node: str | None = None

        self.on_node_click: Callable[[str, dict], None] | None = None
        self.on_node_hover: Callable[[str, dict], None] | None = None
        self._ctk = ctk_runtime

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the component widgets."""
        self.frame = self._ctk.CTkFrame(self.master)
        self.toolbar = self._ctk.CTkFrame(self.frame, height=40)
        self.toolbar.pack(fill="x", padx=5, pady=5)

        self._ctk.CTkLabel(self.toolbar, text="缩放:").pack(side="left", padx=5)
        self.zoom_slider = self._ctk.CTkSlider(
            self.toolbar,
            from_=0.5,
            to=2.0,
            number_of_steps=15,
            command=self._on_zoom_change,
        )
        self.zoom_slider.set(1.0)
        self.zoom_slider.pack(side="left", padx=5)

        self.reset_btn = self._ctk.CTkButton(
            self.toolbar,
            text="重置布局",
            width=80,
            command=self._reset_layout,
        )
        self.reset_btn.pack(side="right", padx=5)

        self.stats_label = self._ctk.CTkLabel(self.toolbar, text="节点: 0 | 边: 0")
        self.stats_label.pack(side="right", padx=20)

        bg_color = ModernColors.DARK_BG if self.theme == "dark" else ModernColors.LIGHT_BG
        self.canvas = self._ctk.CTkCanvas(
            self.frame,
            width=self.width,
            height=self.height,
            bg=bg_color,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)

    def pack(self, **kwargs: Any) -> None:
        """Pack the component frame."""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """Grid the component frame."""
        self.frame.grid(**kwargs)

    def load_knowledge_graph(self, kg: KnowledgeGraph) -> None:
        """Load a domain knowledge graph."""
        self.nodes, self.edges = graph_data_from_knowledge_graph(kg)
        self.node_positions.clear()
        self._init_layout()
        self._update_stats()
        self._render()

    def load_from_dict(
        self,
        entities: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
    ) -> None:
        """Load graph data from dictionaries."""
        self.nodes, self.edges = graph_data_from_dicts(entities, relationships)
        self.node_positions.clear()
        self._init_layout()
        self._update_stats()
        self._render()

    def _init_layout(self) -> None:
        """Initialize node positions."""
        self.node_positions = initialize_layout(self.nodes, self.width, self.height)

    def _force_directed_layout(self, iterations: int = 50) -> None:
        """Apply the force-directed layout algorithm."""
        apply_force_directed_layout(
            self.nodes,
            self.edges,
            self.node_positions,
            self.width,
            self.height,
            iterations,
        )

    def _render(self) -> None:
        """Render the graph."""
        render_graph(
            self.canvas,
            self.nodes,
            self.edges,
            self.node_positions,
            self.theme,
            self.node_items,
            self.edge_items,
            self.label_items,
        )

    def _update_stats(self) -> None:
        """Update the statistics label."""
        self.stats_label.configure(text=f"节点: {len(self.nodes)} | 边: {len(self.edges)}")

    def _reset_layout(self) -> None:
        """Reset graph layout."""
        self._init_layout()
        self._force_directed_layout()
        self._render()

    def _on_zoom_change(self, value: float) -> None:
        """Handle zoom changes."""
        pass

    def _on_click(self, event: Any) -> None:
        """Handle mouse click events."""
        node_id = self._find_node_at(event.x, event.y)
        if node_id:
            self.selected_node = node_id
            self.drag_node = node_id
            self.dragging = True
            if self.on_node_click:
                self.on_node_click(node_id, self.nodes[node_id])

    def _on_drag(self, event: Any) -> None:
        """Handle node dragging."""
        if self.dragging and self.drag_node:
            pos = self.node_positions[self.drag_node]
            pos.x = event.x
            pos.y = event.y
            self._render()

    def _on_release(self, event: Any) -> None:
        """Handle mouse release events."""
        self.dragging = False
        self.drag_node = None

    def _on_motion(self, event: Any) -> None:
        """Handle mouse move events."""
        node_id = self._find_node_at(event.x, event.y)
        if node_id and self.on_node_hover:
            self.on_node_hover(node_id, self.nodes[node_id])

    def _find_node_at(self, x: float, y: float, radius: float = 25) -> str | None:
        """Find a node under the given point."""
        return find_node_at(self.node_positions, x, y, radius)


__all__ = [
    "GraphViewerComponent",
    "NodePosition",
    "_ctk_available",
    "ctk",
]
