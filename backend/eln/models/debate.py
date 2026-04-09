"""Debate data models."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DebateRound(BaseModel):
    round_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str  # "planner" | "critic" | "red_team"
    position: str
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.5  # 0–1
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DebateSynthesis(BaseModel):
    synthesis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    rounds: list[DebateRound] = Field(default_factory=list)
    consensus_points: list[str] = Field(default_factory=list)
    unresolved_points: list[str] = Field(default_factory=list)
    final_recommendation: str = ""
    hypothesis_updates: dict[str, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Debate(BaseModel):
    debate_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    hypothesis_set_id: str | None = None
    rounds: list[DebateRound] = Field(default_factory=list)
    synthesis: DebateSynthesis | None = None
    status: str = "pending"  # "pending" | "in_progress" | "complete"
    created_at: datetime = Field(default_factory=datetime.utcnow)
