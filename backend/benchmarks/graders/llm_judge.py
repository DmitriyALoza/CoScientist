"""
LLM-as-judge grader for free-text troubleshooting and SOP adaptation outputs.

Uses Claude Haiku as the judge with a structured rubric:
  systematic        0-3   Does the response follow a systematic diagnostic approach?
  controls_checked  0-2   Does it check/mention relevant controls?
  hypotheses_ranked 0-2   Are root-cause hypotheses ranked or prioritised?
  next_steps        0-3   Are actionable next steps provided?

Max score: 10
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

_RUBRIC_PROMPT = """\
You are a senior lab scientist evaluating an AI assistant's response to an experimental troubleshooting question.

Score the response on the following rubric. Reply with ONLY a JSON object — no prose.

Rubric:
  "systematic":        0-3  (0=no structure, 1=some structure, 2=clear steps, 3=thorough systematic diagnosis)
  "controls_checked":  0-2  (0=not mentioned, 1=briefly mentioned, 2=critically evaluated)
  "hypotheses_ranked": 0-2  (0=none, 1=listed but not ranked, 2=ranked by likelihood with rationale)
  "next_steps":        0-3  (0=none, 1=vague, 2=specific but incomplete, 3=specific and actionable)
  "justification":     string (1-2 sentence explanation)

Question: {question}

Response to evaluate:
{response}

JSON output only:"""


@dataclass
class LLMJudgeResult:
    systematic: int
    controls_checked: int
    hypotheses_ranked: int
    next_steps: int
    total: int
    justification: str
    raw_judge_response: str


def grade(question: str, response: str, judge_model=None) -> LLMJudgeResult:
    """Grade a troubleshooting response using Claude Haiku as a judge.

    Args:
        question: The original troubleshooting question.
        response: The model's response to evaluate.
        judge_model: An instantiated LangChain ChatModel. If None, builds one
                     from the current environment settings.
    """
    if judge_model is None:
        judge_model = _build_default_judge()

    prompt = _RUBRIC_PROMPT.format(question=question[:1000], response=response[:3000])

    from langchain_core.messages import HumanMessage

    msg = judge_model.invoke([HumanMessage(content=prompt)])
    raw = msg.content if hasattr(msg, "content") else str(msg)

    scores = _parse_scores(raw)

    total = (
        scores.get("systematic", 0)
        + scores.get("controls_checked", 0)
        + scores.get("hypotheses_ranked", 0)
        + scores.get("next_steps", 0)
    )

    return LLMJudgeResult(
        systematic=scores.get("systematic", 0),
        controls_checked=scores.get("controls_checked", 0),
        hypotheses_ranked=scores.get("hypotheses_ranked", 0),
        next_steps=scores.get("next_steps", 0),
        total=total,
        justification=scores.get("justification", ""),
        raw_judge_response=raw[:500],
    )


def _parse_scores(raw: str) -> dict:
    # Try to extract JSON from the response
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
        return {
            "systematic": _clamp(data.get("systematic", 0), 0, 3),
            "controls_checked": _clamp(data.get("controls_checked", 0), 0, 2),
            "hypotheses_ranked": _clamp(data.get("hypotheses_ranked", 0), 0, 2),
            "next_steps": _clamp(data.get("next_steps", 0), 0, 3),
            "justification": str(data.get("justification", "")),
        }
    except (json.JSONDecodeError, TypeError):
        return {}


def _clamp(value, lo, hi):
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return lo


def _build_default_judge():
    from eln.config import settings
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=settings.anthropic_api_key,
        max_tokens=512,
    )
