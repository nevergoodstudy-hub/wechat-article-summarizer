"""Interaction helpers for the graph viewer."""

from __future__ import annotations

from .graph_viewer_models import NodePosition


def find_node_at(
    positions: dict[str, NodePosition],
    x: float,
    y: float,
    radius: float = 25,
) -> str | None:
    """Return the node id under a point, if any."""
    for node_id, pos in positions.items():
        dx = x - pos.x
        dy = y - pos.y
        if dx * dx + dy * dy <= radius * radius:
            return node_id
    return None


__all__ = ["find_node_at"]
