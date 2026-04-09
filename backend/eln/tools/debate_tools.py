"""LangChain @tool wrappers for the debate system.

Injected into debate_manager. Initialized via set_debate_store() and set_debate_graph().
"""

import json

from langchain_core.tools import tool

from eln.workspace.debate_store import DebateStore

_debate_store: DebateStore | None = None
_debate_graph = None  # compiled StateGraph — set by set_debate_graph()


def set_debate_store(store: DebateStore) -> None:
    global _debate_store
    _debate_store = store


def set_debate_graph(graph) -> None:
    global _debate_graph
    _debate_graph = graph


def _get_store() -> DebateStore:
    if _debate_store is None:
        raise RuntimeError("DebateStore not initialized. Call set_debate_store() first.")
    return _debate_store


@tool
def start_debate(topic: str, hypothesis_set_id: str = "", max_rounds: int = 2) -> str:
    """Start a multi-agent debate to evaluate a scientific topic or hypothesis set.

    Runs critic → red_team → synthesis rounds. Saves the debate to storage.

    Args:
        topic: The debate topic or hypothesis statement to evaluate.
        hypothesis_set_id: Optional ID of a hypothesis set to evaluate.
        max_rounds: Number of debate rounds (default 2, max 3).

    Returns:
        Debate ID and synthesis summary.
    """
    from eln.models.debate import Debate

    max_rounds = min(max(max_rounds, 1), 3)
    debate = Debate(topic=topic, hypothesis_set_id=hypothesis_set_id or None)

    if _debate_graph is not None:
        try:
            import uuid
            from eln.agents.debate.state import DebateState

            initial_state: DebateState = {
                "topic": topic,
                "hypothesis_set": {"set_id": hypothesis_set_id},
                "rounds": [],
                "current_round": 0,
                "max_rounds": max_rounds,
                "synthesis": None,
            }
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            result = _debate_graph.invoke(initial_state, config=config)

            debate.rounds = [
                r if isinstance(r, dict) else r.model_dump()
                for r in result.get("rounds", [])
            ]
            synthesis_data = result.get("synthesis")
            if synthesis_data:
                from eln.models.debate import DebateSynthesis
                if isinstance(synthesis_data, dict):
                    debate.synthesis = DebateSynthesis(**synthesis_data)
                else:
                    debate.synthesis = synthesis_data
            debate.status = "complete"
        except Exception as e:
            debate.status = "complete"
            from eln.models.debate import DebateSynthesis
            debate.synthesis = DebateSynthesis(
                topic=topic,
                final_recommendation=f"Debate graph error: {e}. Manual review required.",
            )
    else:
        debate.status = "complete"
        from eln.models.debate import DebateSynthesis
        debate.synthesis = DebateSynthesis(
            topic=topic,
            final_recommendation="Debate graph not initialized — provide your own synthesis.",
        )

    _get_store().save(debate)

    synthesis_text = ""
    if debate.synthesis:
        consensus = "\n".join(f"  ✓ {p}" for p in debate.synthesis.consensus_points[:3])
        unresolved = "\n".join(f"  ? {p}" for p in debate.synthesis.unresolved_points[:3])
        synthesis_text = (
            f"\nConsensus:\n{consensus or '  (none)'}\n"
            f"Unresolved:\n{unresolved or '  (none)'}\n"
            f"Recommendation: {debate.synthesis.final_recommendation[:300]}"
        )

    return (
        f"Debate completed: {debate.debate_id[:8]}\n"
        f"Topic: {topic[:100]}\n"
        f"Rounds: {len(debate.rounds)}\n"
        f"{synthesis_text}"
    )


@tool
def get_debate_status(debate_id: str) -> str:
    """Get the current status and round count of a debate.

    Args:
        debate_id: The debate ID (full or first 8 chars).

    Returns:
        Debate status, round count, and synthesis summary.
    """
    debate = _get_store().load(debate_id)
    if not debate:
        return f"No debate found with ID starting with '{debate_id}'."
    rounds_summary = f"{len(debate.rounds)} rounds completed"
    synth = ""
    if debate.synthesis:
        synth = f"\nRecommendation: {debate.synthesis.final_recommendation[:200]}"
    return f"Debate {debate.debate_id[:8]}: {debate.status} | {rounds_summary}{synth}"


@tool
def load_debate_synthesis(debate_id: str) -> str:
    """Load the full synthesis from a completed debate.

    Args:
        debate_id: The debate ID (full or first 8 chars).

    Returns:
        Full synthesis including consensus, unresolved points, and recommendation.
    """
    debate = _get_store().load(debate_id)
    if not debate:
        return f"No debate found with ID '{debate_id}'."
    if not debate.synthesis:
        return f"Debate {debate_id[:8]} has no synthesis yet (status: {debate.status})."

    s = debate.synthesis
    consensus = "\n".join(f"  • {p}" for p in s.consensus_points)
    unresolved = "\n".join(f"  • {p}" for p in s.unresolved_points)
    updates = json.dumps(s.hypothesis_updates, indent=2) if s.hypothesis_updates else "none"

    return (
        f"**Debate Synthesis** [{debate.debate_id[:8]}]\n"
        f"Topic: {s.topic}\n\n"
        f"**Consensus:**\n{consensus or '  (none identified)'}\n\n"
        f"**Unresolved:**\n{unresolved or '  (none)'}\n\n"
        f"**Recommendation:**\n{s.final_recommendation}\n\n"
        f"**Hypothesis score updates:**\n{updates}"
    )
