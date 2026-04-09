"""Data Analyst subagent.

Specialized agent for statistical analysis, plot generation, fold change
computation, and R-based bioinformatics workflows. Reads artifacts from
the run folder and saves results/plots back as artifacts.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from eln.skills import load_skill


def build_data_analyst(model: BaseChatModel, tools: list[BaseTool] | None = None):
    """Build the Data Analyst ReAct agent with SKILL.md prompt and analysis tools."""
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=load_skill("data_analyst"),
        name="data_analyst",
    )
