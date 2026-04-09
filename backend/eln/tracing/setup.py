"""
OpenTelemetry tracing setup.

Configures a global TracerProvider based on environment settings.
If tracing is disabled, uses NoOpTracerProvider for zero overhead.
"""

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import NoOpTracerProvider


def init_tracing(
    service_name: str = "eln-plus-plus",
    endpoint: str | None = None,
    enabled: bool = False,
    exporter: str = "otlp",
) -> None:
    """
    Configure the global TracerProvider.

    Args:
        service_name: OTel service name attribute.
        endpoint: OTLP collector endpoint (e.g. http://localhost:4317).
        enabled: If False, installs a NoOpTracerProvider (zero overhead).
        exporter: "otlp" for OTLPSpanExporter, "console" for ConsoleSpanExporter.
    """
    if not enabled:
        trace.set_tracer_provider(NoOpTracerProvider())
        return

    resource = Resource.create({
        "service.name": service_name,
        "service.version": "0.1.0",
    })

    provider = TracerProvider(resource=resource)

    if exporter == "console":
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )

        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    else:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        otlp_endpoint = endpoint or "http://localhost:4317"
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
        )

    trace.set_tracer_provider(provider)


def get_tracer(name: str) -> trace.Tracer:
    """Return a named Tracer from the global provider."""
    return trace.get_tracer(name)
