"""
Agent harness — thin wrapper around build_supervisor_graph() for eval runs.

Sends one message per eval item and returns a structured EvalResult with
the model response, accumulated citations, tool trace, and cost metadata.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage


@dataclass
class EvalResult:
    item_id: str
    question: str
    response: str
    citations: list[dict] = field(default_factory=list)
    tool_trace: list[dict] = field(default_factory=list)
    agent_route: str = ""       # which agent(s) the supervisor invoked
    latency_ms: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost_usd: float = 0.0
    error: str | None = None


# Cost table (USD per 1k tokens, input/output) — update as pricing changes
_COST_TABLE: dict[str, tuple[float, float]] = {
    "claude-opus-4-6": (0.015, 0.075),
    "claude-sonnet-4-6": (0.003, 0.015),
    "claude-haiku-4-5-20251001": (0.00025, 0.00125),
    "gpt-4o": (0.005, 0.015),
    "gpt-4-turbo": (0.010, 0.030),
    "gemini-1.5-pro": (0.00125, 0.005),
    "gemini-2.0-flash": (0.000075, 0.0003),
}

_DEFAULT_TIMEOUT_S = 120


class AgentHarness:
    """Wraps the compiled supervisor graph for eval runs.

    The graph is built once and reused across all eval items.
    Each item gets its own thread_id so state doesn't bleed between items.
    """

    def __init__(
        self,
        main_model,
        supervisor_model=None,
        model_name: str = "claude-sonnet-4-6",
        workspace_path: Path | None = None,
        timeout_s: int = _DEFAULT_TIMEOUT_S,
    ):
        self.model_name = model_name
        self.timeout_s = timeout_s
        self._graph = self._build_graph(main_model, supervisor_model, workspace_path)

    def _build_graph(self, main_model, supervisor_model, workspace_path):
        from eln.agents.supervisor import build_supervisor_graph

        return build_supervisor_graph(
            main_model=main_model,
            supervisor_model=supervisor_model,
            workspace_path=workspace_path,
        )

    def run(self, item_id: str, question: str, mode: str = "normal") -> EvalResult:
        """Run a single eval item through the graph.

        Args:
            item_id: Unique identifier for this eval item.
            question: The question/prompt to send.
            mode: Graph mode — "normal", "validation", or "protocol".
        """
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        initial_state: dict[str, Any] = {
            "messages": [HumanMessage(content=question)],
            "mode": mode,
            "run_id": None,
            "citations": [],
            "tool_trace": [],
            "selected_template": None,
            "memory_context": [],
            "hypotheses": [],
            "debates": [],
            "experiments": [],
            "pending_images": [],
            "image_analyses": [],
        }

        start = time.monotonic()
        error: str | None = None
        response_text = ""
        citations: list[dict] = []
        tool_trace: list[dict] = []

        try:
            import signal

            def _timeout_handler(signum, frame):
                raise TimeoutError(f"Item {item_id} exceeded {self.timeout_s}s timeout")

            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(self.timeout_s)

            try:
                result = self._graph.invoke(initial_state, config=config)
            finally:
                signal.alarm(0)  # cancel alarm

            # Extract last assistant message
            messages = result.get("messages", [])
            for msg in reversed(messages):
                if hasattr(msg, "content") and not isinstance(msg.content, list):
                    response_text = str(msg.content)
                    break
                elif hasattr(msg, "content") and isinstance(msg.content, list):
                    # Handle multi-part content (e.g., tool use blocks)
                    text_parts = [p.get("text", "") for p in msg.content if isinstance(p, dict) and p.get("type") == "text"]
                    if text_parts:
                        response_text = " ".join(text_parts)
                        break

            citations = result.get("citations", [])
            tool_trace = result.get("tool_trace", [])

        except TimeoutError as e:
            error = str(e)
        except Exception as e:
            error = f"{type(e).__name__}: {e}"

        latency_ms = int((time.monotonic() - start) * 1000)

        # Estimate token cost from tool_trace metadata if available
        prompt_tokens, completion_tokens = _extract_token_counts(tool_trace)
        cost = _estimate_cost(self.model_name, prompt_tokens, completion_tokens)

        # Extract agent route from tool_trace
        agent_route = _extract_agent_route(tool_trace)

        return EvalResult(
            item_id=item_id,
            question=question,
            response=response_text,
            citations=citations,
            tool_trace=tool_trace,
            agent_route=agent_route,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            estimated_cost_usd=cost,
            error=error,
        )


def _extract_token_counts(tool_trace: list[dict]) -> tuple[int, int]:
    prompt_total = 0
    completion_total = 0
    for entry in tool_trace:
        meta = entry.get("metadata", {}) or {}
        prompt_total += meta.get("prompt_tokens", 0) or 0
        completion_total += meta.get("completion_tokens", 0) or 0
    return prompt_total, completion_total


def _estimate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    # Find matching entry (prefix match for versioned model names)
    rates = None
    for key, rate in _COST_TABLE.items():
        if model_name.startswith(key) or key.startswith(model_name.split("-20")[0]):
            rates = rate
            break
    if rates is None:
        return 0.0
    input_rate, output_rate = rates
    return round(
        (prompt_tokens / 1000) * input_rate + (completion_tokens / 1000) * output_rate,
        6,
    )


def _extract_agent_route(tool_trace: list[dict]) -> str:
    agents = []
    for entry in tool_trace:
        agent = entry.get("agent") or entry.get("subagent") or ""
        if agent and agent not in agents:
            agents.append(agent)
    return " → ".join(agents) if agents else "supervisor"


def build_harness(provider: str, model_name: str, workspace_path: Path | None = None, timeout_s: int = _DEFAULT_TIMEOUT_S) -> AgentHarness:
    """Factory that instantiates the right LangChain model for the provider."""
    main_model = _make_model(provider, model_name, temperature=0)
    supervisor_model = _make_haiku_supervisor(provider)
    return AgentHarness(
        main_model=main_model,
        supervisor_model=supervisor_model,
        model_name=model_name,
        workspace_path=workspace_path,
        timeout_s=timeout_s,
    )


def _make_model(provider: str, model_name: str, temperature: float = 0):
    from eln.config import settings

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model_name, api_key=settings.anthropic_api_key, temperature=temperature)
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name, api_key=settings.openai_api_key, temperature=temperature)
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model_name, google_api_key=settings.gemini_api_key, temperature=temperature)
    else:
        raise ValueError(f"Unknown provider: {provider!r}. Must be anthropic|openai|gemini")


def _make_haiku_supervisor(provider: str):
    """Use the cheapest/fastest model for supervisor routing."""
    _SUPERVISOR_MODELS = {
        "anthropic": ("anthropic", "claude-haiku-4-5-20251001"),
        "openai": ("openai", "gpt-4o-mini"),
        "gemini": ("gemini", "gemini-2.0-flash"),
    }
    p, m = _SUPERVISOR_MODELS.get(provider, ("anthropic", "claude-haiku-4-5-20251001"))
    return _make_model(p, m)
