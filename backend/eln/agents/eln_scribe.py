"""
ELN Scribe subagent.

Renders the RunManifest + gathered context into a structured ELN.md.
Has access to write_eln tool to persist the output to disk.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from eln.skills import load_skill


def build_eln_scribe(model: BaseChatModel, tools: list[BaseTool] | None = None):
    """Build the ELN Scribe ReAct agent with SKILL.md prompt and tools."""
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=load_skill("eln_scribe"),
        name="eln_scribe",
    )
