"""
OpenTelemetry Tracing

Distributed tracing for request flow tracking.
"""

import functools
import logging
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import SpanKind, Status, StatusCode

logger = logging.getLogger(__name__)


class TracingManager:
    """
    OpenTelemetry tracing manager.
    """

    def __init__(
        self,
        service_name: str = "ieap",
        service_version: str = "1.0.0",
        otlp_endpoint: str | None = None,
        console_export: bool = False
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.otlp_endpoint = otlp_endpoint
        self.console_export = console_export

        self._tracer_provider: TracerProvider | None = None
        self._tracer: trace.Tracer | None = None
        self._initialized = False

    def initialize(self):
        """Initialize OpenTelemetry tracing."""
        if self._initialized:
            return

        logger.info("Initializing OpenTelemetry tracing...")

        # Create resource
        resource = Resource.create({
            SERVICE_NAME: self.service_name,
            SERVICE_VERSION: self.service_version,
            "deployment.environment": "production"
        })

        # Create tracer provider
        self._tracer_provider = TracerProvider(resource=resource)

        # Add exporters
        if self.otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.otlp_endpoint,
                insecure=True
            )
            self._tracer_provider.add_span_processor(
                BatchSpanProcessor(otlp_exporter)
            )
            logger.info(f"OTLP exporter configured: {self.otlp_endpoint}")

        if self.console_export:
            console_exporter = ConsoleSpanExporter()
            self._tracer_provider.add_span_processor(
                BatchSpanProcessor(console_exporter)
            )

        # Set as global tracer provider
        trace.set_tracer_provider(self._tracer_provider)

        # Set propagator for distributed tracing
        set_global_textmap(B3MultiFormat())

        # Get tracer
        self._tracer = trace.get_tracer(
            self.service_name,
            self.service_version
        )

        # Instrument common libraries
        self._instrument_libraries()

        self._initialized = True
        logger.info("OpenTelemetry tracing initialized")

    def _instrument_libraries(self):
        """Instrument common libraries for automatic tracing."""
        try:
            RequestsInstrumentor().instrument()
            logger.debug("Instrumented: requests")
        except Exception as e:
            logger.debug(f"Could not instrument requests: {e}")

        try:
            RedisInstrumentor().instrument()
            logger.debug("Instrumented: redis")
        except Exception as e:
            logger.debug(f"Could not instrument redis: {e}")

    def instrument_sqlalchemy(self, engine):
        """Instrument SQLAlchemy engine."""
        try:
            SQLAlchemyInstrumentor().instrument(engine=engine)
            logger.debug("Instrumented: sqlalchemy")
        except Exception as e:
            logger.debug(f"Could not instrument sqlalchemy: {e}")

    def shutdown(self):
        """Shutdown tracing."""
        if self._tracer_provider:
            self._tracer_provider.shutdown()
            logger.info("OpenTelemetry tracing shutdown")

    @property
    def tracer(self) -> trace.Tracer:
        """Get the tracer instance."""
        if not self._tracer:
            self._tracer = trace.get_tracer(self.service_name)
        return self._tracer

    @contextmanager
    def span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: dict[str, Any] | None = None
    ):
        """
        Context manager for creating spans.
        
        Usage:
            with tracing.span("operation_name") as span:
                span.set_attribute("key", "value")
                # do work
        """
        with self.tracer.start_as_current_span(
            name,
            kind=kind,
            attributes=attributes or {}
        ) as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


# Global tracing manager
_tracing: TracingManager | None = None


def get_tracer() -> trace.Tracer:
    """Get the global tracer."""
    global _tracing
    if _tracing is None:
        _tracing = TracingManager()
    return _tracing.tracer


def init_tracing(
    service_name: str = "ieap",
    otlp_endpoint: str | None = None
) -> TracingManager:
    """Initialize global tracing."""
    global _tracing
    _tracing = TracingManager(
        service_name=service_name,
        otlp_endpoint=otlp_endpoint
    )
    _tracing.initialize()
    return _tracing


@contextmanager
def span(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None
):
    """
    Context manager for creating spans.
    
    Usage:
        with span("my_operation") as s:
            s.set_attribute("key", "value")
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(
        name,
        kind=kind,
        attributes=attributes or {}
    ) as s:
        try:
            yield s
        except Exception as e:
            s.set_status(Status(StatusCode.ERROR, str(e)))
            s.record_exception(e)
            raise


def trace_async(
    name: str | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None
):
    """
    Decorator for tracing async functions.
    
    Usage:
        @trace_async("my_operation")
        async def my_function():
            pass
    """
    def decorator(func: Callable):
        span_name = name or f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with span(span_name, kind=kind, attributes=attributes):
                return await func(*args, **kwargs)

        return wrapper
    return decorator


def trace_sync(
    name: str | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None
):
    """
    Decorator for tracing sync functions.
    
    Usage:
        @trace_sync("my_operation")
        def my_function():
            pass
    """
    def decorator(func: Callable):
        span_name = name or f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with span(span_name, kind=kind, attributes=attributes):
                return func(*args, **kwargs)

        return wrapper
    return decorator


def add_span_attributes(attributes: dict[str, Any]):
    """Add attributes to the current span."""
    current_span = trace.get_current_span()
    if current_span:
        for key, value in attributes.items():
            current_span.set_attribute(key, value)


def record_exception(exception: Exception, attributes: dict[str, Any] | None = None):
    """Record an exception in the current span."""
    current_span = trace.get_current_span()
    if current_span:
        current_span.record_exception(exception, attributes=attributes)
        current_span.set_status(Status(StatusCode.ERROR, str(exception)))
