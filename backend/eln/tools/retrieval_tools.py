"""
LangChain @tool wrappers around the RAG retriever.

These are injected into subagents (literature_scout, sop_adapter, etc.)
so they can search the knowledge base within the LangGraph flow.
"""

from langchain_core.tools import tool

from eln.models.citation import SourceType
from eln.retrieval.retriever import RAGRetriever

# Module-level retriever instance — set by the supervisor builder
_retriever: RAGRetriever | None = None


def set_retriever(retriever: RAGRetriever) -> None:
    global _retriever
    _retriever = retriever


def _get_retriever() -> RAGRetriever:
    if _retriever is None:
        raise RuntimeError("RAGRetriever not initialized. Call set_retriever() first.")
    return _retriever


@tool
def search_papers(query: str, k: int = 5) -> str:
    """Search the indexed papers/literature for relevant content.

    Args:
        query: A natural language search query about the scientific topic.
        k: Maximum number of results to return (default 5).

    Returns:
        Formatted citations with excerpts from matching papers.
    """
    retriever = _get_retriever()
    citations = retriever.retrieve(query, source_types=[SourceType.PAPER], k=k)
    if not citations:
        return "No relevant papers found in the knowledge base."
    lines = []
    for c in citations:
        lines.append(
            f"[{c.citation_id}] {c.title or 'Untitled'}\n"
            f"  Excerpt: {c.excerpt[:300]}...\n"
            f"  Location: {c.location or 'N/A'}\n"
        )
    return "\n".join(lines)


@tool
def search_sops(query: str, k: int = 5) -> str:
    """Search internal and manufacturer SOPs for relevant protocol content.

    Args:
        query: A natural language search query about a protocol or procedure.
        k: Maximum number of results to return (default 5).

    Returns:
        Formatted citations with excerpts from matching SOPs.
    """
    retriever = _get_retriever()
    citations = retriever.retrieve(
        query,
        source_types=[SourceType.SOP_INTERNAL, SourceType.SOP_MANUFACTURER],
        k=k,
    )
    if not citations:
        return "No relevant SOPs found in the knowledge base."
    lines = []
    for c in citations:
        is_internal = c.source_type == SourceType.SOP_INTERNAL
        src_label = "Internal SOP" if is_internal else "Manufacturer SOP"
        lines.append(
            f"[{c.citation_id}] ({src_label}) {c.title or 'Untitled'}\n"
            f"  Excerpt: {c.excerpt[:300]}...\n"
            f"  Location: {c.location or 'N/A'}\n"
        )
    return "\n".join(lines)


@tool
def search_reports(query: str, k: int = 5) -> str:
    """Search indexed experiment reports for relevant content.

    Args:
        query: A natural language search query about experiment results or findings.
        k: Maximum number of results to return (default 5).

    Returns:
        Formatted citations with excerpts from matching reports.
    """
    retriever = _get_retriever()
    citations = retriever.retrieve(query, source_types=[SourceType.REPORT], k=k)
    if not citations:
        return "No relevant reports found in the knowledge base."
    lines = []
    for c in citations:
        lines.append(
            f"[{c.citation_id}] {c.title or 'Untitled'}\n"
            f"  Excerpt: {c.excerpt[:300]}...\n"
            f"  Location: {c.location or 'N/A'}\n"
        )
    return "\n".join(lines)


@tool
def search_eln_entries(query: str, k: int = 5) -> str:
    """Search indexed ELN / lab notebook documents for relevant content.

    Args:
        query: A natural language search query about lab notebook entries.
        k: Maximum number of results to return (default 5).

    Returns:
        Formatted citations with excerpts from matching ELN entries.
    """
    retriever = _get_retriever()
    citations = retriever.retrieve(query, source_types=[SourceType.ELN_ENTRY], k=k)
    if not citations:
        return "No relevant ELN entries found in the knowledge base."
    lines = []
    for c in citations:
        lines.append(
            f"[{c.citation_id}] {c.title or 'Untitled'}\n"
            f"  Excerpt: {c.excerpt[:300]}...\n"
            f"  Location: {c.location or 'N/A'}\n"
        )
    return "\n".join(lines)


@tool
def search_reference_docs(query: str, k: int = 5) -> str:
    """Search indexed reference documents for relevant content.

    Args:
        query: A natural language search query.
        k: Maximum number of results to return (default 5).

    Returns:
        Formatted citations with excerpts from matching reference documents.
    """
    retriever = _get_retriever()
    citations = retriever.retrieve(query, source_types=[SourceType.REFERENCE_DOC], k=k)
    if not citations:
        return "No relevant reference documents found in the knowledge base."
    lines = []
    for c in citations:
        lines.append(
            f"[{c.citation_id}] {c.title or 'Untitled'}\n"
            f"  Excerpt: {c.excerpt[:300]}...\n"
            f"  Location: {c.location or 'N/A'}\n"
        )
    return "\n".join(lines)


@tool
def search_all_kb(query: str, k: int = 5) -> str:
    """Search the entire knowledge base (papers + SOPs) for relevant content.

    Args:
        query: A natural language search query.
        k: Maximum number of results to return (default 5).

    Returns:
        Formatted citations with excerpts from all matching sources.
    """
    retriever = _get_retriever()
    citations = retriever.retrieve(query, source_types=None, k=k)
    if not citations:
        return "No relevant documents found in the knowledge base."
    lines = []
    for c in citations:
        lines.append(
            f"[{c.citation_id}] ({c.source_type}) {c.title or 'Untitled'}\n"
            f"  Excerpt: {c.excerpt[:300]}...\n"
            f"  Location: {c.location or 'N/A'}\n"
        )
    return "\n".join(lines)
