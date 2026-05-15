"""
LangChain callback handler for per-session cost tracking and budget enforcement.

Intercepts every LLM call made inside a LangGraph graph (which bypasses
BaseProvider.chat()), extracts token usage from the LLMResult, looks up
pricing in the model registry, and accumulates cost broken down by tier
(lite / standard / premium).

If max_budget_usd > 0, raises BudgetExceededError when the running total
crosses the limit — LangGraph propagates this as a graph execution error.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


class BudgetExceededError(Exception):
    """Raised when a session's running cost exceeds the configured budget."""


class CostCallbackHandler(BaseCallbackHandler):
    """Tracks LLM call costs and optionally enforces a per-session budget."""

    def __init__(self, provider: str, max_budget_usd: float = 0.0) -> None:
        super().__init__()
        self.provider = provider
        self.max_budget_usd = max_budget_usd
        self.total_cost_usd: float = 0.0
        self.by_tier: dict[str, float] = {}
        # run_id → model name, populated in on_llm_start
        self._run_model: dict[str, str] = {}

    # ------------------------------------------------------------------
    # LangChain callback hooks
    # ------------------------------------------------------------------

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        # Extract model name from the serialized LangChain model dict.
        # Anthropic / Gemini use "model"; OpenAI uses "model_name".
        kw = serialized.get("kwargs", {})
        model = kw.get("model") or kw.get("model_name") or serialized.get("name", "")
        self._run_model[str(run_id)] = model

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        model = self._run_model.pop(str(run_id), "")

        # --- Extract token counts (multi-provider) ---
        input_tokens = output_tokens = 0
        if response.llm_output:
            usage = response.llm_output.get("token_usage") or response.llm_output.get("usage", {})
            input_tokens = usage.get("prompt_tokens") or usage.get("input_tokens", 0)
            output_tokens = usage.get("completion_tokens") or usage.get("output_tokens", 0)
            # Also try to refine the model name from the response if we didn't get it
            if not model:
                model = (
                    response.llm_output.get("model_name")
                    or response.llm_output.get("model", "")
                )

        # Fallback: Anthropic streaming stores usage in generation_info
        if not input_tokens and response.generations:
            gen_info = getattr(response.generations[0][0], "generation_info", None) or {}
            usage = gen_info.get("usage") or {}
            input_tokens = usage.get("input_tokens", input_tokens)
            output_tokens = usage.get("output_tokens", output_tokens)

        if not (input_tokens or output_tokens):
            return

        # --- Look up spec and compute cost ---
        from eln.providers.registry import get_spec

        spec = get_spec(self.provider, model)
        if not spec:
            return

        cost = spec.cost_usd(input_tokens, output_tokens)
        self.total_cost_usd += cost
        tier_key = spec.tier.value
        self.by_tier[tier_key] = self.by_tier.get(tier_key, 0.0) + cost

        # Write to audit trail with actual cost
        from eln.audit.singleton import get_audit_logger
        _al = get_audit_logger()
        if _al:
            _al.log_llm_call(
                provider=self.provider,
                model=model,
                prompt="",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
            )

        # Budget enforcement — raises and propagates through the graph
        if self.max_budget_usd > 0 and self.total_cost_usd > self.max_budget_usd:
            raise BudgetExceededError(
                f"Session budget of ${self.max_budget_usd:.4f} exceeded "
                f"(spent ${self.total_cost_usd:.4f})"
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def summary(self) -> dict:
        """Cost summary suitable for sending to the frontend."""
        return {
            "total_usd": round(self.total_cost_usd, 6),
            "by_tier": {k: round(v, 6) for k, v in self.by_tier.items()},
        }
