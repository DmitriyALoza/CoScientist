"""OpenTelemetry tracing for ELN++."""

from eln.tracing.decorators import traced
from eln.tracing.setup import get_tracer, init_tracing

__all__ = ["init_tracing", "get_tracer", "traced"]
