"""
Retry Pattern

Automatic retry with configurable backoff strategies.
"""

import asyncio
import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)


class BackoffStrategy(Enum):
    """Backoff strategies"""
    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    DECORRELATED_JITTER = "decorrelated_jitter"


@dataclass
class RetryPolicy:
    """Retry policy configuration"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    backoff_multiplier: float = 2.0
    jitter: bool = True
    jitter_range: float = 0.1  # ±10% jitter
    retryable_exceptions: tuple = (Exception,)
    non_retryable_exceptions: tuple = ()
    on_retry: Callable | None = None

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        if self.backoff_strategy == BackoffStrategy.FIXED:
            delay = self.initial_delay
        elif self.backoff_strategy == BackoffStrategy.LINEAR:
            delay = self.initial_delay * attempt
        elif self.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.initial_delay * (self.backoff_multiplier ** (attempt - 1))
        elif self.backoff_strategy == BackoffStrategy.DECORRELATED_JITTER:
            # AWS-style decorrelated jitter
            delay = min(self.max_delay, random.uniform(self.initial_delay, self.initial_delay * 3))
        else:
            delay = self.initial_delay

        # Apply jitter
        if self.jitter and self.backoff_strategy != BackoffStrategy.DECORRELATED_JITTER:
            jitter = delay * self.jitter_range
            delay = delay + random.uniform(-jitter, jitter)

        return min(delay, self.max_delay)


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL,
    retryable_exceptions: tuple = (Exception,),
    non_retryable_exceptions: tuple = (),
    on_retry: Callable | None = None,
    policy: RetryPolicy | None = None
) -> Callable:
    """
    Decorator for automatic retry with backoff.
    
    Usage:
        @retry(max_attempts=3, initial_delay=1.0)
        async def flaky_operation():
            # Operation that might fail
            pass
        
        # Or with a policy
        @retry(policy=RetryPolicy(max_attempts=5, backoff_strategy=BackoffStrategy.LINEAR))
        def another_operation():
            pass
    """

    if policy is None:
        policy = RetryPolicy(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            max_delay=max_delay,
            backoff_strategy=backoff_strategy,
            retryable_exceptions=retryable_exceptions,
            non_retryable_exceptions=non_retryable_exceptions,
            on_retry=on_retry
        )

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None

                for attempt in range(1, policy.max_attempts + 1):
                    try:
                        return await func(*args, **kwargs)
                    except policy.non_retryable_exceptions:
                        # Don't retry these
                        raise
                    except policy.retryable_exceptions as e:
                        last_exception = e

                        if attempt == policy.max_attempts:
                            logger.warning(
                                f"Function {func.__name__} failed after {attempt} attempts: {e}"
                            )
                            raise

                        delay = policy.calculate_delay(attempt)

                        logger.info(
                            f"Function {func.__name__} failed (attempt {attempt}/{policy.max_attempts}), "
                            f"retrying in {delay:.2f}s: {e}"
                        )

                        if policy.on_retry:
                            try:
                                policy.on_retry(attempt, e, delay)
                            except Exception:
                                pass

                        await asyncio.sleep(delay)

                raise last_exception

            return async_wrapper
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, policy.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except policy.non_retryable_exceptions:
                    raise
                except policy.retryable_exceptions as e:
                    last_exception = e

                    if attempt == policy.max_attempts:
                        logger.warning(
                            f"Function {func.__name__} failed after {attempt} attempts: {e}"
                        )
                        raise

                    delay = policy.calculate_delay(attempt)

                    logger.info(
                        f"Function {func.__name__} failed (attempt {attempt}/{policy.max_attempts}), "
                        f"retrying in {delay:.2f}s: {e}"
                    )

                    if policy.on_retry:
                        try:
                            policy.on_retry(attempt, e, delay)
                        except Exception:
                            pass

                    time.sleep(delay)

            raise last_exception

        return sync_wrapper

    return decorator


class RetryContext:
    """
    Context manager for retry logic.
    
    Usage:
        async with RetryContext(max_attempts=3) as ctx:
            while ctx.should_retry():
                try:
                    result = await some_operation()
                    ctx.success()
                    break
                except Exception as e:
                    await ctx.failed(e)
    """

    def __init__(self, policy: RetryPolicy | None = None, **kwargs):
        self.policy = policy or RetryPolicy(**kwargs)
        self.attempt = 0
        self.last_exception = None
        self._succeeded = False

    def should_retry(self) -> bool:
        """Check if we should retry"""
        return self.attempt < self.policy.max_attempts and not self._succeeded

    def success(self):
        """Mark operation as successful"""
        self._succeeded = True

    async def failed(self, exception: Exception):
        """Record failure and wait before retry"""
        self.last_exception = exception
        self.attempt += 1

        if self.attempt < self.policy.max_attempts:
            delay = self.policy.calculate_delay(self.attempt)
            await asyncio.sleep(delay)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
