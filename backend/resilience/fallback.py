"""
Fallback Pattern

Provides fallback behavior when operations fail.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FallbackPolicy:
    """Fallback policy configuration"""
    fallback_value: Any = None
    fallback_function: Callable | None = None
    exceptions: tuple = (Exception,)
    log_failures: bool = True


def fallback(
    value: Any = None,
    function: Callable | None = None,
    exceptions: tuple = (Exception,),
    log_failures: bool = True,
    policy: FallbackPolicy | None = None
) -> Callable:
    """
    Decorator to add fallback behavior.
    
    Usage:
        @fallback(value=[])
        async def get_items():
            # Returns [] if this fails
            return await fetch_items()
        
        @fallback(function=get_cached_value)
        def get_data():
            # Calls get_cached_value if this fails
            return fetch_data()
    """

    if policy is None:
        policy = FallbackPolicy(
            fallback_value=value,
            fallback_function=function,
            exceptions=exceptions,
            log_failures=log_failures
        )

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except policy.exceptions as e:
                    if policy.log_failures:
                        logger.warning(
                            f"Function {func.__name__} failed, using fallback: {e}"
                        )

                    if policy.fallback_function:
                        if asyncio.iscoroutinefunction(policy.fallback_function):
                            return await policy.fallback_function(*args, **kwargs)
                        return policy.fallback_function(*args, **kwargs)

                    return policy.fallback_value

            return async_wrapper
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except policy.exceptions as e:
                if policy.log_failures:
                    logger.warning(
                        f"Function {func.__name__} failed, using fallback: {e}"
                    )

                if policy.fallback_function:
                    return policy.fallback_function(*args, **kwargs)

                return policy.fallback_value

        return sync_wrapper

    return decorator


class FallbackChain:
    """
    Chain multiple fallback options.
    
    Usage:
        chain = FallbackChain()
        chain.add(primary_source)
        chain.add(secondary_source)
        chain.add_value(default_value)
        
        result = await chain.execute()
    """

    def __init__(self):
        self._chain: list = []

    def add(self, func: Callable) -> "FallbackChain":
        """Add a function to the chain"""
        self._chain.append(("func", func))
        return self

    def add_value(self, value: Any) -> "FallbackChain":
        """Add a fallback value"""
        self._chain.append(("value", value))
        return self

    async def execute(self, *args, **kwargs) -> Any:
        """Execute the fallback chain"""
        last_error = None

        for item_type, item in self._chain:
            try:
                if item_type == "value":
                    return item
                if item_type == "func":
                    if asyncio.iscoroutinefunction(item):
                        return await item(*args, **kwargs)
                    return item(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.debug(f"Fallback chain item failed: {e}")
                continue

        if last_error:
            raise last_error
        return None

    def execute_sync(self, *args, **kwargs) -> Any:
        """Execute the fallback chain synchronously"""
        last_error = None

        for item_type, item in self._chain:
            try:
                if item_type == "value":
                    return item
                if item_type == "func":
                    return item(*args, **kwargs)
            except Exception as e:
                last_error = e
                continue

        if last_error:
            raise last_error
        return None
