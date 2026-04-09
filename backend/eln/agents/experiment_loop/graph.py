"""Experiment loop sub-graph (reserved for future async/interrupt-based use).

Currently the experiment loop is managed through experiment_manager's ReAct loop.
This module provides the graph builder for future closed-loop automation.
"""

from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from eln.agents.experiment_loop.state import LoopState


def build_experiment_loop_graph(model: BaseChatModel) -> object:
    """Build the experiment loop sub-graph.

    The loop follows: plan → analyze_result → update_hypothesis → decide_next → (loop or end)
    Results are injected via state (for automated pipelines) or through chat (for interactive use).
    """

    def plan_node(state: LoopState) -> dict:
        hypothesis = state.get("hypothesis", {})
        history = state.get("experiment_history", [])
        iteration = state.get("iteration", 1)

        from langchain_core.messages import HumanMessage, SystemMessage
        from eln.skills import load_skill

        content = (
            f"Hypothesis: {hypothesis.get('statement', 'not specified')}\n"
            f"Iteration: {iteration}\n"
            f"Prior experiments: {len(history)}\n\n"
            + (f"Last result: {history[-1].get('actual_result', 'none')}\n" if history else "")
            + "Plan the next experiment with specific protocol, parameters, and success metric."
        )
        messages = [
            SystemMessage(content=load_skill("experiment_planner")),
            HumanMessage(content=content),
        ]
        response = model.invoke(messages)
        plan_text = response.content if hasattr(response, "content") else str(response)

        from eln.models.experiment import Experiment
        exp = Experiment(
            hypothesis_id=hypothesis.get("hypothesis_id"),
            protocol=plan_text[:1000],
            expected_outcome="See protocol",
            success_metric="As defined in protocol",
            iteration=iteration,
        )
        return {"current_experiment": exp.model_dump(mode="json")}

    def analyze_result_node(state: LoopState) -> dict:
        current = state.get("current_experiment", {})
        result = current.get("actual_result", "")
        if not result:
            # No result yet — this iteration waits for user input via chat
            return {"should_continue": False}

        history = list(state.get("experiment_history", []))
        history.append(current)
        return {"experiment_history": history}

    def update_hypothesis_node(state: LoopState) -> dict:
        history = state.get("experiment_history", [])
        hypothesis = state.get("hypothesis", {})

        completed = [e for e in history if e.get("actual_result")]
        if not completed:
            return {}

        # Simple convergence check: if last result matches expected
        last = completed[-1]
        expected = last.get("expected_outcome", "")
        actual = last.get("actual_result", "")
        converging = bool(expected and actual and any(
            word in actual.lower() for word in expected.lower().split()[:3]
        ))

        updated_hyp = dict(hypothesis)
        if converging:
            updated_hyp["status"] = "testing"
        return {"hypothesis": updated_hyp}

    def decide_next(state: LoopState) -> str:
        iteration = state.get("iteration", 1)
        history = state.get("experiment_history", [])
        hypothesis = state.get("hypothesis", {})

        max_iter = 5
        if iteration >= max_iter:
            return "end"
        if not state.get("should_continue", True):
            return "end"
        # Continue if we have a result from the current experiment
        if len(history) >= iteration:
            return "continue"
        return "end"

    graph = StateGraph(LoopState)
    graph.add_node("plan_experiment", plan_node)
    graph.add_node("analyze_result", analyze_result_node)
    graph.add_node("update_hypothesis", update_hypothesis_node)

    graph.add_edge(START, "plan_experiment")
    graph.add_edge("plan_experiment", "analyze_result")
    graph.add_edge("analyze_result", "update_hypothesis")
    graph.add_conditional_edges(
        "update_hypothesis",
        decide_next,
        {"continue": "plan_experiment", "end": END},
    )

    return graph.compile(checkpointer=MemorySaver())
