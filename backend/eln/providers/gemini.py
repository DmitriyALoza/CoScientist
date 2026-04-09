"""
Google Gemini provider using langchain-google-genai.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from opentelemetry import trace

from eln.config import settings
from eln.providers.base import BaseProvider, LLMResponse
from eln.tracing import get_tracer

_DEFAULT_MODEL = "gemini-2.5-flash"


class GeminiProvider(BaseProvider):
    """LangChain-backed Google Gemini provider."""

    def __init__(self, model: str | None = None, **kwargs):
        self._model_name = model or _DEFAULT_MODEL
        self._llm = ChatGoogleGenerativeAI(
            model=self._model_name,
            google_api_key=settings.google_api_key or None,
            streaming=True,
            **kwargs,
        )

    @property
    def llm(self) -> ChatGoogleGenerativeAI:
        return self._llm

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    def with_model(self, model: str) -> "GeminiProvider":
        return GeminiProvider(model=model)

    async def chat(
        self,
        messages: list[dict],
        tools: list | None = None,
        response_format: dict | type | None = None,
        stream: bool = True,
    ) -> LLMResponse:
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span("llm.chat") as span:
            span.set_attribute("llm.provider", "gemini")
            span.set_attribute("llm.model", self._model_name)
            span.set_attribute("llm.stream", stream)

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
            input_tokens = output_tokens = 0

            try:
                if stream:
                    async for chunk in bound.astream(lc_messages):
                        if hasattr(chunk, "content") and chunk.content:
                            full_text += chunk.content
                        if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                            tool_calls.extend(chunk.tool_calls)
                        if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                            input_tokens = chunk.usage_metadata.get("input_tokens", 0)
                            output_tokens = chunk.usage_metadata.get("output_tokens", 0)
                else:
                    result = await bound.ainvoke(lc_messages)
                    full_text = result.content or ""
                    tool_calls = result.tool_calls or []
                    if hasattr(result, "usage_metadata") and result.usage_metadata:
                        input_tokens = result.usage_metadata.get("input_tokens", 0)
                        output_tokens = result.usage_metadata.get("output_tokens", 0)
            except Exception as exc:
                span.set_status(trace.StatusCode.ERROR, str(exc))
                span.record_exception(exc)
                raise

            span.set_attribute("llm.input_tokens", input_tokens)
            span.set_attribute("llm.output_tokens", output_tokens)

            from eln.audit.singleton import get_audit_logger
            _al = get_audit_logger()
            if _al:
                _al.log_llm_call(
                    provider="gemini",
                    model=self._model_name,
                    prompt=str(messages)[:500],
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )

            return LLMResponse(
                text=full_text,
                tool_calls=tool_calls,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=self._model_name,
                provider="gemini",
            )
