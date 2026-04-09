from __future__ import annotations

from langchain_ollama import ChatOllama
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from eln.providers.base import BaseProvider, LLMResponse

_DEFAULT_MODEL = "llama3"

_VISION_MODELS = {"llava", "llava-phi3", "moondream", "bakllava", "minicpm-v"}


def _has_image_blocks(messages: list[dict]) -> bool:
    """Return True if any message contains an image_url content block."""
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "image_url":
                    return True
    return False


class OllamaProvider(BaseProvider):
    """LangChain-backed Ollama local model provider."""

    def __init__(self, model: str = _DEFAULT_MODEL, base_url: str = "http://localhost:11434", **kwargs):
        self._model = model
        self._base_url = base_url
        self._llm = ChatOllama(model=model, base_url=base_url, **kwargs)

    @property
    def llm(self) -> BaseChatModel:
        return self._llm

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    def with_model(self, model: str) -> "OllamaProvider":
        return OllamaProvider(model=model, base_url=self._base_url)

    async def chat(
        self,
        messages: list[dict],
        tools: list | None = None,
        response_format: dict | type | None = None,
        stream: bool = True,
    ) -> LLMResponse:
        # Warn if model likely doesn't support vision
        if _has_image_blocks(messages):
            model_base = self._model.split(":")[0].lower()
            if model_base not in _VISION_MODELS:
                import streamlit as st
                try:
                    st.warning(
                        f"Model '{self._model}' may not support images. "
                        f"Switch to a vision model (llava, llava-phi3, moondream, etc.) for best results."
                    )
                except Exception:
                    pass  # Not in a Streamlit context

        lc_messages = []
        for m in messages:
            role, content = m["role"], m["content"]
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            else:
                lc_messages.append(HumanMessage(content=content))

        bound = self._llm
        if tools:
            bound = bound.bind_tools(tools)

        full_text = ""
        tool_calls: list[dict] = []

        if stream:
            async for chunk in bound.astream(lc_messages):
                if hasattr(chunk, "content") and chunk.content:
                    full_text += chunk.content
                if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                    tool_calls.extend(chunk.tool_calls)
        else:
            result = await bound.ainvoke(lc_messages)
            full_text = result.content or ""
            tool_calls = result.tool_calls or []

        from eln.audit.singleton import get_audit_logger
        _al = get_audit_logger()
        if _al:
            _al.log_llm_call(
                provider="ollama",
                model=self._model,
                prompt=str(messages)[:500],
                input_tokens=0,
                output_tokens=0,
            )

        return LLMResponse(
            text=full_text,
            tool_calls=tool_calls,
            input_tokens=0,
            output_tokens=0,
            model=self._model,
            provider="ollama",
        )
