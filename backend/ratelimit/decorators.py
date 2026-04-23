"""
Rate Limit Decorators

Decorator-based rate limiting for functions and endpoints.
"""

import asyncio
import functools
import logging
from collections.abc import Callable

from .limiter import RateLimitConfig, RateLimiter
from .strategies import SlidingWindow, TokenBucket

logger = logging.getLogger(__name__)


def rate_limit(
    limit: int,
    window: int = 60,
    key: str | Callable | None = None,
    strategy: str = "sliding",
    on_exceed: Callable | None = None
):
    """
    Rate limit decorator for functions.
    
    Usage:
        @rate_limit(limit=100, window=60)
        async def my_function():
            ...
        
        @rate_limit(limit=10, window=1, key=lambda user_id: f"user:{user_id}")
        async def per_user_function(user_id: str):
            ...
    """
    def decorator(func: Callable):
        if strategy == "sliding":
            limiter = SlidingWindow(limit=limit, window_size=window)
        else:
            limiter = TokenBucket(rate=limit/window, capacity=limit)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Determine key
            if key is None:
                limit_key = func.__name__
            elif callable(key):
                limit_key = key(*args, **kwargs)
            else:
                limit_key = key

            result = await limiter.is_allowed(limit_key)

            if not result.allowed:
                if on_exceed:
                    return on_exceed(result)
                raise RateLimitExceeded(
                    f"Rate limit exceeded. Retry after {result.retry_after:.1f}s",
                    retry_after=result.retry_after
                )

            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.get_event_loop().run_until_complete(
                async_wrapper(*args, **kwargs)
            )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def quota_limit(
    daily: int | None = None,
    monthly: int | None = None,
    cost: float = 1.0,
    key_func: Callable | None = None,
    redis_client = None
):
    """
    Quota-based rate limiting decorator.
    
    Usage:
        @quota_limit(daily=1000, monthly=10000)
        async def expensive_operation():
            ...
        
        @quota_limit(daily=100, cost=10)  # Each call costs 10 quota units
        async def very_expensive_operation():
            ...
    """
    def decorator(func: Callable):
        config = RateLimitConfig(
            daily_quota=daily,
            monthly_quota=monthly,
            cost_per_request=cost
        )
        limiter = RateLimiter(redis_client=redis_client, default_config=config)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if key_func:
                limit_key = key_func(*args, **kwargs)
            else:
                limit_key = func.__name__

            result = await limiter.check(limit_key, cost=cost)

            if not result.allowed:
                raise QuotaExceeded(
                    f"Quota exceeded. {result.quota_remaining or 0} remaining",
                    quota_remaining=result.quota_remaining,
                    reset_at=result.reset_at
                )

            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.get_event_loop().run_until_complete(
                async_wrapper(*args, **kwargs)
            )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class RateLimitExceeded(Exception):
    """Rate limit exceeded exception"""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class QuotaExceeded(Exception):
    """Quota exceeded exception"""

    def __init__(
        self,
        message: str,
        quota_remaining: int | None = None,
        reset_at = None
    ):
        super().__init__(message)
        self.quota_remaining = quota_remaining
        self.reset_at = reset_at


# Convenience decorators for common patterns
def per_second(limit: int, **kwargs):
    """Rate limit per second"""
    return rate_limit(limit=limit, window=1, **kwargs)


def per_minute(limit: int, **kwargs):
    """Rate limit per minute"""
    return rate_limit(limit=limit, window=60, **kwargs)


def per_hour(limit: int, **kwargs):
    """Rate limit per hour"""
    return rate_limit(limit=limit, window=3600, **kwargs)


def per_day(limit: int, **kwargs):
    """Rate limit per day"""
    return rate_limit(limit=limit, window=86400, **kwargs)
