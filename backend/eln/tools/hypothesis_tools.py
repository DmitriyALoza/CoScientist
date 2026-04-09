"""LangChain @tool wrappers for hypothesis generation and management.

Injected into hypothesis_generator. Initialized via set_hypothesis_store().
"""

import json

from langchain_core.tools import tool

from eln.workspace.hypothesis_store import HypothesisStore

_hypothesis_store: HypothesisStore | None = None


def set_hypothesis_store(store: HypothesisStore) -> None:
    global _hypothesis_store
    _hypothesis_store = store


def _get_store() -> HypothesisStore:
    if _hypothesis_store is None:
        raise RuntimeError("HypothesisStore not initialized. Call set_hypothesis_store() first.")
    return _hypothesis_store


@tool
def generate_hypotheses(query: str, context: str = "", n: int = 3) -> str:
    """Generate a structured set of scientific hypotheses for a research question.

    Args:
        query: The research question or topic to generate hypotheses for.
        context: Optional context (e.g., prior results, constraints).
        n: Number of hypotheses to generate (default 3, min 3).

    Returns:
        JSON schema for ≥3 ranked hypotheses with scoring rubric applied.
    """
    # This tool is a scaffold — the LLM agent fills it with content.
    # The actual generation happens via the LLM's reasoning in the agent loop.
    n = max(n, 3)
    return (
        f"Generate exactly {n} hypotheses for: '{query}'\n"
        f"Context: {context or 'none provided'}\n\n"
        "For each hypothesis produce JSON with:\n"
        "  statement, novelty_score (0-1), feasibility_score (0-1), "
        "evidence_score (0-1), cost_estimate (USD), supporting_citations (list)\n\n"
        "Ranking formula: 0.3*N + 0.3*F + 0.3*E + 0.1*(1/log(cost+e))\n"
        "Ensure hypotheses are diverse and non-overlapping."
    )


@tool
def rank_hypotheses(hypotheses_json: str) -> str:
    """Rank a list of hypotheses by composite score.

    Args:
        hypotheses_json: JSON array of hypothesis objects with scoring fields.

    Returns:
        Ranked hypotheses with composite scores.
    """
    import math

    try:
        data = json.loads(hypotheses_json)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"

    scored = []
    for i, h in enumerate(data):
        n = float(h.get("novelty_score", 0))
        f_s = float(h.get("feasibility_score", 0))
        e_s = float(h.get("evidence_score", 0))
        cost = float(h.get("cost_estimate", 0))
        score = 0.3 * n + 0.3 * f_s + 0.3 * e_s + 0.1 / math.log(cost + math.e)
        scored.append((score, i + 1, h))

    scored.sort(key=lambda x: x[0], reverse=True)
    lines = ["**Ranked Hypotheses** (by composite score):"]
    for rank, (score, orig_rank, h) in enumerate(scored, 1):
        lines.append(
            f"\n#{rank} (score: {score:.3f}) — {h.get('statement', 'N/A')[:120]}\n"
            f"  Novelty: {h.get('novelty_score', 0):.2f} | "
            f"Feasibility: {h.get('feasibility_score', 0):.2f} | "
            f"Evidence: {h.get('evidence_score', 0):.2f} | "
            f"Cost: ${h.get('cost_estimate', 0):.0f}"
        )
    return "\n".join(lines)


@tool
def save_hypothesis_set(query: str, hypotheses_json: str) -> str:
    """Save a hypothesis set to persistent storage.

    Args:
        query: The research question that generated these hypotheses.
        hypotheses_json: JSON array of hypothesis objects.

    Returns:
        Confirmation with the set ID.
    """
    import json
    import math

    from eln.models.hypothesis import Hypothesis, HypothesisSet

    try:
        data = json.loads(hypotheses_json)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"

    hypotheses = []
    for h in data:
        try:
            hyp = Hypothesis(
                statement=h.get("statement", ""),
                novelty_score=float(h.get("novelty_score", 0)),
                feasibility_score=float(h.get("feasibility_score", 0)),
                evidence_score=float(h.get("evidence_score", 0)),
                cost_estimate=float(h.get("cost_estimate", 0)),
                supporting_citations=h.get("supporting_citations", []),
                status=h.get("status", "proposed"),
            )
            hypotheses.append(hyp)
        except Exception as e:
            return f"Error parsing hypothesis: {e}"

    h_set = HypothesisSet(query=query, hypotheses=hypotheses)
    # Assign ranks
    ranked = h_set.ranked()
    h_set.hypotheses = ranked

    _get_store().save(h_set)
    return f"Saved hypothesis set {h_set.set_id[:8]} with {len(hypotheses)} hypotheses."


@tool
def load_hypothesis_history(limit: int = 5) -> str:
    """Load recent hypothesis sets from storage.

    Args:
        limit: Max number of sets to return (default 5).

    Returns:
        Summary of recent hypothesis sets.
    """
    sets = _get_store().list(limit=limit)
    if not sets:
        return "No hypothesis sets found in storage."
    lines = []
    for h_set in sets:
        top = h_set.ranked()[0] if h_set.hypotheses else None
        top_stmt = top.statement[:100] if top else "N/A"
        lines.append(
            f"[{h_set.set_id[:8]}] {h_set.created_at.strftime('%Y-%m-%d')} "
            f"— {len(h_set.hypotheses)} hypotheses | Query: {h_set.query[:80]}\n"
            f"  Top: {top_stmt}"
        )
    return "\n\n".join(lines)
