"""Composition tests for split graph viewer component helpers."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from wechat_summarizer.presentation.gui.components import graph_viewer as graph_module
from wechat_summarizer.presentation.gui.components.graph_viewer import (
    GraphViewerComponent,
    NodePosition,
)
from wechat_summarizer.presentation.gui.components.graph_viewer_data import (
    graph_data_from_dicts,
)
from wechat_summarizer.presentation.gui.components.graph_viewer_interaction import (
    find_node_at,
)
from wechat_summarizer.presentation.gui.components.graph_viewer_layout import (
    apply_force_directed_layout,
    initialize_layout,
)
from wechat_summarizer.presentation.gui.components.graph_viewer_models import (
    NodePosition as SplitNodePosition,
)
from wechat_summarizer.presentation.gui.components.graph_viewer_models import (
    node_color_for_type,
    truncate_node_label,
)
from wechat_summarizer.presentation.gui.components.graph_viewer_render import render_graph


class RecordingCanvas:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []
        self._next_id = 1

    def delete(self, *args, **kwargs) -> None:
        self.calls.append(("delete", args, kwargs))

    def create_line(self, *args, **kwargs) -> int:
        return self._record("line", args, kwargs)

    def create_oval(self, *args, **kwargs) -> int:
        return self._record("oval", args, kwargs)

    def create_text(self, *args, **kwargs) -> int:
        return self._record("text", args, kwargs)

    def _record(self, name: str, args: tuple, kwargs: dict) -> int:
        item_id = self._next_id
        self._next_id += 1
        self.calls.append((name, args, kwargs))
        return item_id


@pytest.mark.unit
def test_graph_viewer_module_keeps_compatibility_exports() -> None:
    assert graph_module.GraphViewerComponent is GraphViewerComponent
    assert graph_module.NodePosition is SplitNodePosition
    assert NodePosition is SplitNodePosition


@pytest.mark.unit
def test_graph_viewer_data_normalizes_dict_payloads() -> None:
    nodes, edges = graph_data_from_dicts(
        entities=[
            {"name": "Alice", "type": "人物"},
            {"id": 42, "name": "ACME", "type": "组织", "description": "Org"},
            {},
        ],
        relationships=[
            {"source": "Alice", "target": "42"},
            {"id": "r2", "source_id": "42", "target_id": "entity_2", "type": "包含"},
        ],
    )

    assert list(nodes) == ["Alice", "42", "entity_2"]
    assert nodes["42"]["description"] == "Org"
    assert edges == [
        {"id": "Alice-42", "source": "Alice", "target": "42", "type": "相关"},
        {"id": "r2", "source": "42", "target": "entity_2", "type": "包含"},
    ]


@pytest.mark.unit
def test_graph_viewer_layout_keeps_positions_inside_canvas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from wechat_summarizer.presentation.gui.components import graph_viewer_layout

    monkeypatch.setattr(graph_viewer_layout.random, "uniform", lambda _a, _b: 0.0)
    nodes = {"a": {}, "b": {}}
    edges = [{"source": "a", "target": "b"}]
    positions = initialize_layout(nodes, width=200, height=200)

    apply_force_directed_layout(nodes, edges, positions, 200, 200, iterations=2)

    assert set(positions) == {"a", "b"}
    for position in positions.values():
        assert 50 <= position.x <= 150
        assert 50 <= position.y <= 150


@pytest.mark.unit
def test_graph_viewer_render_records_edges_nodes_and_labels() -> None:
    canvas = RecordingCanvas()
    nodes = {
        "a": {"name": "VeryLongEntityName", "type": "人物"},
        "b": {"name": "B", "type": "未知"},
    }
    edges = [{"source": "a", "target": "b"}]
    positions = {"a": NodePosition(50, 60), "b": NodePosition(150, 160)}
    node_items: dict[str, int] = {}
    edge_items: list[int] = []
    label_items: dict[str, int] = {}

    render_graph(canvas, nodes, edges, positions, "dark", node_items, edge_items, label_items)

    assert [call[0] for call in canvas.calls] == ["delete", "line", "oval", "text", "oval", "text"]
    assert len(edge_items) == 1
    assert set(node_items) == {"a", "b"}
    assert set(label_items) == {"a", "b"}
    assert truncate_node_label("VeryLongEntityName") == "VeryLong..."
    assert node_color_for_type("人物") == "#ef4444"


@pytest.mark.unit
def test_graph_viewer_interaction_finds_nearest_node() -> None:
    positions = {"a": NodePosition(10, 10), "b": NodePosition(100, 100)}

    assert find_node_at(positions, 14, 14, radius=10) == "a"
    assert find_node_at(positions, 50, 50, radius=10) is None


@pytest.mark.unit
def test_graph_viewer_private_methods_delegate_without_tk() -> None:
    viewer = object.__new__(GraphViewerComponent)
    viewer.nodes = {"a": {}, "b": {}}
    viewer.edges = [{"source": "a", "target": "b"}]
    viewer.node_positions = {"a": NodePosition(20, 20), "b": NodePosition(120, 120)}
    viewer.width = 200
    viewer.height = 200
    viewer.theme = "dark"
    viewer.canvas = RecordingCanvas()
    viewer.node_items = {}
    viewer.edge_items = []
    viewer.label_items = {}
    viewer.stats_label = SimpleNamespace(configure=lambda **_kwargs: None)

    assert viewer._find_node_at(20, 20) == "a"
    viewer._force_directed_layout(iterations=1)
    viewer._render()

    assert viewer.edge_items
    assert viewer.node_items


@pytest.mark.unit
def test_graph_viewer_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/components/graph_viewer.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/graph_viewer_runtime.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/graph_viewer_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/graph_viewer_data.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/graph_viewer_layout.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/graph_viewer_render.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/graph_viewer_interaction.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target
