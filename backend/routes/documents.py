"""Knowledge base ingest and search endpoints."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from eln.workspace.manager import WorkspaceManager

router = APIRouter(tags=["documents"])


@router.get("/kb/stats")
async def kb_stats(user_id: str = "default") -> dict:
    wm = WorkspaceManager(user_id=user_id)
    collections = ["papers", "sops_internal", "sops_manufacturer", "reports", "eln_entries", "reference_docs"]
    by_collection: dict[str, int] = {}
    total = 0
    for col in collections:
        col_dir = wm.kb_path(col)
        count = len(list(col_dir.glob("*"))) if col_dir.exists() else 0
        by_collection[col] = count
        total += count
    return {"by_collection": by_collection, "total_documents": total}


@router.post("/kb/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    kb_type: str = Form(default="papers"),
    user_id: str = Form(default="default"),
) -> dict:
    from eln.retrieval.ingester import Ingester, IngestionError
    from eln.retrieval.indexer import KBIndexer, EMBEDDING_PROVIDERS

    suffix = Path(file.filename or "upload").suffix
    contents = await file.read()

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        ingester = Ingester()
        docs = ingester.ingest(tmp_path)
    except (IngestionError, Exception) as e:
        raise HTTPException(status_code=422, detail=f"Could not parse file: {e}")
    finally:
        tmp_path.unlink(missing_ok=True)

    if not docs:
        raise HTTPException(status_code=422, detail="File produced no indexable content")

    wm = WorkspaceManager(user_id=user_id)
    ep = "local"
    em = EMBEDDING_PROVIDERS[ep]["default"]
    indexer = KBIndexer(
        indexes_path=wm.indexes_path(),
        embedding_provider=ep,
        embedding_model=em,
    )
    indexer.index(docs, collection=kb_type)

    return {"indexed": len(docs), "collection": kb_type, "filename": file.filename}


class SearchRequest(BaseModel):
    query: str
    collection: str = "papers"
    limit: int = 5
    user_id: str = "default"


@router.post("/kb/search")
async def search_kb(body: SearchRequest) -> list[dict]:
    from eln.retrieval.retriever import RAGRetriever
    from eln.retrieval.indexer import KBIndexer, EMBEDDING_PROVIDERS

    wm = WorkspaceManager(user_id=body.user_id)
    ep = "local"
    em = EMBEDDING_PROVIDERS[ep]["default"]
    indexer = KBIndexer(
        indexes_path=wm.indexes_path(),
        embedding_provider=ep,
        embedding_model=em,
    )
    retriever = RAGRetriever(indexer=indexer)
    results = retriever.retrieve(body.query, collection=body.collection, k=body.limit)
    return [r.model_dump(mode="json") for r in results]
