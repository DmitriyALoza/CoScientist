import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ArtifactType(StrEnum):
    CSV = "csv"
    PDF = "pdf"
    PPTX = "pptx"
    IMAGE = "image"
    TEXT = "text"
    OTHER = "other"


class CreatedBy(StrEnum):
    USER = "user"
    TOOL = "tool"
    AGENT = "agent"


class ArtifactRecord(BaseModel):
    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    path: str  # relative to run folder
    artifact_type: ArtifactType
    sha256: str
    created_by: CreatedBy = CreatedBy.USER
    created_at: datetime = Field(default_factory=datetime.utcnow)
    derived_text_path: str | None = None  # path to extracted text
    tool_provenance: dict | None = None  # tool call details if created by a tool
    notes: str | None = None
    image_type: str | None = None        # "western_blot" | "gel" | "microscopy" | ...
    analysis_summary: str | None = None  # 1-sentence CV tool output summary


class ArtifactManifest(BaseModel):
    run_id: str
    artifacts: list[ArtifactRecord] = Field(default_factory=list)

    def get(self, artifact_id: str) -> ArtifactRecord | None:
        for a in self.artifacts:
            if a.artifact_id == artifact_id:
                return a
        return None

    def add(self, record: ArtifactRecord) -> None:
        self.artifacts.append(record)
