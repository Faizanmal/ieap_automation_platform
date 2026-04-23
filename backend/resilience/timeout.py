"""
Timeout Pattern

Enforces time limits on operations.
"""

import asyncio
import builtins
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from functools import wraps

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Exception raised when operation times out"""

    def __init__(self, operation_name: str, timeout_seconds: float):
        self.operation_name = operation_name
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Operation '{operation_name}' timed out after {timeout_seconds}s")


@dataclass
class TimeoutPolicy:
    """Timeout policy configuration"""
    timeout_seconds: float = 30.0
    cancel_on_timeout: bool = True
    on_timeout: Callable | None = None


def timeout(
    seconds: float = 30.0,
    cancel_on_timeout: bool = True,
    on_timeout: Callable | None = None,
    policy: TimeoutPolicy | None = None
) -> Callable:
    """
    Decorator to add timeout to a function.
    
    Usage:
        @timeout(seconds=5.0)
        async def slow_operation():
            await asyncio.sleep(10)  # Will timeout
        
        @timeout(seconds=10.0)
        def sync_operation():
            time.sleep(20)  # Will timeout
    """

    if policy is None:
        policy = TimeoutPolicy(
            timeout_seconds=seconds,
            cancel_on_timeout=cancel_on_timeout,
            on_timeout=on_timeout
        )

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=policy.timeout_seconds
                    )
                except builtins.TimeoutError:
                    if policy.on_timeout:
                        try:
                            policy.on_timeout(func.__name__, policy.timeout_seconds)
                        except Exception:
                            pass
                    raise TimeoutError(func.__name__, policy.timeout_seconds)

            return async_wrapper
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Use thread pool for sync timeout
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=policy.timeout_seconds)
                except FuturesTimeoutError:
                    if policy.on_timeout:
                        try:
                            policy.on_timeout(func.__name__, policy.timeout_seconds)
                        except Exception:
                            pass
                    if policy.cancel_on_timeout:
                        future.cancel()
                    raise TimeoutError(func.__name__, policy.timeout_seconds)

        return sync_wrapper

    return decorator


class TimeoutContext:
    """
    Context manager for timeout.
    
    Usage:
        async with TimeoutContext(seconds=5.0):
            await slow_operation()
    """

    def __init__(
        self,
        seconds: float = 30.0,
        operation_name: str = "operation"
    ):
        self.seconds = seconds
        self.operation_name = operation_name

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, asyncio.TimeoutError):
            raise TimeoutError(self.operation_name, self.seconds)
        return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


async def with_timeout(
    coro,
    seconds: float,
    operation_name: str = "operation"
):
    """
    Run a coroutine with timeout.
    
    Usage:
        result = await with_timeout(slow_operation(), seconds=5.0)
    """
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except builtins.TimeoutError:
        raise TimeoutError(operation_name, seconds)
