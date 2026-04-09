"""Experiment Manager subagent.

Manages closed-loop experimentation: planning experiments, recording results,
suggesting iterations, and updating hypothesis status based on accumulated evidence.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from eln.skills import load_skill


def build_experiment_manager(model: BaseChatModel, tools: list[BaseTool] | None = None):
    """Build the Experiment Manager ReAct agent with SKILL.md prompt and tools."""
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=load_skill("experiment_planner"),
        name="experiment_manager",
    )
