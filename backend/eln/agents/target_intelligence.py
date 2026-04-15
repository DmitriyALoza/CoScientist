"""Target Intelligence agent builder."""

from __future__ import annotations

from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent


def build_target_intelligence(
    model: BaseChatModel,
    tools: list[BaseTool] | None = None,
) -> object:
    """Build the Target Intelligence ReAct agent."""
    skill_path = Path(__file__).parent.parent / "skills" / "target_intelligence" / "SKILL.md"
    prompt = skill_path.read_text()

    return create_react_agent(
        model=model,
        tools=tools or [],
        prompt=prompt,
        name="target_intelligence",
    )
