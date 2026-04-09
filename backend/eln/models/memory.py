"""Memory data models."""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    memory_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    memory_type: str  # "episodic" | "semantic" | "procedural"
    content: str
    source_run_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeNode(BaseModel):
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str
    node_type: str  # "concept" | "entity" | "result" | "hypothesis"
    properties: dict[str, Any] = Field(default_factory=dict)


class KnowledgeEdge(BaseModel):
    source_id: str
    target_id: str
    relation: str  # "supports" | "contradicts" | "related_to" | "derived_from"
    weight: float = 1.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
