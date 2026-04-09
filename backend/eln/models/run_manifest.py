import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ChatSession(BaseModel):
    thread_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0
    first_message: str | None = None  # first user message, truncated to 80 chars


class Domain(StrEnum):
    FLOW_CYTOMETRY = "flow_cytometry"
    IHC = "ihc"
    CELL_CULTURE = "cell_culture"
    IMAGING = "imaging"
    WET_LAB = "wet_lab"
    OTHER = "other"


class Reagent(BaseModel):
    name: str
    vendor: str
    catalog_number: str
    lot_number: str
    expiry: datetime | None = None
    concentration: str | None = None
    notes: str | None = None


class Sample(BaseModel):
    sample_id: str
    description: str
    source: str | None = None
    passage: int | None = None
    notes: str | None = None


class Control(BaseModel):
    name: str
    type: str  # "positive", "negative", "isotype", etc.
    required: bool = True
    completed: bool = False
    notes: str | None = None


class Deviation(BaseModel):
    description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    impact: str | None = None


class RunManifest(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    owner: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    domain: Domain = Domain.WET_LAB
    objective: str
    hypothesis: str | None = None
    samples: list[Sample] = Field(default_factory=list)
    reagents: list[Reagent] = Field(default_factory=list)
    sop_refs: list[str] = Field(default_factory=list)  # citation_ids
    parameters: dict[str, str] = Field(default_factory=dict)
    deviations: list[Deviation] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)  # artifact_ids
    controls: list[Control] = Field(default_factory=list)
    results_summary: str | None = None
    citation_ids: list[str] = Field(default_factory=list)
    active_thread_id: str | None = None
    chat_sessions: list[ChatSession] = Field(default_factory=list)
    experiment_ids: list[str] = Field(default_factory=list)
