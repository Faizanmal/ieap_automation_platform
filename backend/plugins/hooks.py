"""
Hook Manager

Plugin hook system for extension points.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Hook:
    """Hook definition"""
    name: str
    description: str = ""
    params: list[str] = field(default_factory=list)
    returns: str = "None"


@dataclass
class HookHandler:
    """Registered hook handler"""
    callback: Callable
    priority: int = 0
    plugin_name: str | None = None


class HookManager:
    """
    Manages hook registration and execution.
    
    Hooks allow plugins to extend core functionality
    at defined extension points.
    
    Usage:
        hooks = HookManager()
        
        # Register a hook
        hooks.register("before_prediction", my_handler, priority=10)
        
        # Execute hook
        results = await hooks.execute("before_prediction", model=model, data=data)
    """

    # Pre-defined hooks
    DEFINED_HOOKS = {
        "app_startup": Hook(
            name="app_startup",
            description="Called when the application starts"
        ),
        "app_shutdown": Hook(
            name="app_shutdown",
            description="Called when the application shuts down"
        ),
        "before_request": Hook(
            name="before_request",
            description="Called before each request",
            params=["request"]
        ),
        "after_request": Hook(
            name="after_request",
            description="Called after each request",
            params=["request", "response"]
        ),
        "before_prediction": Hook(
            name="before_prediction",
            description="Called before ML prediction",
            params=["model", "data"]
        ),
        "after_prediction": Hook(
            name="after_prediction",
            description="Called after ML prediction",
            params=["model", "data", "prediction"]
        ),
        "before_decision": Hook(
            name="before_decision",
            description="Called before autonomous decision",
            params=["context"]
        ),
        "after_decision": Hook(
            name="after_decision",
            description="Called after autonomous decision",
            params=["context", "decision"]
        ),
        "user_created": Hook(
            name="user_created",
            description="Called when a user is created",
            params=["user"]
        ),
        "model_deployed": Hook(
            name="model_deployed",
            description="Called when a model is deployed",
            params=["model"]
        ),
        "error_occurred": Hook(
            name="error_occurred",
            description="Called when an error occurs",
            params=["error", "context"]
        )
    }

    def __init__(self):
        self._handlers: dict[str, list[HookHandler]] = {}

    def register(
        self,
        hook_name: str,
        callback: Callable,
        priority: int = 0,
        plugin_name: str | None = None
    ):
        """
        Register a hook handler.
        
        Args:
            hook_name: Name of the hook
            callback: Handler function (async or sync)
            priority: Execution priority (higher = earlier)
            plugin_name: Name of the registering plugin
        """
        if hook_name not in self._handlers:
            self._handlers[hook_name] = []

        handler = HookHandler(
            callback=callback,
            priority=priority,
            plugin_name=plugin_name
        )

        self._handlers[hook_name].append(handler)
        self._handlers[hook_name].sort(key=lambda h: -h.priority)

        logger.debug(
            f"Registered hook handler for '{hook_name}' "
            f"(priority={priority}, plugin={plugin_name})"
        )

    def unregister(self, hook_name: str, callback: Callable):
        """Unregister a specific hook handler"""
        if hook_name in self._handlers:
            self._handlers[hook_name] = [
                h for h in self._handlers[hook_name]
                if h.callback != callback
            ]

    def unregister_plugin(self, plugin_name: str):
        """Unregister all handlers from a plugin"""
        for hook_name in self._handlers:
            self._handlers[hook_name] = [
                h for h in self._handlers[hook_name]
                if h.plugin_name != plugin_name
            ]

    async def execute(
        self,
        hook_name: str,
        *args,
        stop_on_error: bool = False,
        **kwargs
    ) -> list[Any]:
        """
        Execute all handlers for a hook.
        
        Args:
            hook_name: Name of the hook
            *args: Positional arguments to pass to handlers
            stop_on_error: Stop execution if a handler raises
            **kwargs: Keyword arguments to pass to handlers
        
        Returns:
            List of results from all handlers
        """
        handlers = self._handlers.get(hook_name, [])

        if not handlers:
            return []

        results = []

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler.callback):
                    result = await handler.callback(*args, **kwargs)
                else:
                    result = handler.callback(*args, **kwargs)

                results.append(result)

            except Exception as e:
                logger.error(
                    f"Hook handler error in '{hook_name}' "
                    f"(plugin={handler.plugin_name}): {e}"
                )

                if stop_on_error:
                    raise

                results.append(None)

        return results

    async def execute_filter(
        self,
        hook_name: str,
        value: Any,
        **kwargs
    ) -> Any:
        """
        Execute handlers as a filter chain.
        
        Each handler receives the return value of the previous one.
        
        Args:
            hook_name: Name of the hook
            value: Initial value to filter
            **kwargs: Additional context
        
        Returns:
            Final filtered value
        """
        handlers = self._handlers.get(hook_name, [])

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler.callback):
                    value = await handler.callback(value, **kwargs)
                else:
                    value = handler.callback(value, **kwargs)
            except Exception as e:
                logger.error(f"Filter hook error in '{hook_name}': {e}")

        return value

    def has_handlers(self, hook_name: str) -> bool:
        """Check if a hook has any handlers"""
        return hook_name in self._handlers and len(self._handlers[hook_name]) > 0

    def list_hooks(self) -> list[str]:
        """List all hooks with registered handlers"""
        return list(self._handlers.keys())

    def count(self) -> int:
        """Count total registered handlers"""
        return sum(len(handlers) for handlers in self._handlers.values())

    def get_defined_hooks(self) -> dict[str, Hook]:
        """Get all pre-defined hooks"""
        return self.DEFINED_HOOKS.copy()


# Decorator for hook handlers
def hook(hook_name: str, priority: int = 0):
    """
    Decorator to mark a function as a hook handler.
    
    Usage:
        @hook("before_prediction", priority=10)
        async def my_handler(model, data):
            # Modify data before prediction
            return modified_data
    """
    def decorator(func: Callable) -> Callable:
        func._hook_name = hook_name
        func._hook_priority = priority
        return func
    return decorator
