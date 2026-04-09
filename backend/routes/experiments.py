"""Experiment loop endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from eln.workspace.manager import WorkspaceManager
from eln.workspace.experiment_store import ExperimentStore

router = APIRouter(tags=["experiments"])


@router.get("/experiments")
async def list_experiments(user_id: str = "default", limit: int = 20) -> list[dict]:
    wm = WorkspaceManager(user_id=user_id)
    store = ExperimentStore(wm.experiments_path())
    loops = store.list_loops()
    return [loop.model_dump(mode="json") for loop in loops]


@router.get("/experiments/{loop_id}")
async def get_experiment_loop(loop_id: str, user_id: str = "default") -> dict:
    wm = WorkspaceManager(user_id=user_id)
    store = ExperimentStore(wm.experiments_path())
    loop = store.load_loop(loop_id)
    if loop is None:
        raise HTTPException(status_code=404, detail="Experiment loop not found")
    return loop.model_dump(mode="json")
