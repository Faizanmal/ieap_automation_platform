"""
Plugin Base Classes

Base classes and interfaces for plugins.
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PluginState(Enum):
    """Plugin lifecycle states"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ERROR = "error"
    UNLOADING = "unloading"


@dataclass
class PluginInfo:
    """Plugin metadata"""
    name: str
    version: str
    description: str = ""
    author: str = ""
    author_email: str = ""
    homepage: str = ""
    license: str = ""
    dependencies: list[str] = field(default_factory=list)
    python_requires: str = ">=3.11"
    tags: list[str] = field(default_factory=list)
    entry_point: str = ""
    config_schema: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "author_email": self.author_email,
            "homepage": self.homepage,
            "license": self.license,
            "dependencies": self.dependencies,
            "python_requires": self.python_requires,
            "tags": self.tags
        }


class Plugin(ABC):
    """
    Abstract base class for all plugins.
    
    Plugins must implement:
    - get_info(): Return plugin metadata
    - on_load(): Called when plugin is loaded
    - on_unload(): Called when plugin is unloaded
    
    Plugins can optionally implement:
    - on_activate(): Called when plugin is activated
    - on_deactivate(): Called when plugin is deactivated
    - on_config_change(): Called when configuration changes
    - get_routes(): Return FastAPI routes to register
    - get_cli_commands(): Return CLI commands to register
    
    Example:
        class MyPlugin(Plugin):
            @property
            def info(self) -> PluginInfo:
                return PluginInfo(
                    name="my-plugin",
                    version="1.0.0",
                    description="My custom plugin"
                )
            
            async def on_load(self, context: PluginContext) -> None:
                self.db = context.get_service("database")
            
            async def on_unload(self) -> None:
                pass
    """

    def __init__(self):
        self._state = PluginState.UNLOADED
        self._config: dict[str, Any] = {}
        self._context: PluginContext | None = None
        self._loaded_at: datetime | None = None
        self._error: str | None = None

    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """Return plugin metadata"""

    @property
    def state(self) -> PluginState:
        """Current plugin state"""
        return self._state

    @property
    def config(self) -> dict[str, Any]:
        """Plugin configuration"""
        return self._config

    @property
    def name(self) -> str:
        """Plugin name shortcut"""
        return self.info.name

    @property
    def version(self) -> str:
        """Plugin version shortcut"""
        return self.info.version

    # Lifecycle methods
    @abstractmethod
    async def on_load(self, context: "PluginContext") -> None:
        """
        Called when the plugin is loaded.
        
        Use this to initialize resources, register hooks, etc.
        """

    @abstractmethod
    async def on_unload(self) -> None:
        """
        Called when the plugin is unloaded.
        
        Use this to cleanup resources, unregister hooks, etc.
        """

    async def on_activate(self) -> None:
        """Called when the plugin is activated"""

    async def on_deactivate(self) -> None:
        """Called when the plugin is deactivated"""

    async def on_config_change(self, config: dict[str, Any]) -> None:
        """Called when configuration changes"""
        self._config = config

    # Extension points
    def get_routes(self) -> list[Any] | None:
        """
        Return FastAPI routes to register.
        
        Returns list of APIRouter instances.
        """
        return None

    def get_cli_commands(self) -> list[Any] | None:
        """
        Return CLI commands to register.
        
        Returns list of click commands/groups.
        """
        return None

    def get_middleware(self) -> list[Any] | None:
        """
        Return middleware to register.
        
        Returns list of Starlette middleware.
        """
        return None

    def get_event_handlers(self) -> dict[str, Callable] | None:
        """
        Return event handlers to register.
        
        Returns dict of event_name -> handler function.
        """
        return None

    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate plugin configuration"""
        schema = self.info.config_schema
        if not schema:
            return True

        # Basic schema validation
        for key, spec in schema.items():
            if spec.get("required") and key not in config:
                return False

        return True

    def get_status(self) -> dict[str, Any]:
        """Get plugin status"""
        return {
            "name": self.name,
            "version": self.version,
            "state": self._state.value,
            "loaded_at": self._loaded_at.isoformat() if self._loaded_at else None,
            "error": self._error,
            "config": {k: "***" if "secret" in k.lower() else v for k, v in self._config.items()}
        }


@dataclass
class PluginContext:
    """
    Context provided to plugins during loading.
    
    Provides access to core services and utilities.
    """
    app: Any  # FastAPI app
    config: dict[str, Any]  # Global configuration
    services: dict[str, Any] = field(default_factory=dict)

    def get_service(self, name: str) -> Any | None:
        """Get a registered service"""
        return self.services.get(name)

    def register_service(self, name: str, service: Any):
        """Register a service for other plugins"""
        self.services[name] = service

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)


class PluginHook:
    """
    Decorator for marking methods as hook handlers.
    
    Usage:
        class MyPlugin(Plugin):
            @PluginHook("before_request")
            async def handle_request(self, request):
                # Handle the hook
                pass
    """

    def __init__(self, hook_name: str, priority: int = 0):
        self.hook_name = hook_name
        self.priority = priority

    def __call__(self, func: Callable) -> Callable:
        func._plugin_hook = self.hook_name
        func._plugin_hook_priority = self.priority
        return func


# Convenience decorator
def plugin_hook(hook_name: str, priority: int = 0):
    """Decorator to mark a method as a hook handler"""
    return PluginHook(hook_name, priority)
