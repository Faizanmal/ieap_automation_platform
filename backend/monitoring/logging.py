"""
Structured Logging

Enterprise logging with JSON format, context, and correlation.
"""

import json
import logging
import sys
import traceback
from contextvars import ContextVar
from datetime import datetime
from typing import Any

# Context variable for request-scoped data
log_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default={})


class LogContext:
    """
    Context manager for adding request-scoped logging context.
    
    Usage:
        with LogContext(request_id="abc", user_id="123"):
            logger.info("Processing request")
    """

    def __init__(self, **kwargs):
        self.new_context = kwargs
        self.old_context = None

    def __enter__(self):
        self.old_context = log_context.get().copy()
        current = log_context.get().copy()
        current.update(self.new_context)
        log_context.set(current)
        return self

    def __exit__(self, *args):
        log_context.set(self.old_context)


def add_context(**kwargs):
    """Add items to the current log context."""
    current = log_context.get().copy()
    current.update(kwargs)
    log_context.set(current)


def get_context() -> dict[str, Any]:
    """Get current log context."""
    return log_context.get().copy()


def clear_context():
    """Clear log context."""
    log_context.set({})


class StructuredFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.
    """

    def __init__(
        self,
        include_timestamp: bool = True,
        include_logger: bool = True,
        include_level: bool = True,
        include_location: bool = True,
        extra_fields: dict[str, Any] | None = None
    ):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_logger = include_logger
        self.include_level = include_level
        self.include_location = include_location
        self.extra_fields = extra_fields or {}

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "message": record.getMessage()
        }

        # Add timestamp
        if self.include_timestamp:
            log_data["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Add level
        if self.include_level:
            log_data["level"] = record.levelname
            log_data["level_num"] = record.levelno

        # Add logger name
        if self.include_logger:
            log_data["logger"] = record.name

        # Add location
        if self.include_location:
            log_data["location"] = {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName
            }

        # Add context
        ctx = log_context.get()
        if ctx:
            log_data["context"] = ctx

        # Add exception info
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields from record
        extra_keys = set(record.__dict__.keys()) - {
            "name", "msg", "args", "created", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs",
            "pathname", "process", "processName", "relativeCreated",
            "stack_info", "exc_info", "exc_text", "thread", "threadName",
            "message", "asctime", "taskName"
        }

        for key in extra_keys:
            value = getattr(record, key)
            if value is not None:
                log_data[key] = value

        # Add static extra fields
        log_data.update(self.extra_fields)

        return json.dumps(log_data, default=str)


class StructuredLogger:
    """
    Wrapper for structured logging with additional methods.
    """

    def __init__(self, name: str):
        self._logger = logging.getLogger(name)

    def _log(
        self,
        level: int,
        message: str,
        exc_info: Any = None,
        **kwargs
    ):
        extra = kwargs.copy()
        self._logger.log(level, message, exc_info=exc_info, extra=extra)

    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, exc_info: Any = None, **kwargs):
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)

    def critical(self, message: str, exc_info: Any = None, **kwargs):
        self._log(logging.CRITICAL, message, exc_info=exc_info, **kwargs)

    def exception(self, message: str, **kwargs):
        self._log(logging.ERROR, message, exc_info=True, **kwargs)

    # Domain-specific logging methods
    def request(
        self,
        method: str,
        path: str,
        status: int,
        duration_ms: float,
        **kwargs
    ):
        """Log HTTP request."""
        self.info(
            f"{method} {path} - {status}",
            http_method=method,
            http_path=path,
            http_status=status,
            duration_ms=duration_ms,
            event_type="http_request",
            **kwargs
        )

    def prediction(
        self,
        model_id: str,
        latency_ms: float,
        success: bool = True,
        **kwargs
    ):
        """Log ML prediction."""
        self.info(
            f"Prediction {'completed' if success else 'failed'}: {model_id}",
            model_id=model_id,
            latency_ms=latency_ms,
            success=success,
            event_type="prediction",
            **kwargs
        )

    def decision(
        self,
        decision_id: str,
        domain: str,
        confidence: float,
        **kwargs
    ):
        """Log autonomous decision."""
        self.info(
            f"Decision made: {decision_id} ({domain})",
            decision_id=decision_id,
            domain=domain,
            confidence=confidence,
            event_type="decision",
            **kwargs
        )

    def security_event(
        self,
        event_type: str,
        user_id: str | None = None,
        success: bool = True,
        **kwargs
    ):
        """Log security event."""
        level = logging.INFO if success else logging.WARNING
        self._log(
            level,
            f"Security event: {event_type}",
            event_type="security",
            security_event=event_type,
            user_id=user_id,
            success=success,
            **kwargs
        )


def setup_logging(
    level: str | int = "INFO",
    json_format: bool = True,
    log_file: str | None = None,
    service_name: str = "ieap"
):
    """
    Configure application logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON structured format
        log_file: Optional log file path
        service_name: Service name for logs
    """
    # Convert string level to int
    if isinstance(level, str):
        level = getattr(logging, level.upper())

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers = []

    # Create formatter
    if json_format:
        formatter = StructuredFormatter(
            extra_fields={"service": service_name}
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger."""
    return StructuredLogger(name)
