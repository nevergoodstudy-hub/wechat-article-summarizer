"""Data normalization helpers for the graph viewer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ....application.ports.outbound import KnowledgeGraph


def graph_data_from_knowledge_graph(
    kg: KnowledgeGraph,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Convert a domain knowledge graph into viewer nodes and edges."""
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    for entity_id, entity in kg.entities.items():
        nodes[entity_id] = {
            "id": entity_id,
            "name": entity.name,
            "type": entity.type,
            "description": entity.description,
        }

    for rel_id, rel in kg.relationships.items():
        edges.append(
            {
                "id": rel_id,
                "source": rel.source_id,
                "target": rel.target_id,
                "type": rel.type,
            }
        )

    return nodes, edges


def graph_data_from_dicts(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Normalize dictionary payloads into viewer nodes and edges."""
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    for index, entity in enumerate(entities):
        entity_id_raw = entity.get("id", entity.get("name"))
        if entity_id_raw is None:
            entity_id = f"entity_{index}"
        elif isinstance(entity_id_raw, str):
            entity_id = entity_id_raw
        else:
            entity_id = str(entity_id_raw)
        nodes[entity_id] = {
            "id": entity_id,
            "name": entity.get("name", ""),
            "type": entity.get("type", ""),
            "description": entity.get("description", ""),
        }

    for rel in relationships:
        source = rel.get("source_id", rel.get("source"))
        target = rel.get("target_id", rel.get("target"))
        edges.append(
            {
                "id": rel.get("id", f"{source}-{target}"),
                "source": source,
                "target": target,
                "type": rel.get("type", "相关"),
            }
        )

    return nodes, edges


__all__ = ["graph_data_from_dicts", "graph_data_from_knowledge_graph"]
