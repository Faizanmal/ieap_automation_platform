"""
SDK Exceptions

Custom exceptions for the IEAP SDK.
"""

from typing import Any


class IEAPError(Exception):
    """Base exception for IEAP SDK"""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        status_code: int | None = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code


class AuthenticationError(IEAPError):
    """Authentication failed"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, error_code="AUTH_FAILED", status_code=401)


class AuthorizationError(IEAPError):
    """Authorization denied"""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message, error_code="ACCESS_DENIED", status_code=403)


class NotFoundError(IEAPError):
    """Resource not found"""

    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            f"{resource} with id '{resource_id}' not found",
            error_code="NOT_FOUND",
            details={"resource": resource, "resource_id": resource_id},
            status_code=404
        )


class ValidationError(IEAPError):
    """Validation failed"""

    def __init__(self, message: str, errors: dict[str, Any]):
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            details={"errors": errors},
            status_code=422
        )


class RateLimitError(IEAPError):
    """Rate limit exceeded"""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            "Rate limit exceeded",
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
            status_code=429
        )
        self.retry_after = retry_after


class ServerError(IEAPError):
    """Server error"""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, error_code="SERVER_ERROR", status_code=500)


class TimeoutError(IEAPError):
    """Request timeout"""

    def __init__(self, message: str = "Request timed out"):
        super().__init__(message, error_code="TIMEOUT", status_code=504)


class ConnectionError(IEAPError):
    """Connection error"""

    def __init__(self, message: str = "Failed to connect to server"):
        super().__init__(message, error_code="CONNECTION_ERROR")
