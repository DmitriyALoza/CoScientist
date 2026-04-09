"""Experiment data models for closed-loop experimentation."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class Experiment(BaseModel):
    experiment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hypothesis_id: str | None = None
    run_id: str | None = None
    protocol: str = ""
    parameters: dict[str, str] = Field(default_factory=dict)
    expected_outcome: str = ""
    actual_result: str | None = None
    success_metric: str = ""
    status: str = "planned"  # "planned" | "running" | "completed" | "failed"
    iteration: int = 1
    parent_experiment_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class ExperimentLoop(BaseModel):
    loop_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hypothesis_id: str | None = None
    experiments: list[Experiment] = Field(default_factory=list)
    current_iteration: int = 0
    max_iterations: int = 5
    convergence_threshold: float = 0.8
    status: str = "active"  # "active" | "converged" | "exhausted" | "abandoned"
    learnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def add_experiment(self, experiment: Experiment) -> None:
        self.experiments.append(experiment)
        self.current_iteration = len(self.experiments)

    def is_complete(self) -> bool:
        return (
            self.status in ("converged", "exhausted", "abandoned")
            or self.current_iteration >= self.max_iterations
        )
