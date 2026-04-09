"""
Literature Scout subagent.

Finds papers via local KB + external search, extracts methods, produces citation objects.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from eln.skills import load_skill


def build_literature_scout(model: BaseChatModel, tools: list[BaseTool] | None = None):
    """Build the Literature Scout ReAct agent with SKILL.md prompt and tools."""
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=load_skill("literature_scout"),
        name="literature_scout",
    )
