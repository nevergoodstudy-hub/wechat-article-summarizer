"""Models and constants for the graph viewer."""

from __future__ import annotations

from dataclasses import dataclass

from ..styles.colors import ModernColors


@dataclass
class NodePosition:
    """Node position and velocity used by the force layout."""

    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0


NODE_TYPE_COLORS = {
    "人物": "#ef4444",
    "组织": "#3b82f6",
    "地点": "#10b981",
    "技术": "#8b5cf6",
    "概念": "#f59e0b",
    "事件": "#ec4899",
}


def node_color_for_type(node_type: str) -> str:
    """Return a node color for a knowledge-graph entity type."""
    return NODE_TYPE_COLORS.get(node_type, ModernColors.DARK_ACCENT)


def truncate_node_label(name: str, limit: int = 8) -> str:
    """Return the compact label shown under a graph node."""
    return name[:limit] + ("..." if len(name) > limit else "")


__all__ = [
    "NODE_TYPE_COLORS",
    "NodePosition",
    "node_color_for_type",
    "truncate_node_label",
]
