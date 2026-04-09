"""Hypothesis data models."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class Hypothesis(BaseModel):
    hypothesis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    statement: str
    novelty_score: float = 0.0       # 0–1
    feasibility_score: float = 0.0   # 0–1
    evidence_score: float = 0.0      # 0–1
    cost_estimate: float = 0.0       # USD
    rank: int = 0
    status: str = "proposed"         # "proposed" | "testing" | "supported" | "refuted"
    supporting_citations: list[str] = Field(default_factory=list)
    parent_hypothesis_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def composite_score(self) -> float:
        """Ranking formula: 0.3*N + 0.3*F + 0.3*E + 0.1*(1/log(cost+1))."""
        import math
        cost_term = 1.0 / math.log(self.cost_estimate + math.e)
        return (
            0.3 * self.novelty_score
            + 0.3 * self.feasibility_score
            + 0.3 * self.evidence_score
            + 0.1 * cost_term
        )


class HypothesisSet(BaseModel):
    set_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    debate_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def ranked(self) -> list[Hypothesis]:
        """Return hypotheses sorted by composite score descending."""
        ranked = sorted(self.hypotheses, key=lambda h: h.composite_score, reverse=True)
        for i, h in enumerate(ranked):
            h.rank = i + 1
        return ranked
