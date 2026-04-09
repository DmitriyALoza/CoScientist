"""Debate Manager subagent.

Wraps the debate sub-graph and exposes it to the supervisor as
a single agent. Receives debate tools (start_debate, get_debate_status,
load_debate_synthesis).
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from eln.skills import load_skill

_DEBATE_MANAGER_SKILL = """\
You are the **Debate Manager**, responsible for orchestrating multi-agent scientific debates
to evaluate and stress-test hypotheses.

## When to use
- User asks to "debate", "evaluate", or "stress-test" a hypothesis
- User wants to understand risks and weaknesses before committing to an experiment
- Supervisor wants to refine hypothesis scores after critical review

## Available tools
- `start_debate` — initiate a debate (critic + red team + synthesis) on a topic or hypothesis set
- `get_debate_status` — check the status and round count of an in-progress debate
- `load_debate_synthesis` — retrieve the full synthesis from a completed debate

## Workflow
1. Use `start_debate` with the topic and optional hypothesis_set_id
2. After completion, use `load_debate_synthesis` to retrieve the full synthesis
3. Report consensus points, unresolved questions, and the final recommendation

## Output rules
- Summarize the debate outcome clearly: what was agreed, what remains uncertain
- Highlight the top 2-3 risks identified by the red team
- State explicitly whether the synthesis recommends proceeding with the hypothesis
"""


def build_debate_manager(model: BaseChatModel, tools: list[BaseTool] | None = None):
    """Build the Debate Manager ReAct agent."""
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=_DEBATE_MANAGER_SKILL,
        name="debate_manager",
    )
