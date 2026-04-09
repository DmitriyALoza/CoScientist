"""
CoScientist FastAPI backend.

Wraps the existing ELN++ agent system with REST + WebSocket endpoints.
Run with:  uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import chat, documents, experiments, hypotheses, metrics, workspace


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown."""
    # Ensure workspaces root exists
    from eln.config import settings
    settings.workspaces_root.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="CoScientist API",
    version="1.0.0",
    description="AI Co-Scientist for Biology — FastAPI backend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router,        prefix="/api")
app.include_router(workspace.router,   prefix="/api")
app.include_router(hypotheses.router,  prefix="/api")
app.include_router(experiments.router, prefix="/api")
app.include_router(documents.router,   prefix="/api")
app.include_router(metrics.router,     prefix="/api")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "service": "coscientist-api"}
