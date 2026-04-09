from datetime import datetime

from pydantic import BaseModel, Field


class RunIndex(BaseModel):
    run_id: str
    title: str
    domain: str
    owner: str
    timestamp: datetime
    path: str  # absolute path to run folder


class WorkspaceSettings(BaseModel):
    workspace_id: str
    owner: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    default_provider: str = "anthropic"
    default_model: str = "claude-opus-4-6"
    supervisor_model: str = "claude-haiku-4-5-20251001"
    mcp_tool_allowlist: list[str] = Field(default_factory=list)
    runs: list[RunIndex] = Field(default_factory=list)
    last_run_id: str | None = None
