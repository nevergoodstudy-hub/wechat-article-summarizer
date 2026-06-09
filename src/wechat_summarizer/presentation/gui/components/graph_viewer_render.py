"""Canvas rendering helpers for the graph viewer."""

from __future__ import annotations

from typing import Any

from ..styles.colors import ModernColors
from .graph_viewer_models import (
    NodePosition,
    node_color_for_type,
    truncate_node_label,
)


def render_graph(
    canvas: Any,
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    positions: dict[str, NodePosition],
    theme: str,
    node_items: dict[str, int],
    edge_items: list[int],
    label_items: dict[str, int],
) -> None:
    """Render graph nodes and edges onto a Tk-compatible canvas."""
    canvas.delete("all")
    node_items.clear()
    edge_items.clear()
    label_items.clear()

    is_dark = theme == "dark"
    edge_color = ModernColors.DARK_BORDER if is_dark else ModernColors.LIGHT_BORDER
    text_color = ModernColors.DARK_TEXT if is_dark else ModernColors.LIGHT_TEXT

    _render_edges(canvas, edges, positions, edge_color, edge_items)
    _render_nodes(canvas, nodes, positions, is_dark, text_color, node_items, label_items)


def _render_edges(
    canvas: Any,
    edges: list[dict[str, Any]],
    positions: dict[str, NodePosition],
    edge_color: str,
    edge_items: list[int],
) -> None:
    for edge in edges:
        source, target = edge["source"], edge["target"]
        if source not in positions or target not in positions:
            continue
        pos_s = positions[source]
        pos_t = positions[target]
        item = canvas.create_line(
            pos_s.x,
            pos_s.y,
            pos_t.x,
            pos_t.y,
            fill=edge_color,
            width=1,
            arrow="last",
            arrowshape=(8, 10, 4),
        )
        edge_items.append(item)


def _render_nodes(
    canvas: Any,
    nodes: dict[str, dict[str, Any]],
    positions: dict[str, NodePosition],
    is_dark: bool,
    text_color: str,
    node_items: dict[str, int],
    label_items: dict[str, int],
) -> None:
    node_radius = 20
    for node_id, node in nodes.items():
        if node_id not in positions:
            continue

        pos = positions[node_id]
        color = node_color_for_type(str(node.get("type", "")))
        item = canvas.create_oval(
            pos.x - node_radius,
            pos.y - node_radius,
            pos.x + node_radius,
            pos.y + node_radius,
            fill=color,
            outline="white" if is_dark else "#333",
            width=2,
        )
        node_items[node_id] = item

        label = canvas.create_text(
            pos.x,
            pos.y + node_radius + 12,
            text=truncate_node_label(str(node.get("name", ""))),
            fill=text_color,
            font=("Segoe UI", 10),
        )
        label_items[node_id] = label


__all__ = ["render_graph"]
