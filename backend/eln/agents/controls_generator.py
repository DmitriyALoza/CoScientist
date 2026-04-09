"""
Controls Generator subagent.

Generates controls checklists appropriate for the experiment's assay type.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from eln.skills import load_skill


def build_controls_generator(model: BaseChatModel, tools: list[BaseTool] | None = None):
    """Build the Controls Generator ReAct agent with SKILL.md prompt."""
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=load_skill("controls_generator"),
        name="controls_generator",
    )
