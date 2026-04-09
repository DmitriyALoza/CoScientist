"""
Unified RAG retriever.

Combines the ingester + indexer to provide a single `retrieve()` call
that returns Citation objects ready for the subagents and ELN renderer.
"""

import hashlib
import uuid
from pathlib import Path

from langchain_core.documents import Document

from eln.models.citation import Citation, SourceType
from eln.retrieval.indexer import KBIndexer
from eln.tracing import get_tracer

# Map collection names to SourceType
_COLLECTION_TO_SOURCE: dict[str, SourceType] = {
    "papers": SourceType.PAPER,
    "sops_internal": SourceType.SOP_INTERNAL,
    "sops_manufacturer": SourceType.SOP_MANUFACTURER,
    "reports": SourceType.REPORT,
    "eln_entries": SourceType.ELN_ENTRY,
    "reference_docs": SourceType.REFERENCE_DOC,
}

# Reverse mapping
_SOURCE_TO_COLLECTION: dict[SourceType, str] = {v: k for k, v in _COLLECTION_TO_SOURCE.items()}


class RAGRetriever:
    """
    High-level retriever that:
      1. Queries the KBIndexer
      2. Converts search results into Citation objects
    """

    def __init__(self, indexer: KBIndexer):
        self.indexer = indexer

    def retrieve(
        self,
        query: str,
        source_types: list[SourceType] | None = None,
        k: int = 5,
    ) -> list[Citation]:
        """
        Retrieve relevant documents and return Citation objects.

        Args:
            query: Natural language search query.
            source_types: Limit search to these source types. None = search all.
            k: Maximum number of citations to return.
        """
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span("retrieval.retrieve") as span:
            span.set_attribute("retrieval.query_length", len(query))
            span.set_attribute("retrieval.k", k)
            if source_types:
                span.set_attribute(
                    "retrieval.source_types", ",".join(st.value for st in source_types)
                )

            if source_types:
                collections = [
                    _SOURCE_TO_COLLECTION[st]
                    for st in source_types
                    if st in _SOURCE_TO_COLLECTION
                ]
            else:
                collections = None

            docs = self.indexer.search_all(query, collection_names=collections, k=k)
            citations = [self._doc_to_citation(doc) for doc in docs]

            span.set_attribute("retrieval.result_count", len(citations))
            span.set_attribute(
                "retrieval.citation_ids", ",".join(c.citation_id for c in citations)
            )

            from eln.audit.singleton import get_audit_logger
            _al = get_audit_logger()
            if _al:
                _al.log_retrieval(
                    query=query,
                    source_types=[c.source_type.value for c in citations],
                    doc_ids=[c.source_id for c in citations],
                    excerpt_hashes=[c.excerpt_hash for c in citations],
                )

            return citations

    @staticmethod
    def _doc_to_citation(doc: Document) -> Citation:
        """Convert a LangChain Document (with retrieval metadata) to a Citation."""
        meta = doc.metadata
        excerpt = doc.page_content[:500]  # cap excerpt length
        excerpt_hash = hashlib.sha256(excerpt.encode()).hexdigest()

        source_type_str = meta.get("source_type", "paper")
        try:
            source_type = SourceType(source_type_str)
        except ValueError:
            source_type = SourceType.PAPER

        # Build a human-readable location string
        location_parts = []
        if "page" in meta:
            location_parts.append(f"page {meta['page']}")
        if "slide" in meta:
            location_parts.append(f"slide {meta['slide']}")
        if "chunk_index" in meta and "total_chunks" in meta:
            location_parts.append(f"chunk {meta['chunk_index']+1}/{meta['total_chunks']}")
        location = ", ".join(location_parts) if location_parts else None

        return Citation(
            citation_id=meta.get("doc_id", str(uuid.uuid4())[:8]),
            source_type=source_type,
            source_id=meta.get("sha256", meta.get("source_path", "")),
            title=(
                Path(meta.get("source_path", "unknown")).stem
                if meta.get("source_path") else None
            ),
            excerpt=excerpt,
            location=location,
            excerpt_hash=excerpt_hash,
        )
