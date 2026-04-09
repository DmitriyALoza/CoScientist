"""LangChain @tool wrappers for the closed-loop experimentation engine.

Injected into experiment_manager. Initialized via set_experiment_store().
"""

import json

from langchain_core.tools import tool

from eln.workspace.experiment_store import ExperimentStore

_experiment_store: ExperimentStore | None = None


def set_experiment_store(store: ExperimentStore) -> None:
    global _experiment_store
    _experiment_store = store


def _get_store() -> ExperimentStore:
    if _experiment_store is None:
        raise RuntimeError("ExperimentStore not initialized. Call set_experiment_store() first.")
    return _experiment_store


@tool
def plan_experiment(
    hypothesis_id: str,
    protocol: str,
    expected_outcome: str,
    success_metric: str,
    parameters_json: str = "{}",
) -> str:
    """Plan a new experiment for a hypothesis.

    Args:
        hypothesis_id: ID of the hypothesis this experiment tests.
        protocol: Step-by-step experimental protocol.
        expected_outcome: What a successful result looks like.
        success_metric: Quantitative or qualitative success criterion.
        parameters_json: JSON dict of experimental parameters.

    Returns:
        Experiment ID and summary.
    """
    from eln.models.experiment import Experiment

    try:
        params = json.loads(parameters_json)
    except json.JSONDecodeError:
        params = {}

    # Find or create a loop for this hypothesis
    loop = _get_store().get_loop_for_hypothesis(hypothesis_id)
    if loop is None:
        from eln.models.experiment import ExperimentLoop
        loop = ExperimentLoop(hypothesis_id=hypothesis_id)
        _get_store().save_loop(loop)

    iteration = len(loop.experiments) + 1
    exp = Experiment(
        hypothesis_id=hypothesis_id,
        protocol=protocol,
        expected_outcome=expected_outcome,
        success_metric=success_metric,
        parameters=params,
        iteration=iteration,
    )
    loop.add_experiment(exp)
    _get_store().save_loop(loop)
    _get_store().save_experiment(exp)

    return (
        f"Experiment planned: {exp.experiment_id[:8]}\n"
        f"Hypothesis: {hypothesis_id[:8]}\n"
        f"Iteration: {iteration} / {loop.max_iterations}\n"
        f"Protocol: {protocol[:200]}\n"
        f"Expected: {expected_outcome[:150]}\n"
        f"Metric: {success_metric}"
    )


@tool
def record_result(experiment_id: str, result: str, status: str = "completed") -> str:
    """Record the result of a completed experiment.

    Args:
        experiment_id: The experiment ID (full or first 8 chars).
        result: Description of the actual experimental result.
        status: 'completed' or 'failed'.

    Returns:
        Confirmation and updated loop status.
    """
    from datetime import datetime

    exp = _get_store().load_experiment(experiment_id)
    if not exp:
        return f"No experiment found with ID '{experiment_id}'."

    exp.actual_result = result
    exp.status = status
    exp.completed_at = datetime.utcnow()
    _get_store().save_experiment(exp)

    loop = _get_store().get_loop_for_hypothesis(exp.hypothesis_id or "")
    loop_status = ""
    if loop:
        for i, e in enumerate(loop.experiments):
            if e.experiment_id == exp.experiment_id:
                loop.experiments[i] = exp
                break
        _get_store().save_loop(loop)
        loop_status = f"\nLoop: iteration {loop.current_iteration}/{loop.max_iterations} ({loop.status})"

    return f"Result recorded for experiment {experiment_id[:8]} ({status}).{loop_status}"


@tool
def get_experiment_history(hypothesis_id: str) -> str:
    """Get the full experiment history for a hypothesis.

    Args:
        hypothesis_id: The hypothesis ID to retrieve history for.

    Returns:
        Formatted history of all experiments for this hypothesis.
    """
    loop = _get_store().get_loop_for_hypothesis(hypothesis_id)
    if not loop or not loop.experiments:
        return f"No experiments found for hypothesis {hypothesis_id[:8]}."

    lines = [
        f"**Experiment History** for hypothesis {hypothesis_id[:8]}\n"
        f"Loop: {loop.loop_id[:8]} | Status: {loop.status} | "
        f"Iterations: {loop.current_iteration}/{loop.max_iterations}"
    ]
    for exp in loop.experiments:
        result_preview = (exp.actual_result or "pending")[:150]
        lines.append(
            f"\n**Iteration {exp.iteration}** [{exp.experiment_id[:8]}] — {exp.status}\n"
            f"  Protocol: {exp.protocol[:100]}\n"
            f"  Expected: {exp.expected_outcome[:100]}\n"
            f"  Result: {result_preview}"
        )
    if loop.learnings:
        lines.append("\n**Accumulated learnings:**")
        lines.extend(f"  • {l}" for l in loop.learnings)

    return "\n".join(lines)


@tool
def suggest_next_experiment(hypothesis_id: str) -> str:
    """Suggest the next experiment based on prior results and hypothesis.

    Args:
        hypothesis_id: The hypothesis ID to suggest a next experiment for.

    Returns:
        Suggested protocol adjustments and rationale.
    """
    loop = _get_store().get_loop_for_hypothesis(hypothesis_id)
    if not loop:
        return f"No experiment loop found for hypothesis {hypothesis_id[:8]}. Plan an initial experiment first."

    if loop.is_complete():
        return f"Loop is {loop.status}. No further experiments suggested."

    completed = [e for e in loop.experiments if e.status == "completed"]
    failed = [e for e in loop.experiments if e.status == "failed"]

    history_summary = ""
    for exp in loop.experiments[-3:]:  # Last 3
        history_summary += (
            f"  Iteration {exp.iteration} ({exp.status}): "
            f"Result: {(exp.actual_result or 'pending')[:150]}\n"
        )

    return (
        f"**Next Experiment Suggestion** for hypothesis {hypothesis_id[:8]}\n"
        f"Loop iteration: {loop.current_iteration + 1}/{loop.max_iterations}\n"
        f"Completed: {len(completed)} | Failed: {len(failed)}\n\n"
        f"Recent history:\n{history_summary}\n"
        "Based on the above, suggest:\n"
        "1. What parameter to change and why (based on prior results)\n"
        "2. Updated protocol step\n"
        "3. Revised expected outcome\n"
        "4. How this iteration moves toward confirming or refuting the hypothesis"
    )


@tool
def update_hypothesis_from_results(hypothesis_id: str, update_summary: str) -> str:
    """Update the status and learnings for a hypothesis based on experiment results.

    Args:
        hypothesis_id: The hypothesis ID to update.
        update_summary: Summary of what was learned and how it affects the hypothesis.

    Returns:
        Confirmation of the update.
    """
    loop = _get_store().get_loop_for_hypothesis(hypothesis_id)
    if not loop:
        return f"No loop found for hypothesis {hypothesis_id[:8]}."

    loop.learnings.append(update_summary)

    # Check convergence
    completed = [e for e in loop.experiments if e.status == "completed"]
    if len(completed) >= loop.max_iterations:
        loop.status = "converged"
    _get_store().save_loop(loop)

    return (
        f"Hypothesis {hypothesis_id[:8]} updated.\n"
        f"Learning added: {update_summary[:200]}\n"
        f"Total learnings: {len(loop.learnings)}\n"
        f"Loop status: {loop.status}"
    )
