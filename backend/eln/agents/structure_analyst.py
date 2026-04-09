"""Structure Analyst subagent.

Specialist agent for protein structure prediction and analysis via the
AlphaFold Database (EBI), pLDDT confidence interpretation, PAE domain
analysis, and ColabFold prediction submission (premium).
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from eln.skills import load_skill


def build_structure_analyst(model: BaseChatModel, tools: list[BaseTool] | None = None):
    """Build the Structure Analyst ReAct agent with SKILL.md prompt and AlphaFold tools."""
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=load_skill("structure_analyst"),
        name="structure_analyst",
    )
