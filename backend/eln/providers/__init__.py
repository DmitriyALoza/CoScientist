from eln.providers.base import BaseProvider, LLMResponse
from eln.providers.registry import MODEL_REGISTRY, ModelSpec, ModelTier, get_spec, get_tier_model, list_specs

__all__ = [
    "BaseProvider",
    "LLMResponse",
    "MODEL_REGISTRY",
    "ModelSpec",
    "ModelTier",
    "PROVIDERS",
    "build_provider",
    "get_spec",
    "get_tier_model",
    "list_ollama_models",
    "list_specs",
]

# Derived from MODEL_REGISTRY — single source of truth for available models.
# Ollama models are dynamic and appended at runtime via list_ollama_models().
_PROVIDER_DEFAULTS = {
    "anthropic": "claude-opus-4-6",
    "openai": "gpt-4o",
    "gemini": "gemini-2.5-flash",
    "ollama": "llama3",
}

PROVIDERS: dict[str, dict] = {
    provider: {
        "models": [s.model_id for s in list_specs(provider)],
        "default": _PROVIDER_DEFAULTS[provider],
    }
    for provider in _PROVIDER_DEFAULTS
}


def list_ollama_models(base_url: str = "http://localhost:11434") -> list[str]:
    """Query Ollama's /api/tags endpoint. Returns [] if Ollama isn't running."""
    import httpx

    try:
        resp = httpx.get(f"{base_url}/api/tags", timeout=2.0)
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        return []


def build_provider(name: str, model: str | None = None) -> BaseProvider:
    """Factory: return the right provider by name."""
    if name == "anthropic":
        from eln.providers.anthropic import AnthropicProvider

        return AnthropicProvider(model=model)
    elif name == "openai":
        from eln.providers.openai import OpenAIProvider

        return OpenAIProvider(model=model)
    elif name == "gemini":
        from eln.providers.gemini import GeminiProvider

        return GeminiProvider(model=model)
    elif name == "ollama":
        from eln.providers.ollama import OllamaProvider
        from eln.config import settings

        return OllamaProvider(model=model or "llama3", base_url=settings.ollama_base_url)
    else:
        raise ValueError(f"Unknown provider: {name!r}. Supported: {list(PROVIDERS.keys())}")
