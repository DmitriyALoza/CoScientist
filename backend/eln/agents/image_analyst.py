"""
Image Analyst subagent.

ReAct agent that classifies lab images, runs CV analysis tools,
optionally calls BiomedParse, saves artifacts, and returns structured reports.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from eln.skills import load_skill


def build_image_analyst(model: BaseChatModel, tools: list[BaseTool] | None = None):
    """Build the Image Analyst ReAct agent with SKILL.md prompt and tools."""
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=load_skill("image_analyst"),
        name="image_analyst",
    )
