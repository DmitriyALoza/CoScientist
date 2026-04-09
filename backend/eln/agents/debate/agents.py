"""Builder functions for debate participant agents."""

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from eln.skills import load_skill


def build_critic(model: BaseChatModel, tools: list[BaseTool] | None = None):
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=load_skill("critic"),
        name="critic",
    )


def build_red_team(model: BaseChatModel, tools: list[BaseTool] | None = None):
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=load_skill("red_team"),
        name="red_team",
    )


def build_planner(model: BaseChatModel, tools: list[BaseTool] | None = None):
    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=load_skill("planner"),
        name="planner",
    )
