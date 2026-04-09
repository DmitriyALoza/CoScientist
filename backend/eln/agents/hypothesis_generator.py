"""Hypothesis Generator subagent.

Generates, scores, and ranks scientific hypotheses from research questions.
Gets literature + memory tools for evidence scoring.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from eln.skills import load_skill


def build_hypothesis_generator(model: BaseChatModel, tools: list[BaseTool] | None = None):
    """Build the Hypothesis Generator ReAct agent with SKILL.md prompt and tools."""
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=load_skill("hypothesis_generator"),
        name="hypothesis_generator",
    )
