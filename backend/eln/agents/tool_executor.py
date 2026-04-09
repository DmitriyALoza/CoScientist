"""Tool Executor subagent.

Dynamically selects and executes analysis, simulation, and cost
estimation tools based on the user's task.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from eln.skills import load_skill


def build_tool_executor(model: BaseChatModel, tools: list[BaseTool] | None = None):
    """Build the Tool Executor ReAct agent with SKILL.md prompt and all available tools."""
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=load_skill("tool_executor"),
        name="tool_executor",
    )
