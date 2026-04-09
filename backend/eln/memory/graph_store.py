"""Knowledge graph store using NetworkX, persisted as node_link_data JSON."""
import json
from pathlib import Path
from typing import Any

from eln.models.memory import KnowledgeEdge, KnowledgeNode


class KnowledgeGraphStore:
    """NetworkX DiGraph persisted as node_link_data JSON."""

    def __init__(self, storage_path: Path):
        self._path = storage_path / "knowledge_graph.json"
        try:
            import networkx as nx  # lazy import — heavy dep
        except ImportError:
            raise ImportError("networkx is required. Run: uv add networkx")
        self._nx = nx
        self._graph: Any = nx.DiGraph()
        if self._path.exists():
            self.load()

    def add_node(self, node: KnowledgeNode) -> None:
        self._graph.add_node(
            node.node_id,
            label=node.label,
            node_type=node.node_type,
            **node.properties,
        )

    def add_edge(self, edge: KnowledgeEdge) -> None:
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            relation=edge.relation,
            weight=edge.weight,
            timestamp=edge.timestamp.isoformat(),
        )

    def find_node_by_label(self, label: str) -> str | None:
        for node_id, data in self._graph.nodes(data=True):
            if data.get("label", "").lower() == label.lower():
                return node_id
        return None

    def get_neighbors(self, node_id: str) -> list[dict]:
        if node_id not in self._graph:
            return []
        neighbors = []
        for neighbor in self._graph.neighbors(node_id):
            data = dict(self._graph.nodes[neighbor])
            edge_data = dict(self._graph.edges[node_id, neighbor])
            neighbors.append({
                "node_id": neighbor,
                "label": data.get("label", neighbor[:8]),
                "node_type": data.get("node_type", "unknown"),
                "relation": edge_data.get("relation", "related"),
            })
        return neighbors

    def query_subgraph(self, node_ids: list[str]) -> dict:
        valid = [n for n in node_ids if n in self._graph]
        if not valid:
            return {}
        subgraph = self._graph.subgraph(valid)
        return self._nx.node_link_data(subgraph)

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = self._nx.node_link_data(self._graph)
        with open(self._path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> None:
        with open(self._path) as f:
            data = json.load(f)
        self._graph = self._nx.node_link_graph(data, directed=True)

    def summary(self) -> dict:
        return {
            "nodes": self._graph.number_of_nodes(),
            "edges": self._graph.number_of_edges(),
        }
