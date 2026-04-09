"""MemoryManager — unified interface for all memory subsystems."""
from pathlib import Path

from eln.memory.episodic_store import EpisodicStore
from eln.memory.graph_store import KnowledgeGraphStore
from eln.models.memory import KnowledgeEdge, KnowledgeNode, MemoryEntry


class MemoryManager:
    """Wraps episodic store + knowledge graph, provides a unified API."""

    def __init__(self, memory_path: Path):
        self._path = memory_path
        memory_path.mkdir(parents=True, exist_ok=True)
        self._episodic = EpisodicStore(memory_path)
        self._graph = KnowledgeGraphStore(memory_path)

    def store(
        self,
        content: str,
        memory_type: str = "episodic",
        source_run_id: str | None = None,
        metadata: dict | None = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            memory_type=memory_type,
            content=content,
            source_run_id=source_run_id,
            metadata=metadata or {},
        )
        self._episodic.store(entry)
        return entry

    def recall(self, query: str, k: int = 5) -> list[MemoryEntry]:
        return self._episodic.search(query, k=k)

    def get_recent(self, n: int = 10) -> list[MemoryEntry]:
        return self._episodic.get_recent(n)

    def update_graph(
        self,
        node: KnowledgeNode | None = None,
        edge: KnowledgeEdge | None = None,
    ) -> None:
        if node:
            self._graph.add_node(node)
        if edge:
            self._graph.add_edge(edge)
        self._graph.save()

    def query_knowledge_graph(self, node_label: str) -> dict:
        node_id = self._graph.find_node_by_label(node_label)
        if not node_id:
            return {"found": False, "label": node_label}
        neighbors = self._graph.get_neighbors(node_id)
        return {
            "found": True,
            "node_id": node_id,
            "label": node_label,
            "neighbors": neighbors,
            "graph_summary": self._graph.summary(),
        }

    def get_context_for_hypothesis(self, hypothesis: str) -> dict:
        """Recall relevant episodic memories + graph context for a hypothesis."""
        episodes = self.recall(hypothesis, k=5)
        first_word = hypothesis.split()[0] if hypothesis else ""
        graph_result = self.query_knowledge_graph(first_word)
        return {
            "episodic_memories": [e.model_dump(mode="json") for e in episodes],
            "graph_context": graph_result,
        }
