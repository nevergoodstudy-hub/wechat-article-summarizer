"""Force-directed layout helpers for the graph viewer."""

from __future__ import annotations

import math
import random
from typing import Any

from .graph_viewer_models import NodePosition


def initialize_layout(
    nodes: dict[str, dict[str, Any]],
    width: int,
    height: int,
) -> dict[str, NodePosition]:
    """Initialize nodes on a noisy circle around the canvas center."""
    positions: dict[str, NodePosition] = {}
    cx, cy = width / 2, height / 2
    radius = min(width, height) * 0.35

    for index, node_id in enumerate(nodes.keys()):
        angle = 2 * math.pi * index / max(len(nodes), 1)
        x = cx + radius * math.cos(angle) + random.uniform(-50, 50)
        y = cy + radius * math.sin(angle) + random.uniform(-50, 50)
        positions[node_id] = NodePosition(x=x, y=y)

    return positions


def apply_force_directed_layout(
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    positions: dict[str, NodePosition],
    width: int,
    height: int,
    iterations: int = 50,
) -> None:
    """Mutate positions with a simple force-directed layout algorithm."""
    k = math.sqrt(width * height / max(len(nodes), 1))
    temp = width / 10

    for _ in range(iterations):
        _apply_repulsion(nodes, positions, k)
        _apply_edge_attraction(edges, positions, k)
        _apply_displacement(nodes, positions, width, height, temp)
        temp *= 0.95


def _apply_repulsion(
    nodes: dict[str, dict[str, Any]],
    positions: dict[str, NodePosition],
    k: float,
) -> None:
    for node_id in nodes:
        pos_v = positions[node_id]
        pos_v.vx, pos_v.vy = 0, 0

        for other_id in nodes:
            if other_id == node_id:
                continue
            pos_u = positions[other_id]
            dx = pos_v.x - pos_u.x
            dy = pos_v.y - pos_u.y
            dist = max(math.sqrt(dx * dx + dy * dy), 0.01)
            force = k * k / dist
            pos_v.vx += dx / dist * force
            pos_v.vy += dy / dist * force


def _apply_edge_attraction(
    edges: list[dict[str, Any]],
    positions: dict[str, NodePosition],
    k: float,
) -> None:
    for edge in edges:
        source, target = edge["source"], edge["target"]
        if source not in positions or target not in positions:
            continue
        pos_s = positions[source]
        pos_t = positions[target]
        dx = pos_t.x - pos_s.x
        dy = pos_t.y - pos_s.y
        dist = max(math.sqrt(dx * dx + dy * dy), 0.01)
        force = dist * dist / k
        pos_s.vx += dx / dist * force
        pos_s.vy += dy / dist * force
        pos_t.vx -= dx / dist * force
        pos_t.vy -= dy / dist * force


def _apply_displacement(
    nodes: dict[str, dict[str, Any]],
    positions: dict[str, NodePosition],
    width: int,
    height: int,
    temp: float,
) -> None:
    for node_id in nodes:
        pos = positions[node_id]
        disp = math.sqrt(pos.vx * pos.vx + pos.vy * pos.vy)
        if disp > 0:
            pos.x += pos.vx / disp * min(disp, temp)
            pos.y += pos.vy / disp * min(disp, temp)

        margin = 50
        pos.x = max(margin, min(width - margin, pos.x))
        pos.y = max(margin, min(height - margin, pos.y))


__all__ = ["apply_force_directed_layout", "initialize_layout"]
