"""LangGraph sub-graph for multi-agent scientific debate.

Nodes: generate_position → critique → red_team_attack → synthesize
Conditional edge: loop back if unresolved points remain and round < max_rounds.
"""
import uuid

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from eln.agents.debate.state import DebateState
from eln.skills import load_skill


def _invoke_role(model: BaseChatModel, role_skill: str, content: str) -> str:
    """Call a model with a SKILL.md system prompt and a content message."""
    system = load_skill(role_skill)
    messages = [SystemMessage(content=system), HumanMessage(content=content)]
    response = model.invoke(messages)
    return response.content if hasattr(response, "content") else str(response)


def build_debate_graph(
    model: BaseChatModel,
    tools: list | None = None,
) -> object:
    """Build and compile the debate sub-graph.

    Args:
        model: LLM to use for all debate participants.
        tools: Optional tools available to debate agents (e.g., search).

    Returns:
        Compiled LangGraph StateGraph.
    """

    def generate_position(state: DebateState) -> dict:
        """Planner generates an initial analytical position."""
        topic = state.get("topic", "unknown topic")
        hyp_set = state.get("hypothesis_set", {})
        hyp_summary = ""
        if hyp_set:
            hypotheses = hyp_set.get("hypotheses", [])
            if hypotheses:
                hyp_summary = "\n".join(
                    f"  H{i+1}: {h.get('statement', '')[:150]}"
                    for i, h in enumerate(hypotheses[:5])
                )
        content = (
            f"Analyze this scientific topic: {topic}\n\n"
            f"{'Hypotheses to evaluate:\n' + hyp_summary if hyp_summary else ''}\n\n"
            "Generate an initial analytical position with supporting evidence and key claims."
        )
        position = _invoke_role(model, "planner", content)
        from eln.models.debate import DebateRound
        round_obj = DebateRound(
            agent_name="planner",
            position=position,
            confidence=0.7,
        )
        rounds = list(state.get("rounds", []))
        rounds.append(round_obj.model_dump(mode="json"))
        return {"rounds": rounds, "current_round": state.get("current_round", 0) + 1}

    def critique_node(state: DebateState) -> dict:
        """Critic identifies weaknesses in the current position."""
        topic = state.get("topic", "unknown topic")
        last_position = ""
        rounds = state.get("rounds", [])
        if rounds:
            last_position = rounds[-1].get("position", "")

        content = (
            f"Topic: {topic}\n\n"
            f"Position to critique:\n{last_position[:1000]}\n\n"
            "Identify all weaknesses, evidence gaps, and logical flaws."
        )
        critique = _invoke_role(model, "critic", content)
        from eln.models.debate import DebateRound
        round_obj = DebateRound(
            agent_name="critic",
            position=critique,
            confidence=0.6,
        )
        rounds = list(rounds)
        rounds.append(round_obj.model_dump(mode="json"))
        return {"rounds": rounds, "current_round": state.get("current_round", 0) + 1}

    def red_team_attack(state: DebateState) -> dict:
        """Red team finds failure modes and counter-experiments."""
        topic = state.get("topic", "unknown topic")
        rounds = state.get("rounds", [])
        # Give red team the planner's position + critique
        context = "\n\n---\n\n".join(
            f"[{r.get('agent_name', '?')}]: {r.get('position', '')[:600]}"
            for r in rounds[-3:]
        )
        content = (
            f"Topic: {topic}\n\n"
            f"Prior analysis:\n{context}\n\n"
            "Attack this hypothesis. Find alternative explanations, failure modes, "
            "and propose killer experiments."
        )
        attack = _invoke_role(model, "red_team", content)
        from eln.models.debate import DebateRound
        round_obj = DebateRound(
            agent_name="red_team",
            position=attack,
            confidence=0.5,
        )
        rounds = list(rounds)
        rounds.append(round_obj.model_dump(mode="json"))
        return {"rounds": rounds, "current_round": state.get("current_round", 0) + 1}

    def synthesize_node(state: DebateState) -> dict:
        """Planner synthesizes the debate into consensus + recommendations."""
        topic = state.get("topic", "unknown topic")
        rounds = state.get("rounds", [])
        full_debate = "\n\n---\n\n".join(
            f"[{r.get('agent_name', '?')}]:\n{r.get('position', '')[:800]}"
            for r in rounds
        )
        content = (
            f"Topic: {topic}\n\n"
            f"Full debate transcript:\n{full_debate}\n\n"
            "Synthesize the debate. Identify:\n"
            "1. Points of consensus\n"
            "2. Unresolved disagreements\n"
            "3. A final experimental recommendation\n"
            "4. Updated confidence scores for each hypothesis (if applicable)\n\n"
            "Format as:\nCONSENSUS: ...\nUNRESOLVED: ...\nRECOMMENDATION: ..."
        )
        synthesis_text = _invoke_role(model, "planner", content)

        # Parse synthesis sections
        consensus_points: list[str] = []
        unresolved_points: list[str] = []
        recommendation = synthesis_text

        for line in synthesis_text.split("\n"):
            if line.startswith("CONSENSUS:"):
                consensus_points.append(line.removeprefix("CONSENSUS:").strip())
            elif line.startswith("UNRESOLVED:"):
                unresolved_points.append(line.removeprefix("UNRESOLVED:").strip())
            elif line.startswith("RECOMMENDATION:"):
                recommendation = line.removeprefix("RECOMMENDATION:").strip()

        from eln.models.debate import DebateSynthesis
        synthesis = DebateSynthesis(
            topic=topic,
            rounds=[],  # stored separately on the Debate model
            consensus_points=consensus_points or [synthesis_text[:200]],
            unresolved_points=unresolved_points,
            final_recommendation=recommendation,
        )
        return {"synthesis": synthesis.model_dump(mode="json")}

    def should_continue(state: DebateState) -> str:
        """Loop if unresolved points remain and we haven't hit max_rounds."""
        current = state.get("current_round", 0)
        max_r = state.get("max_rounds", 2)
        synthesis = state.get("synthesis") or {}
        unresolved = synthesis.get("unresolved_points", [])

        if current < max_r * 3 and unresolved:  # *3 because each round = 3 nodes
            return "continue"
        return "end"

    # Build graph
    graph = StateGraph(DebateState)
    graph.add_node("generate_position", generate_position)
    graph.add_node("critique", critique_node)
    graph.add_node("red_team_attack", red_team_attack)
    graph.add_node("synthesize", synthesize_node)

    graph.add_edge(START, "generate_position")
    graph.add_edge("generate_position", "critique")
    graph.add_edge("critique", "red_team_attack")
    graph.add_edge("red_team_attack", "synthesize")
    graph.add_conditional_edges(
        "synthesize",
        should_continue,
        {"continue": "critique", "end": END},
    )

    return graph.compile(checkpointer=MemorySaver())
