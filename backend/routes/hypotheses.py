"""Hypothesis endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from eln.config import settings
from eln.workspace.manager import WorkspaceManager
from eln.workspace.hypothesis_store import HypothesisStore

router = APIRouter(tags=["hypotheses"])


@router.get("/hypotheses")
async def list_hypotheses(user_id: str = "default", limit: int = 20) -> list[dict]:
    wm = WorkspaceManager(user_id=user_id)
    store = HypothesisStore(wm.hypotheses_path())
    sets = store.list(limit=limit)
    return [s.model_dump(mode="json") for s in sets]


@router.get("/hypotheses/{set_id}")
async def get_hypothesis_set(set_id: str, user_id: str = "default") -> dict:
    wm = WorkspaceManager(user_id=user_id)
    store = HypothesisStore(wm.hypotheses_path())
    h_set = store.load(set_id)
    if h_set is None:
        raise HTTPException(status_code=404, detail="Hypothesis set not found")
    return h_set.model_dump(mode="json")
