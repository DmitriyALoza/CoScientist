from eln.providers.base import BaseProvider, LLMResponse

__all__ = ["BaseProvider", "LLMResponse", "build_provider", "list_ollama_models"]

# Available providers and their default models
PROVIDERS = {
    "anthropic": {
        "models": ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
        "default": "claude-opus-4-6",
    },
    "openai": {
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "o3-mini"],
        "default": "gpt-4o",
    },
    "gemini": {
        "models": ["gemini-2.5-pro", "gemini-2.5-flash"],
        "default": "gemini-2.5-flash",
    },
    "ollama": {
        "models": [],  # populated dynamically at runtime
        "default": "llama3",
    },
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
