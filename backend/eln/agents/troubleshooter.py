"""
Troubleshooter subagent.

Interactively diagnoses unexpected experimental results (Validation Mode).
Multi-turn conversation with structured TroubleshootingReport output.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from eln.skills import load_skill


def build_troubleshooter(model: BaseChatModel, tools: list[BaseTool] | None = None):
    """Build the Troubleshooter ReAct agent with SKILL.md prompt and tools."""
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=load_skill("troubleshooter"),
        name="troubleshooter",
    )
