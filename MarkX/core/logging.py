# core/logging.py - Structured logging with structlog

import structlog
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    json_logs: bool = False,
    enable_console: bool = True
):
    """
    Setup structured logging with structlog.
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (None = no file logging)
        json_logs: Use JSON format for logs
        enable_console: Enable console logging
    """
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Processors for structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Add JSON or console renderer
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=enable_console,
                exception_formatter=structlog.dev.plain_traceback
            )
        )
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup file logging if log_dir provided
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create file handler
        log_file = log_dir / f"dmitry_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        # JSON format for file logs
        file_formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(file_formatter)
        
        # Add to root logger
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Get a structured logger.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


# Convenience logger
logger = get_logger(__name__)


# Example usage functions
def log_request(
    request_id: str,
    endpoint: str,
    method: str = "POST",
    **kwargs
):
    """Log an incoming request."""
    logger.info(
        "request_received",
        request_id=request_id,
        endpoint=endpoint,
        method=method,
        **kwargs
    )


def log_response(
    request_id: str,
    status_code: int,
    duration_ms: float,
    **kwargs
):
    """Log a response."""
    logger.info(
        "response_sent",
        request_id=request_id,
        status_code=status_code,
        duration_ms=duration_ms,
        **kwargs
    )


def log_platform_call(
    request_id: str,
    endpoint: str,
    call_id: str,
    status: str,
    duration_ms: float,
    **kwargs
):
    """Log a Platform API call."""
    logger.info(
        "platform_call",
        request_id=request_id,
        endpoint=endpoint,
        call_id=call_id,
        status=status,
        duration_ms=duration_ms,
        **kwargs
    )


def log_action_proposed(
    request_id: str,
    action_type: str,
    target: str,
    confidence: float,
    approval_required: bool,
    **kwargs
):
    """Log an action proposal."""
    logger.info(
        "action_proposed",
        request_id=request_id,
        action_type=action_type,
        target=target,
        confidence=confidence,
        approval_required=approval_required,
        **kwargs
    )


def log_error(
    error_type: str,
    error_message: str,
    request_id: str = None,
    **kwargs
):
    """Log an error."""
    logger.error(
        "error_occurred",
        error_type=error_type,
        error_message=error_message,
        request_id=request_id,
        **kwargs
    )


def log_security_event(
    event_type: str,
    severity: str,
    description: str,
    **kwargs
):
    """Log a security event."""
    logger.warning(
        "security_event",
        event_type=event_type,
        severity=severity,
        description=description,
        **kwargs
    )


# Context managers for logging
class LogContext:
    """Context manager for adding context to logs."""
    
    def __init__(self, **kwargs):
        self.context = kwargs
        self.token = None
    
    def __enter__(self):
        self.token = structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        structlog.contextvars.unbind_contextvars(*self.context.keys())


def with_context(**kwargs):
    """
    Decorator to add context to all logs in a function.
    
    Usage:
        @with_context(request_id="req-123")
        def process_request():
            logger.info("processing")  # Will include request_id
    """
    def decorator(func):
        def wrapper(*args, **func_kwargs):
            with LogContext(**kwargs):
                return func(*args, **func_kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test logging
    from pathlib import Path
    
    setup_logging(
        log_level="DEBUG",
        log_dir=Path("logs"),
        json_logs=False,
        enable_console=True
    )
    
    logger = get_logger(__name__)
    
    # Test different log types
    logger.debug("Debug message", key="value")
    logger.info("Info message", user="john", action="login")
    logger.warning("Warning message", threshold=0.8, current=0.9)
    logger.error("Error message", error_code="E001")
    
    # Test convenience functions
    log_request("req-123", "/advise", method="POST", tenant_id="tenant-1")
    log_response("req-123", 200, 245.5)
    log_platform_call("req-123", "get_risk_findings", "call-456", "success", 123.4)
    log_action_proposed("req-123", "isolate_entity", "customer-db", 0.87, True)
    
    # Test context
    with LogContext(request_id="req-789", tenant_id="tenant-1"):
        logger.info("Inside context")  # Will include request_id and tenant_id
    
    logger.info("Outside context")  # Won't include request_id
    
    print("\nLogging test complete!")
