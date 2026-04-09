"""Run / workspace CRUD endpoints."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from eln.config import settings
from eln.workspace.manager import WorkspaceManager

router = APIRouter(tags=["workspace"])


class CreateRunRequest(BaseModel):
    title: str
    domain: str = "other"
    objective: str = ""
    user_id: str = "default"


@router.get("/runs")
async def list_runs(user_id: str = "default", limit: int = 20) -> list[dict]:
    wm = WorkspaceManager(user_id=user_id)
    runs_dir = wm.root / "runs"
    if not runs_dir.exists():
        return []

    rows = []
    for run_dir in sorted(runs_dir.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        mp = run_dir / "run_manifest.json"
        if not mp.exists():
            continue
        try:
            data = json.loads(mp.read_text())
            rows.append({
                "run_id": data.get("run_id", run_dir.name),
                "title": data.get("title", run_dir.name),
                "domain": data.get("domain", ""),
                "timestamp": data.get("timestamp", ""),
                "has_eln": (run_dir / "ELN.md").exists(),
                "chat_session_count": len(data.get("chat_sessions", [])),
            })
        except Exception:
            continue
        if len(rows) >= limit:
            break
    return rows


@router.post("/runs", status_code=201)
async def create_run(body: CreateRunRequest) -> dict:
    wm = WorkspaceManager(user_id=body.user_id)
    run_id = str(uuid.uuid4())[:8]
    run_dir = wm.root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "run_id": run_id,
        "title": body.title,
        "domain": body.domain,
        "objective": body.objective,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "samples": [],
        "reagents": [],
        "controls": [],
        "deviations": [],
        "citations": [],
        "artifacts": [],
        "sop_refs": [],
        "parameters": {},
        "results_summary": None,
        "chat_sessions": [],
        "experiment_ids": [],
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2))
    return {"run_id": run_id, "run_dir": str(run_dir)}


@router.get("/runs/{run_id}")
async def get_run(run_id: str, user_id: str = "default") -> dict:
    wm = WorkspaceManager(user_id=user_id)
    mp = wm.root / "runs" / run_id / "run_manifest.json"
    if not mp.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    return json.loads(mp.read_text())


@router.get("/runs/{run_id}/citations")
async def get_citations(run_id: str, user_id: str = "default") -> list[dict]:
    wm = WorkspaceManager(user_id=user_id)
    run_dir = wm.root / "runs" / run_id
    # Citations live in the run manifest and in the session state
    # Return the raw citation_ids from the manifest for now
    mp = run_dir / "run_manifest.json"
    if not mp.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    data = json.loads(mp.read_text())
    return [{"citation_id": cid} for cid in data.get("citations", [])]


@router.get("/runs/{run_id}/eln")
async def get_eln(run_id: str, user_id: str = "default") -> dict:
    wm = WorkspaceManager(user_id=user_id)
    eln_path = wm.root / "runs" / run_id / "ELN.md"
    if not eln_path.exists():
        raise HTTPException(status_code=404, detail="ELN.md not found")
    return {"content": eln_path.read_text(encoding="utf-8")}
