"""
API Middleware Stack

Custom middleware for:
- Request ID tracking
- Logging
- Security headers
- Rate limiting
- Performance monitoring
"""

import logging
import time
import uuid
from collections import defaultdict
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to each request for tracing.
    """

    HEADER_NAME = "X-Request-ID"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate request ID
        request_id = request.headers.get(self.HEADER_NAME) or str(uuid.uuid4())

        # Store in request state for access in handlers
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers[self.HEADER_NAME] = request_id

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests with timing and status information.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # Request info
        request_id = getattr(request.state, "request_id", "unknown")
        method = request.method
        path = request.url.path
        client_ip = self._get_client_ip(request)

        # Log request
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "client_ip": client_ip
            }
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log response
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_ip
            }
        )

        # Add timing header
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers (when behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    """

    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        for header, value in self.SECURITY_HEADERS.items():
            response.headers[header] = value

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_limit: int = 100
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.window_size = 60  # 1 minute window

        # In-memory storage (use Redis in production)
        self._requests: dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/v1/health", "/metrics"]:
            return await call_next(request)

        # Get client identifier
        client_id = self._get_client_id(request)

        # Check rate limit
        current_time = time.time()
        window_start = current_time - self.window_size

        # Clean old requests
        self._requests[client_id] = [
            req_time for req_time in self._requests[client_id]
            if req_time > window_start
        ]

        # Check limits
        request_count = len(self._requests[client_id])

        if request_count >= self.burst_limit:
            return self._rate_limit_response(request_count, 0)

        if request_count >= self.requests_per_minute:
            # Calculate retry after
            oldest_request = min(self._requests[client_id])
            retry_after = int(oldest_request + self.window_size - current_time) + 1
            return self._rate_limit_response(request_count, retry_after)

        # Record request
        self._requests[client_id].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = self.requests_per_minute - len(self._requests[client_id])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_size))

        return response

    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key[:16]}"

        # Check for authenticated user
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token_prefix = auth_header[7:23]
            return f"token:{token_prefix}"

        # Fall back to IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"

        return f"ip:{request.client.host if request.client else 'unknown'}"

    def _rate_limit_response(self, current: int, retry_after: int) -> Response:
        """Create rate limit exceeded response"""
        from starlette.responses import JSONResponse

        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please slow down.",
                    "details": {
                        "limit": self.requests_per_minute,
                        "current": current,
                        "retry_after": retry_after
                    }
                }
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(self.requests_per_minute),
                "X-RateLimit-Remaining": "0"
            }
        )


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Performance monitoring middleware.
    """

    # Threshold for slow requests (ms)
    SLOW_REQUEST_THRESHOLD = 1000

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # Track request size
        content_length = request.headers.get("content-length", 0)

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log slow requests
        if duration_ms > self.SLOW_REQUEST_THRESHOLD:
            logger.warning(
                "Slow request detected",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "duration_ms": round(duration_ms, 2),
                    "threshold_ms": self.SLOW_REQUEST_THRESHOLD
                }
            )

        # Add performance headers
        response.headers["X-Request-Duration"] = f"{duration_ms:.2f}ms"
        response.headers["Server-Timing"] = f"total;dur={duration_ms:.2f}"

        return response
