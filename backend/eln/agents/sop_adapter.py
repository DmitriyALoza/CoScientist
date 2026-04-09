"""
SOP Adapter subagent.

Generates experiment-specific protocol addenda with diffs and risk flags.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from eln.skills import load_skill


def build_sop_adapter(model: BaseChatModel, tools: list[BaseTool] | None = None):
    """Build the SOP Adapter ReAct agent with SKILL.md prompt and tools."""
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=load_skill("sop_adapter"),
        name="sop_adapter",
    )
