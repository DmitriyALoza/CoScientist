"""LangChain @tool wrappers for the memory subsystem.

Injected into memory_agent. Initialized via set_memory_manager().
"""

from langchain_core.tools import tool

from eln.memory.memory_manager import MemoryManager

_memory_manager: MemoryManager | None = None


def set_memory_manager(manager: MemoryManager) -> None:
    global _memory_manager
    _memory_manager = manager


def _get_mm() -> MemoryManager:
    if _memory_manager is None:
        raise RuntimeError("MemoryManager not initialized. Call set_memory_manager() first.")
    return _memory_manager


@tool
def recall_memory(query: str, k: int = 5) -> str:
    """Recall relevant memories from the episodic store.

    Args:
        query: Natural language query to search memories.
        k: Max number of memories to return (default 5).

    Returns:
        Formatted list of relevant memory entries.
    """
    mm = _get_mm()
    entries = mm.recall(query, k=k)
    if not entries:
        return "No relevant memories found for that query."
    lines = []
    for e in entries:
        run_tag = f" [run: {e.source_run_id[:8]}]" if e.source_run_id else ""
        lines.append(
            f"[{e.memory_id[:8]}] ({e.memory_type}) {e.timestamp.strftime('%Y-%m-%d')}{run_tag}\n"
            f"  {e.content[:400]}"
        )
    return "\n\n".join(lines)


@tool
def store_memory(content: str, memory_type: str = "episodic", run_id: str = "") -> str:
    """Store a new memory entry.

    Args:
        content: The memory content to store.
        memory_type: 'episodic', 'semantic', or 'procedural'.
        run_id: Optional run ID to associate with this memory.

    Returns:
        Confirmation with the assigned memory ID.
    """
    mm = _get_mm()
    entry = mm.store(content, memory_type=memory_type, source_run_id=run_id or None)
    return f"Memory stored with ID: {entry.memory_id[:8]} (type: {memory_type})"


@tool
def query_knowledge_graph(node_label: str) -> str:
    """Query the knowledge graph for a concept or entity.

    Args:
        node_label: The label of the node to look up.

    Returns:
        Node information and its connected neighbors.
    """
    mm = _get_mm()
    result = mm.query_knowledge_graph(node_label)
    if not result.get("found"):
        return f"No node found for '{node_label}' in the knowledge graph."
    neighbors = result.get("neighbors", [])
    summary = result.get("graph_summary", {})
    lines = [
        f"Node: **{result['label']}** (id: {result['node_id'][:8]})",
        f"Graph size: {summary.get('nodes', 0)} nodes, {summary.get('edges', 0)} edges",
    ]
    if neighbors:
        lines.append("Connected to:")
        for n in neighbors[:10]:
            lines.append(f"  — {n.get('label', n['node_id'][:8])} via '{n.get('relation', 'related')}'")
    return "\n".join(lines)


@tool
def update_knowledge_graph(
    node_label: str,
    node_type: str,
    related_label: str = "",
    relation: str = "related_to",
) -> str:
    """Add a node (and optionally a relationship) to the knowledge graph.

    Args:
        node_label: Label for the new node.
        node_type: 'concept', 'entity', 'result', or 'hypothesis'.
        related_label: Label of an existing node to connect to (optional).
        relation: 'supports', 'contradicts', 'related_to', or 'derived_from'.

    Returns:
        Confirmation message.
    """
    from eln.models.memory import KnowledgeEdge, KnowledgeNode

    mm = _get_mm()
    node = KnowledgeNode(label=node_label, node_type=node_type)
    mm.update_graph(node=node)

    if related_label:
        related_id = mm._graph.find_node_by_label(related_label)
        if related_id:
            edge = KnowledgeEdge(
                source_id=node.node_id,
                target_id=related_id,
                relation=relation,
            )
            mm.update_graph(edge=edge)
            return f"Added '{node_label}' → '{related_label}' via '{relation}'."

    return f"Added node '{node_label}' (type: {node_type})."
