"""
Tracing decorator for wrapping sync and async functions in OTel spans.
"""

import asyncio
import functools
from collections.abc import Callable
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import StatusCode


def traced(
    name: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> Callable:
    """
    Decorator that wraps a sync or async function in an OTel span.

    Args:
        name: Span name. Defaults to the function's qualified name.
        attributes: Static attributes to set on every span.
    """
    static_attrs = attributes or {}

    def decorator(fn: Callable) -> Callable:
        span_name = name or fn.__qualname__
        tracer = trace.get_tracer(fn.__module__)

        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(span_name) as span:
                    _set_attributes(span, static_attrs)
                    _set_attributes(span, {
                        k: str(v) for k, v in kwargs.items()
                        if isinstance(v, (str, int, float, bool))
                    })
                    try:
                        result = await fn(*args, **kwargs)
                        return result
                    except Exception as exc:
                        span.set_status(StatusCode.ERROR, str(exc))
                        span.record_exception(exc)
                        raise

            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(span_name) as span:
                    _set_attributes(span, static_attrs)
                    _set_attributes(span, {
                        k: str(v) for k, v in kwargs.items()
                        if isinstance(v, (str, int, float, bool))
                    })
                    try:
                        result = fn(*args, **kwargs)
                        return result
                    except Exception as exc:
                        span.set_status(StatusCode.ERROR, str(exc))
                        span.record_exception(exc)
                        raise

            return sync_wrapper

    return decorator


def _set_attributes(span: trace.Span, attrs: dict[str, Any]) -> None:
    """Safely set span attributes, skipping non-primitive values."""
    for k, v in attrs.items():
        if isinstance(v, (str, int, float, bool)):
            span.set_attribute(k, v)
