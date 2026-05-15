"""
LLM model registry: metadata and pricing for known models.

Pricing is in USD per million tokens and reflects public list prices.
Update when providers change their pricing.
"""

from dataclasses import dataclass
from enum import Enum


class ModelTier(str, Enum):
    """Cost/capability tier used to route agents to the right model automatically."""
    LITE = "lite"        # routing, retrieval, simple ops (e.g. Haiku, gpt-4o-mini)
    STANDARD = "standard"  # most analytical work (e.g. Sonnet, gpt-4o)
    PREMIUM = "premium"  # deep reasoning: hypothesis gen, debate (e.g. Opus, gpt-4.1)


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model_id: str
    context_window: int
    supports_vision: bool
    supports_tools: bool
    input_cost_per_mtok: float   # USD per 1M input tokens
    output_cost_per_mtok: float  # USD per 1M output tokens
    tier: ModelTier = ModelTier.STANDARD
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
        tier=ModelTier.PREMIUM,
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
        tier=ModelTier.STANDARD,
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
        tier=ModelTier.LITE,
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
        tier=ModelTier.STANDARD,
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
        tier=ModelTier.LITE,
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
        tier=ModelTier.PREMIUM,
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
        tier=ModelTier.PREMIUM,
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
        tier=ModelTier.PREMIUM,
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
        tier=ModelTier.LITE,
        display_name="Gemini 2.5 Flash",
    ),
}

# Default model per provider per tier. Used to auto-assign models to agents
# without requiring the caller to specify all three model names explicitly.
_PROVIDER_TIER_DEFAULTS: dict[str, dict[ModelTier, str]] = {
    "anthropic": {
        ModelTier.LITE: "claude-haiku-4-5-20251001",
        ModelTier.STANDARD: "claude-sonnet-4-6",
        ModelTier.PREMIUM: "claude-opus-4-6",
    },
    "openai": {
        ModelTier.LITE: "gpt-4o-mini",
        ModelTier.STANDARD: "gpt-4o",
        ModelTier.PREMIUM: "gpt-4.1",
    },
    "gemini": {
        # Gemini has no distinct mid-tier; flash covers both LITE and STANDARD
        ModelTier.LITE: "gemini-2.5-flash",
        ModelTier.STANDARD: "gemini-2.5-flash",
        ModelTier.PREMIUM: "gemini-2.5-pro",
    },
    "ollama": {
        # Local models have no cost; user picks their own model
        ModelTier.LITE: "llama3",
        ModelTier.STANDARD: "llama3",
        ModelTier.PREMIUM: "llama3",
    },
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


def get_tier_model(provider: str, tier: ModelTier) -> str | None:
    """Return the default model ID for a given provider + tier, or None if unknown."""
    return _PROVIDER_TIER_DEFAULTS.get(provider, {}).get(tier)
