"""State schema for the experiment loop sub-graph."""
from typing import TypedDict


class LoopState(TypedDict, total=False):
    loop_id: str
    hypothesis: dict          # Hypothesis dict
    current_experiment: dict  # Experiment dict
    experiment_history: list[dict]
    iteration: int
    should_continue: bool
