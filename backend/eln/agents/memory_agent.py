"""Memory Agent subagent.

Stores and retrieves scientific knowledge across experiments
using the episodic store and knowledge graph.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from eln.skills import load_skill


def build_memory_agent(model: BaseChatModel, tools: list[BaseTool] | None = None):
    """Build the Memory Agent ReAct agent with SKILL.md prompt and tools."""
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=load_skill("memory_agent"),
        name="memory_agent",
    )
