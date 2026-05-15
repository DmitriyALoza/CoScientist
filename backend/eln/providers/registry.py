"""
LLM model registry: metadata and pricing for known models.

Pricing is in USD per million tokens and reflects public list prices.
Update when providers change their pricing.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model_id: str
    context_window: int
    supports_vision: bool
    supports_tools: bool
    input_cost_per_mtok: float   # USD per 1M input tokens
    output_cost_per_mtok: float  # USD per 1M output tokens
    display_name: str = ""

    def cost_usd(self, input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens * self.input_cost_per_mtok / 1_000_000
            + output_tokens * self.output_cost_per_mtok / 1_000_000
        )


MODEL_REGISTRY: dict[str, ModelSpec] = {
    # Anthropic
    "anthropic/claude-opus-4-6": ModelSpec(
        provider="anthropic",
        model_id="claude-opus-4-6",
        context_window=200_000,
        supports_vision=True,
        supports_tools=True,
        input_cost_per_mtok=15.0,
        output_cost_per_mtok=75.0,
        display_name="Claude Opus 4",
    ),
    "anthropic/claude-sonnet-4-6": ModelSpec(
        provider="anthropic",
        model_id="claude-sonnet-4-6",
        context_window=200_000,
        supports_vision=True,
        supports_tools=True,
        input_cost_per_mtok=3.0,
        output_cost_per_mtok=15.0,
        display_name="Claude Sonnet 4",
    ),
    "anthropic/claude-haiku-4-5-20251001": ModelSpec(
        provider="anthropic",
        model_id="claude-haiku-4-5-20251001",
        context_window=200_000,
        supports_vision=True,
        supports_tools=True,
        input_cost_per_mtok=0.80,
        output_cost_per_mtok=4.0,
        display_name="Claude Haiku 4.5",
    ),
    # OpenAI
    "openai/gpt-4o": ModelSpec(
        provider="openai",
        model_id="gpt-4o",
        context_window=128_000,
        supports_vision=True,
        supports_tools=True,
        input_cost_per_mtok=2.50,
        output_cost_per_mtok=10.0,
        display_name="GPT-4o",
    ),
    "openai/gpt-4o-mini": ModelSpec(
        provider="openai",
        model_id="gpt-4o-mini",
        context_window=128_000,
        supports_vision=True,
        supports_tools=True,
        input_cost_per_mtok=0.15,
        output_cost_per_mtok=0.60,
        display_name="GPT-4o Mini",
    ),
    "openai/gpt-4.1": ModelSpec(
        provider="openai",
        model_id="gpt-4.1",
        context_window=1_000_000,
        supports_vision=True,
        supports_tools=True,
        input_cost_per_mtok=2.0,
        output_cost_per_mtok=8.0,
        display_name="GPT-4.1",
    ),
    "openai/o3-mini": ModelSpec(
        provider="openai",
        model_id="o3-mini",
        context_window=200_000,
        supports_vision=False,
        supports_tools=True,
        input_cost_per_mtok=1.10,
        output_cost_per_mtok=4.40,
        display_name="o3-mini",
    ),
    # Google Gemini
    "gemini/gemini-2.5-pro": ModelSpec(
        provider="gemini",
        model_id="gemini-2.5-pro",
        context_window=2_000_000,
        supports_vision=True,
        supports_tools=True,
        input_cost_per_mtok=1.25,
        output_cost_per_mtok=5.0,
        display_name="Gemini 2.5 Pro",
    ),
    "gemini/gemini-2.5-flash": ModelSpec(
        provider="gemini",
        model_id="gemini-2.5-flash",
        context_window=1_000_000,
        supports_vision=True,
        supports_tools=True,
        input_cost_per_mtok=0.075,
        output_cost_per_mtok=0.30,
        display_name="Gemini 2.5 Flash",
    ),
}


def get_spec(provider: str, model: str) -> ModelSpec | None:
    """Look up a model spec by provider and model ID. Returns None for unknown models (e.g. Ollama)."""
    return MODEL_REGISTRY.get(f"{provider}/{model}")


def list_specs(provider: str | None = None) -> list[ModelSpec]:
    """Return all known model specs, optionally filtered by provider."""
    specs = list(MODEL_REGISTRY.values())
    if provider:
        specs = [s for s in specs if s.provider == provider]
    return specs
