"""
Rate Limit Middleware

FastAPI middleware for rate limiting.
"""

import logging
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .limiter import RateLimiter, RateLimitTier

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for FastAPI.
    
    Usage:
        limiter = RateLimiter(redis_client=redis)
        app.add_middleware(
            RateLimitMiddleware,
            limiter=limiter,
            key_func=lambda r: r.client.host,
            tier_func=lambda r: get_user_tier(r)
        )
    """

    def __init__(
        self,
        app,
        limiter: RateLimiter,
        key_func: Callable[[Request], str] | None = None,
        tier_func: Callable[[Request], RateLimitTier] | None = None,
        cost_func: Callable[[Request], float] | None = None,
        exclude_paths: list | None = None,
        include_headers: bool = True,
        on_blocked: Callable[[Request], Response] | None = None
    ):
        super().__init__(app)
        self.limiter = limiter
        self.key_func = key_func or self._default_key_func
        self.tier_func = tier_func
        self.cost_func = cost_func or (lambda _: 1.0)
        self.exclude_paths = set(exclude_paths or ["/health", "/metrics", "/docs", "/redoc"])
        self.include_headers = include_headers
        self.on_blocked = on_blocked

    def _default_key_func(self, request: Request) -> str:
        """Default key extraction (IP address)"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Skip preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        try:
            # Extract key and tier
            key = self.key_func(request)
            tier = self.tier_func(request) if self.tier_func else None
            cost = self.cost_func(request)

            # Check rate limit
            result = await self.limiter.check(
                key=key,
                tier=tier,
                cost=cost,
                endpoint=request.url.path
            )

            if not result.allowed:
                logger.warning(
                    f"Rate limit exceeded for {key} on {request.url.path}: {result.reason}"
                )

                if self.on_blocked:
                    response = self.on_blocked(request)
                else:
                    response = JSONResponse(
                        status_code=429,
                        content={
                            "error": "Too Many Requests",
                            "message": result.reason or "Rate limit exceeded",
                            "retry_after": result.retry_after,
                            "limit": result.limit,
                            "remaining": result.remaining
                        }
                    )

                if self.include_headers:
                    for name, value in result.to_headers().items():
                        response.headers[name] = value

                return response

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            if self.include_headers:
                for name, value in result.to_headers().items():
                    response.headers[name] = value

            return response

        except Exception as e:
            logger.error(f"Rate limit middleware error: {e}")
            # Don't block on rate limiter errors
            return await call_next(request)
