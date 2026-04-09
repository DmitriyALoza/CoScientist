"""
Qdrant indexer for the knowledge base.

Manages six collections:
  - papers              (published literature)
  - sops_internal       (internal SOPs)
  - sops_manufacturer   (vendor / manufacturer SOPs)
  - reports             (experiment reports)
  - eln_entries         (ELN / lab notebook documents)
  - reference_docs      (catch-all user uploads)

Supports local (HuggingFace BAAI/bge-small-en-v1.5) and OpenAI embeddings.
"""

from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from eln.config import settings as _settings
from eln.tracing import get_tracer

# Local embedding model — excellent for scientific text, runs on CPU
_DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

COLLECTION_NAMES = (
    "papers", "sops_internal", "sops_manufacturer",
    "reports", "eln_entries", "reference_docs",
)

EMBEDDING_PROVIDERS: dict[str, dict] = {
    "local": {
        "models": ["BAAI/bge-small-en-v1.5"],
        "default": "BAAI/bge-small-en-v1.5",
        "dims": {"BAAI/bge-small-en-v1.5": 384},
    },
    "openai": {
        "models": ["text-embedding-3-small", "text-embedding-3-large"],
        "default": "text-embedding-3-small",
        "dims": {"text-embedding-3-small": 1536, "text-embedding-3-large": 3072},
    },
}


def _build_embeddings(provider: str, model: str) -> Embeddings:
    if provider == "local":
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name=model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    elif provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=model)
    else:
        raise ValueError(f"Unknown embedding provider: {provider!r}")


def get_vector_dim(provider: str, model: str) -> int:
    return EMBEDDING_PROVIDERS[provider]["dims"][model]


class KBIndexer:
    """
    Wraps Qdrant for indexing and querying the knowledge base.

    One QdrantClient per workspace. Three named collections.
    Idempotent upsert: skips chunks whose doc_id already exists.
    """

    def __init__(
        self,
        persist_dir: Path,
        embedding_provider: str = "local",
        embedding_model: str = _DEFAULT_EMBEDDING_MODEL,
    ):
        self.persist_dir = persist_dir
        persist_dir.mkdir(parents=True, exist_ok=True)

        self._embedding_provider = embedding_provider
        # Resolve empty model string to provider default
        if not embedding_model:
            embedding_model = EMBEDDING_PROVIDERS[embedding_provider]["default"]
        self._embedding_model = embedding_model

        self._embeddings = _build_embeddings(embedding_provider, embedding_model)

        if _settings.qdrant_url:
            self._client = QdrantClient(url=_settings.qdrant_url)
        else:
            self._client = QdrantClient(path=str(persist_dir))
        self._stores: dict[str, QdrantVectorStore] = {}

    def _get_store(self, collection_name: str) -> QdrantVectorStore:
        """Get or create a LangChain QdrantVectorStore for the named collection."""
        if collection_name not in self._stores:
            if not self._client.collection_exists(collection_name):
                self._client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=get_vector_dim(self._embedding_provider, self._embedding_model),
                        distance=Distance.COSINE,
                    ),
                )
            self._stores[collection_name] = QdrantVectorStore(
                client=self._client,
                collection_name=collection_name,
                embedding=self._embeddings,
            )
        return self._stores[collection_name]

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def upsert(self, documents: list[Document], collection_name: str) -> int:
        """
        Add documents to a collection, skipping those already indexed.

        Uses doc_id (sha256 of file + chunk_index) for idempotency.
        Returns the number of NEW documents actually inserted.
        """
        if collection_name not in COLLECTION_NAMES:
            raise ValueError(
                f"Unknown collection: {collection_name!r}. Must be one of {COLLECTION_NAMES}"
            )

        store = self._get_store(collection_name)

        # Collect existing doc_ids by scrolling all points
        existing_ids: set[str] = set()
        if self._client.collection_exists(collection_name):
            offset = None
            while True:
                results, offset = self._client.scroll(
                    collection_name=collection_name,
                    with_payload=["doc_id"],
                    limit=1000,
                    offset=offset,
                )
                for point in results:
                    if point.payload and "doc_id" in point.payload:
                        existing_ids.add(point.payload["doc_id"])
                if offset is None:
                    break

        new_docs = []
        for doc in documents:
            doc_id = doc.metadata.get("doc_id", "")
            if doc_id and doc_id not in existing_ids:
                new_docs.append(doc)

        if new_docs:
            store.add_documents(new_docs)

        return len(new_docs)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        collection_name: str,
        k: int = 5,
    ) -> list[Document]:
        """
        Similarity search within a single collection.
        Returns top-k Document objects with scores in metadata.
        """
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span("retrieval.search") as span:
            span.set_attribute("retrieval.collection", collection_name)
            span.set_attribute("retrieval.k", k)

            store = self._get_store(collection_name)
            results = store.similarity_search_with_relevance_scores(query, k=k)
            docs = []
            for doc, score in results:
                doc.metadata["relevance_score"] = score
                docs.append(doc)

            span.set_attribute("retrieval.doc_count", len(docs))
            return docs

    def search_all(
        self,
        query: str,
        collection_names: list[str] | None = None,
        k: int = 5,
    ) -> list[Document]:
        """
        Search across multiple collections, merge and re-rank by score.
        Returns top-k overall.
        """
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span("retrieval.search_all") as span:
            collections = collection_names or list(COLLECTION_NAMES)
            span.set_attribute("retrieval.k", k)

            all_docs: list[Document] = []
            for name in collections:
                try:
                    all_docs.extend(self.search(query, name, k=k))
                except Exception:
                    # Collection might be empty or not yet created
                    continue

            # Sort by relevance descending and take top-k
            all_docs.sort(
                key=lambda d: d.metadata.get("relevance_score", 0), reverse=True
            )
            result = all_docs[:k]
            span.set_attribute("retrieval.doc_count", len(result))
            return result

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    def collection_count(self, collection_name: str) -> int:
        """Return the number of documents in a collection."""
        try:
            return self._client.count(collection_name=collection_name).count
        except Exception:
            return 0
