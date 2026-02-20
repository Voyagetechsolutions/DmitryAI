# core/tracing.py - OpenTelemetry distributed tracing

from typing import Optional, Dict, Any
from contextlib import contextmanager
import time

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None


class TracingManager:
    """Manages OpenTelemetry tracing."""
    
    def __init__(
        self,
        service_name: str = "dmitry",
        service_version: str = "1.2.0",
        otlp_endpoint: Optional[str] = None,
        enable_console: bool = False
    ):
        """
        Initialize tracing manager.
        
        Args:
            service_name: Name of the service
            service_version: Version of the service
            otlp_endpoint: OTLP collector endpoint (e.g., "http://localhost:4318")
            enable_console: Enable console exporter for debugging
        """
        self.service_name = service_name
        self.service_version = service_version
        self.enabled = OTEL_AVAILABLE
        self.tracer = None
        
        if not OTEL_AVAILABLE:
            print("⚠️  OpenTelemetry not available. Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp")
            return
        
        # Create resource
        resource = Resource.create({
            "service.name": service_name,
            "service.version": service_version,
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Add exporters
        if otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        if enable_console:
            console_exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(console_exporter))
        
        # Set as global tracer provider
        trace.set_tracer_provider(provider)
        
        # Get tracer
        self.tracer = trace.get_tracer(__name__)
    
    @contextmanager
    def span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: str = "internal"
    ):
        """
        Create a span context manager.
        
        Args:
            name: Span name
            attributes: Span attributes
            kind: Span kind (internal, server, client, producer, consumer)
        
        Usage:
            with tracing.span("process_request", {"request_id": "req-123"}):
                # Do work
                pass
        """
        if not self.enabled or not self.tracer:
            yield None
            return
        
        # Map kind string to SpanKind
        kind_map = {
            "internal": trace.SpanKind.INTERNAL,
            "server": trace.SpanKind.SERVER,
            "client": trace.SpanKind.CLIENT,
            "producer": trace.SpanKind.PRODUCER,
            "consumer": trace.SpanKind.CONSUMER,
        }
        span_kind = kind_map.get(kind, trace.SpanKind.INTERNAL)
        
        with self.tracer.start_as_current_span(name, kind=span_kind) as span:
            # Add attributes
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            
            try:
                yield span
            except Exception as e:
                # Record exception
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def trace_function(self, name: Optional[str] = None, attributes: Optional[Dict] = None):
        """
        Decorator to trace a function.
        
        Usage:
            @tracing.trace_function("my_function", {"key": "value"})
            def my_function():
                pass
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                span_name = name or func.__name__
                span_attrs = attributes or {}
                
                with self.span(span_name, span_attrs):
                    return func(*args, **kwargs)
            
            return wrapper
        return decorator


# Global tracing manager
_tracing_manager: Optional[TracingManager] = None


def setup_tracing(
    service_name: str = "dmitry",
    service_version: str = "1.2.0",
    otlp_endpoint: Optional[str] = None,
    enable_console: bool = False
) -> TracingManager:
    """
    Setup distributed tracing.
    
    Args:
        service_name: Name of the service
        service_version: Version of the service
        otlp_endpoint: OTLP collector endpoint
        enable_console: Enable console exporter
    
    Returns:
        TracingManager instance
    """
    global _tracing_manager
    _tracing_manager = TracingManager(
        service_name=service_name,
        service_version=service_version,
        otlp_endpoint=otlp_endpoint,
        enable_console=enable_console
    )
    return _tracing_manager


def get_tracing() -> TracingManager:
    """Get tracing manager (singleton)."""
    global _tracing_manager
    if _tracing_manager is None:
        _tracing_manager = TracingManager()
    return _tracing_manager


# Convenience functions
def trace_request(request_id: str, endpoint: str, method: str = "POST"):
    """
    Trace an HTTP request.
    
    Usage:
        with trace_request("req-123", "/advise", "POST") as span:
            # Process request
            pass
    """
    tracing = get_tracing()
    return tracing.span(
        f"{method} {endpoint}",
        attributes={
            "request_id": request_id,
            "http.method": method,
            "http.route": endpoint,
        },
        kind="server"
    )


def trace_platform_call(request_id: str, endpoint: str, call_id: str):
    """
    Trace a Platform API call.
    
    Usage:
        with trace_platform_call("req-123", "get_risk_findings", "call-456") as span:
            # Make Platform call
            pass
    """
    tracing = get_tracing()
    return tracing.span(
        f"platform.{endpoint}",
        attributes={
            "request_id": request_id,
            "platform.endpoint": endpoint,
            "platform.call_id": call_id,
        },
        kind="client"
    )


def trace_llm_call(request_id: str, model: str, prompt_tokens: int = 0):
    """
    Trace an LLM API call.
    
    Usage:
        with trace_llm_call("req-123", "gpt-4", 150) as span:
            # Make LLM call
            if span:
                span.set_attribute("llm.completion_tokens", 200)
    """
    tracing = get_tracing()
    return tracing.span(
        "llm.generate",
        attributes={
            "request_id": request_id,
            "llm.model": model,
            "llm.prompt_tokens": prompt_tokens,
        },
        kind="client"
    )


def trace_action_proposal(request_id: str, action_type: str, target: str):
    """
    Trace an action proposal.
    
    Usage:
        with trace_action_proposal("req-123", "isolate_entity", "customer-db") as span:
            # Propose action
            if span:
                span.set_attribute("action.confidence", 0.87)
    """
    tracing = get_tracing()
    return tracing.span(
        "action.propose",
        attributes={
            "request_id": request_id,
            "action.type": action_type,
            "action.target": target,
        },
        kind="internal"
    )


if __name__ == "__main__":
    # Test tracing
    tracing = setup_tracing(
        service_name="dmitry-test",
        service_version="1.2.0",
        enable_console=True
    )
    
    if tracing.enabled:
        print("✓ Tracing enabled")
        
        # Test span
        with tracing.span("test_operation", {"test_key": "test_value"}):
            print("  Inside span")
            time.sleep(0.1)
        
        # Test nested spans
        with trace_request("req-test", "/advise", "POST") as span:
            print("  Request span")
            
            with trace_platform_call("req-test", "get_risk_findings", "call-test"):
                print("    Platform call span")
                time.sleep(0.05)
            
            with trace_llm_call("req-test", "gpt-4", 150) as llm_span:
                print("    LLM call span")
                if llm_span:
                    llm_span.set_attribute("llm.completion_tokens", 200)
                time.sleep(0.05)
        
        print("\n✓ Tracing test complete")
    else:
        print("⚠️  Tracing not available")
