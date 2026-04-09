"""
LangChain → OpenTelemetry callback handler.

Converts LangChain callback events into OTel spans so that a Jaeger
(or any OTLP-compatible) backend shows the full trace tree:

    chat.generate_response
      └── agent.<name>          (on_chain_start/end)
            └── tool.<name>     (on_tool_start/end)
            └── llm.call        (on_llm_start/end)

Also writes to the AuditLogger singleton when present.
"""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry.trace import Span, StatusCode

from eln.tracing.setup import get_tracer


class OTelCallbackHandler(BaseCallbackHandler):
    """
    Translates LangChain run events into OTel child spans.

    Each span is stored in ``_spans`` keyed by ``str(run_id)`` so that
    start/end callbacks can pair correctly.  Parent context is resolved
    via ``parent_run_id`` to achieve proper nesting.
    """

    def __init__(self) -> None:
        super().__init__()
        # run_id → (span, wall_clock_start)
        self._spans: dict[str, tuple[Span, float]] = {}
        # run_id → span name (stored separately so we don't rely on span.name)
        self._names: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_ctx(self, parent_run_id: UUID | None) -> Any:
        """Return the OTel context to use when starting a child span."""
        if parent_run_id is not None:
            entry = self._spans.get(str(parent_run_id))
            if entry:
                parent_span, _ = entry
                return trace.set_span_in_context(parent_span)
        return otel_context.get_current()

    def _start_span(self, name: str, run_id: UUID, parent_run_id: UUID | None) -> None:
        tracer = get_tracer("eln.tracing.callback")
        ctx = self._get_ctx(parent_run_id)
        span = tracer.start_span(name, context=ctx)
        key = str(run_id)
        self._spans[key] = (span, time.perf_counter())
        self._names[key] = name

    def _end_span(self, run_id: UUID, extra_attrs: dict | None = None) -> str | None:
        """End the span for run_id and return its registered name (or None)."""
        key = str(run_id)
        entry = self._spans.pop(key, None)
        name = self._names.pop(key, None)
        if entry is None:
            return name
        span, t0 = entry
        latency_ms = (time.perf_counter() - t0) * 1000
        span.set_attribute("latency_ms", round(latency_ms, 2))
        if extra_attrs:
            for k, v in extra_attrs.items():
                span.set_attribute(k, v)
        span.end()
        return name

    # ------------------------------------------------------------------
    # Chain (agent / supervisor) events
    # ------------------------------------------------------------------

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        name = serialized.get("name") or serialized.get("id", ["unknown"])[-1]
        self._start_span(f"agent.{name}", run_id, parent_run_id)

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._end_span(run_id)

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        key = str(run_id)
        entry = self._spans.pop(key, None)
        self._names.pop(key, None)
        if entry:
            span, t0 = entry
            span.set_status(StatusCode.ERROR, str(error))
            span.record_exception(error)
            span.set_attribute("latency_ms", round((time.perf_counter() - t0) * 1000, 2))
            span.end()

    # ------------------------------------------------------------------
    # Tool events
    # ------------------------------------------------------------------

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        name = serialized.get("name", "unknown")
        self._start_span(f"tool.{name}", run_id, parent_run_id)
        entry = self._spans.get(str(run_id))
        if entry:
            entry[0].set_attribute("tool.input_len", len(input_str))

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        output_str = str(output) if output is not None else ""
        span_name = self._end_span(run_id, {"tool.output_len": len(output_str)})

        # Write audit entry
        from eln.audit.singleton import get_audit_logger
        _al = get_audit_logger()
        if _al:
            tool_name = (span_name or "tool.unknown").removeprefix("tool.")
            _al.log_tool_call(
                tool_name=tool_name,
                args={},
                result_summary=output_str[:200],
            )

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        key = str(run_id)
        entry = self._spans.pop(key, None)
        self._names.pop(key, None)
        if entry:
            span, t0 = entry
            span.set_status(StatusCode.ERROR, str(error))
            span.record_exception(error)
            span.set_attribute("latency_ms", round((time.perf_counter() - t0) * 1000, 2))
            span.end()

        from eln.audit.singleton import get_audit_logger
        _al = get_audit_logger()
        if _al:
            _al.log_error(
                error_type=type(error).__name__,
                message=str(error),
                context={"run_id": str(run_id)},
            )

    # ------------------------------------------------------------------
    # LLM events
    # ------------------------------------------------------------------

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._start_span("llm.call", run_id, parent_run_id)
        entry = self._spans.get(str(run_id))
        if entry:
            model = serialized.get("kwargs", {}).get("model") or serialized.get("name", "")
            entry[0].set_attribute("llm.model", model)
            entry[0].set_attribute("llm.prompt_count", len(prompts))

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        # Extract token counts from LLMResult
        input_tokens = output_tokens = 0
        model = ""
        if response.llm_output:
            usage = response.llm_output.get("token_usage") or response.llm_output.get("usage", {})
            input_tokens = usage.get("prompt_tokens") or usage.get("input_tokens", 0)
            output_tokens = usage.get("completion_tokens") or usage.get("output_tokens", 0)
            model = response.llm_output.get("model_name") or response.llm_output.get("model", "")

        # Also check first generation's generation_info (Anthropic streaming)
        if not input_tokens and response.generations:
            gen_info = getattr(response.generations[0][0], "generation_info", None) or {}
            usage = gen_info.get("usage") or {}
            input_tokens = usage.get("input_tokens", input_tokens)
            output_tokens = usage.get("output_tokens", output_tokens)

        span = self._end_span(run_id, {
            "llm.input_tokens": input_tokens,
            "llm.output_tokens": output_tokens,
            "llm.model": model,
        })

        # Write audit entry
        from eln.audit.singleton import get_audit_logger
        _al = get_audit_logger()
        if _al:
            prompt_text = ""
            if response.generations and response.generations[0]:
                prompt_text = getattr(response.generations[0][0], "text", "") or ""
            _al.log_llm_call(
                provider="langchain",
                model=model,
                prompt=prompt_text[:500],
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        key = str(run_id)
        entry = self._spans.pop(key, None)
        self._names.pop(key, None)
        if entry:
            span, t0 = entry
            span.set_status(StatusCode.ERROR, str(error))
            span.record_exception(error)
            span.set_attribute("latency_ms", round((time.perf_counter() - t0) * 1000, 2))
            span.end()

        from eln.audit.singleton import get_audit_logger
        _al = get_audit_logger()
        if _al:
            _al.log_error(
                error_type=type(error).__name__,
                message=str(error),
                context={"run_id": str(run_id)},
            )
