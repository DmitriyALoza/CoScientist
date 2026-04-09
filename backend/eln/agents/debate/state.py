"""State schema for the debate sub-graph."""
from typing import TypedDict


class DebateState(TypedDict, total=False):
    topic: str
    hypothesis_set: dict         # HypothesisSet data
    rounds: list[dict]           # list of DebateRound dicts
    current_round: int
    max_rounds: int
    synthesis: dict | None       # DebateSynthesis dict
