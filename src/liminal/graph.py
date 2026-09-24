from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict
from datetime import datetime
from typing import Any

from .models import ProvenanceEdge


class EvidenceGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[str, ProvenanceEdge] = {}

    def add_node(self, node_id: str, node_type: str, **attributes: Any) -> None:
        if not node_id:
            raise ValueError("node_id must not be empty")
        current = self.nodes.setdefault(node_id, {})
        current.update({"node_type": node_type, **attributes})

    def add_edge(self, edge_id: str, edge: ProvenanceEdge) -> None:
        edge.validate()
        if edge.source_id not in self.nodes:
            self.add_node(edge.source_id, "unknown")
        if edge.target_id not in self.nodes:
            self.add_node(edge.target_id, "unknown")
        self.edges[edge_id] = edge

    def neighbors(self, node_id: str, relation: str | None = None) -> list[str]:
        return [
            edge.target_id
            for edge in self.edges.values()
            if edge.source_id == node_id
            and (relation is None or edge.relation == relation)
        ]

    def incoming(self, node_id: str, relation: str | None = None) -> list[str]:
        return [
            edge.source_id
            for edge in self.edges.values()
            if edge.target_id == node_id
            and (relation is None or edge.relation == relation)
        ]

    def propagation_depth(
        self, root_id: str, target_id: str, relation: str | None = None
    ) -> int | None:
        queue = deque([(root_id, 0)])
        visited = {root_id}
        while queue:
            current, depth = queue.popleft()
            if current == target_id:
                return depth
            for neighbor in self.neighbors(current, relation):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))
        return None

    def root_origins(self, node_id: str, relation: str = "copies") -> set[str]:
        roots = set()
        queue = deque([node_id])
        visited = {node_id}
        reverse = defaultdict(list)
        for edge in self.edges.values():
            if edge.relation == relation:
                reverse[edge.target_id].append(edge.source_id)
        while queue:
            current = queue.popleft()
            parents = reverse.get(current, [])
            if not parents:
                roots.add(current)
            for parent in parents:
                if parent not in visited:
                    visited.add(parent)
                    queue.append(parent)
        return roots

    def estimated_independent_origins(self, node_id: str) -> int:
        return len(self.root_origins(node_id))

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": {edge_id: asdict(edge) for edge_id, edge in self.edges.items()},
        }

    def to_json_ready(self) -> dict[str, Any]:
        payload = self.to_dict()
        for edge in payload["edges"].values():
            edge["observed_at"] = (
                edge["observed_at"].isoformat()
                if isinstance(edge["observed_at"], datetime)
                else edge["observed_at"]
            )
        return payload
