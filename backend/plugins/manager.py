"""
Plugin Manager

Central manager for plugin lifecycle and operations.
"""

import logging
from datetime import datetime
from typing import Any

from .base import Plugin, PluginContext, PluginInfo, PluginState
from .hooks import HookManager
from .loader import PluginLoader
from .registry import PluginRegistry

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Central plugin management system.
    
    Features:
    - Plugin discovery and loading
    - Lifecycle management
    - Dependency resolution
    - Configuration management
    - Hook management
    - Hot reload support
    
    Usage:
        manager = PluginManager(app)
        
        # Discover and load plugins
        await manager.discover_plugins("./plugins")
        await manager.load_all()
        
        # Or load specific plugin
        await manager.load_plugin("my-plugin")
        
        # Check plugin status
        status = manager.get_status()
        
        # Unload plugin
        await manager.unload_plugin("my-plugin")
    """

    def __init__(
        self,
        app: Any = None,
        config: dict[str, Any] | None = None,
        plugins_dir: str = "./plugins"
    ):
        self.app = app
        self.global_config = config or {}
        self.plugins_dir = plugins_dir

        self.registry = PluginRegistry()
        self.loader = PluginLoader(plugins_dir)
        self.hooks = HookManager()

        self._context: PluginContext | None = None
        self._initialized = False

    async def initialize(self, services: dict[str, Any] | None = None):
        """Initialize the plugin manager"""
        if self._initialized:
            return

        self._context = PluginContext(
            app=self.app,
            config=self.global_config,
            services=services or {}
        )

        self._initialized = True
        logger.info("Plugin manager initialized")

    async def discover_plugins(
        self,
        path: str | None = None,
        recursive: bool = True
    ) -> list[PluginInfo]:
        """
        Discover available plugins in a directory.
        
        Returns list of discovered plugin metadata.
        """
        search_path = path or self.plugins_dir
        discovered = await self.loader.discover(search_path, recursive)

        for info in discovered:
            self.registry.register_available(info)

        logger.info(f"Discovered {len(discovered)} plugins")
        return discovered

    async def load_plugin(
        self,
        name: str,
        config: dict[str, Any] | None = None
    ) -> bool:
        """
        Load a specific plugin.
        
        Args:
            name: Plugin name
            config: Plugin-specific configuration
        
        Returns:
            True if plugin loaded successfully
        """
        if not self._initialized:
            await self.initialize()

        # Check if already loaded
        if self.registry.is_loaded(name):
            logger.warning(f"Plugin {name} already loaded")
            return True

        try:
            # Load plugin class
            plugin_class = await self.loader.load(name)
            if not plugin_class:
                logger.error(f"Could not load plugin class for {name}")
                return False

            # Instantiate plugin
            plugin = plugin_class()
            plugin._state = PluginState.LOADING

            # Validate config
            plugin_config = config or self.global_config.get(f"plugins.{name}", {})
            if not plugin.validate_config(plugin_config):
                logger.error(f"Invalid configuration for plugin {name}")
                plugin._state = PluginState.ERROR
                plugin._error = "Invalid configuration"
                return False

            plugin._config = plugin_config

            # Check dependencies
            for dep in plugin.info.dependencies:
                if not self.registry.is_loaded(dep):
                    logger.info(f"Loading dependency {dep} for {name}")
                    if not await self.load_plugin(dep):
                        logger.error(f"Failed to load dependency {dep}")
                        plugin._state = PluginState.ERROR
                        plugin._error = f"Dependency failed: {dep}"
                        return False

            # Load the plugin
            await plugin.on_load(self._context)

            plugin._state = PluginState.LOADED
            plugin._loaded_at = datetime.now()
            plugin._context = self._context

            # Register plugin
            self.registry.register(name, plugin)

            # Register hooks
            self._register_plugin_hooks(plugin)

            # Register routes if any
            routes = plugin.get_routes()
            if routes and self.app:
                for router in routes:
                    self.app.include_router(router, prefix=f"/plugins/{name}")

            logger.info(f"Loaded plugin: {name} v{plugin.version}")
            return True

        except Exception as e:
            logger.error(f"Failed to load plugin {name}: {e}")
            return False

    async def unload_plugin(self, name: str) -> bool:
        """
        Unload a specific plugin.
        
        Args:
            name: Plugin name
        
        Returns:
            True if plugin unloaded successfully
        """
        plugin = self.registry.get(name)
        if not plugin:
            logger.warning(f"Plugin {name} not loaded")
            return False

        try:
            plugin._state = PluginState.UNLOADING

            # Check if other plugins depend on this
            dependents = self._get_dependents(name)
            if dependents:
                logger.warning(
                    f"Unloading {name} will affect: {', '.join(dependents)}"
                )

            # Unload the plugin
            await plugin.on_unload()

            # Unregister hooks
            self._unregister_plugin_hooks(plugin)

            plugin._state = PluginState.UNLOADED

            # Remove from registry
            self.registry.unregister(name)

            logger.info(f"Unloaded plugin: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload plugin {name}: {e}")
            plugin._state = PluginState.ERROR
            plugin._error = str(e)
            return False

    async def reload_plugin(self, name: str) -> bool:
        """Reload a plugin (unload + load)"""
        config = None
        plugin = self.registry.get(name)
        if plugin:
            config = plugin.config

        if not await self.unload_plugin(name):
            return False

        return await self.load_plugin(name, config)

    async def load_all(self) -> dict[str, bool]:
        """Load all discovered plugins"""
        results = {}

        for info in self.registry.list_available():
            results[info.name] = await self.load_plugin(info.name)

        return results

    async def unload_all(self) -> dict[str, bool]:
        """Unload all loaded plugins"""
        results = {}

        # Unload in reverse dependency order
        loaded = list(self.registry.list_loaded())
        for plugin in reversed(loaded):
            results[plugin.name] = await self.unload_plugin(plugin.name)

        return results

    async def activate_plugin(self, name: str) -> bool:
        """Activate a loaded plugin"""
        plugin = self.registry.get(name)
        if not plugin:
            return False

        if plugin.state != PluginState.LOADED:
            return False

        try:
            await plugin.on_activate()
            plugin._state = PluginState.ACTIVE
            return True
        except Exception as e:
            logger.error(f"Failed to activate plugin {name}: {e}")
            return False

    async def deactivate_plugin(self, name: str) -> bool:
        """Deactivate an active plugin"""
        plugin = self.registry.get(name)
        if not plugin:
            return False

        if plugin.state != PluginState.ACTIVE:
            return False

        try:
            await plugin.on_deactivate()
            plugin._state = PluginState.SUSPENDED
            return True
        except Exception as e:
            logger.error(f"Failed to deactivate plugin {name}: {e}")
            return False

    async def update_config(
        self,
        name: str,
        config: dict[str, Any]
    ) -> bool:
        """Update plugin configuration"""
        plugin = self.registry.get(name)
        if not plugin:
            return False

        if not plugin.validate_config(config):
            return False

        try:
            await plugin.on_config_change(config)
            return True
        except Exception as e:
            logger.error(f"Failed to update config for {name}: {e}")
            return False

    def get_plugin(self, name: str) -> Plugin | None:
        """Get a loaded plugin by name"""
        return self.registry.get(name)

    def list_plugins(self) -> list[dict[str, Any]]:
        """List all plugins with status"""
        result = []

        # Available but not loaded
        for info in self.registry.list_available():
            if not self.registry.is_loaded(info.name):
                result.append({
                    **info.to_dict(),
                    "state": PluginState.UNLOADED.value,
                    "loaded": False
                })

        # Loaded plugins
        for plugin in self.registry.list_loaded():
            result.append({
                **plugin.info.to_dict(),
                "state": plugin.state.value,
                "loaded": True,
                "loaded_at": plugin._loaded_at.isoformat() if plugin._loaded_at else None,
                "error": plugin._error
            })

        return result

    def get_status(self) -> dict[str, Any]:
        """Get plugin manager status"""
        loaded = list(self.registry.list_loaded())

        return {
            "initialized": self._initialized,
            "plugins_dir": self.plugins_dir,
            "available_count": len(self.registry.list_available()),
            "loaded_count": len(loaded),
            "active_count": sum(1 for p in loaded if p.state == PluginState.ACTIVE),
            "error_count": sum(1 for p in loaded if p.state == PluginState.ERROR),
            "hooks_registered": self.hooks.count()
        }

    def _register_plugin_hooks(self, plugin: Plugin):
        """Register all hooks from a plugin"""
        for name in dir(plugin):
            method = getattr(plugin, name)
            if hasattr(method, "_plugin_hook"):
                hook_name = method._plugin_hook
                priority = getattr(method, "_plugin_hook_priority", 0)
                self.hooks.register(hook_name, method, priority)

    def _unregister_plugin_hooks(self, plugin: Plugin):
        """Unregister all hooks from a plugin"""
        for name in dir(plugin):
            method = getattr(plugin, name)
            if hasattr(method, "_plugin_hook"):
                hook_name = method._plugin_hook
                self.hooks.unregister(hook_name, method)

    def _get_dependents(self, name: str) -> list[str]:
        """Get plugins that depend on the given plugin"""
        dependents = []

        for plugin in self.registry.list_loaded():
            if name in plugin.info.dependencies:
                dependents.append(plugin.name)

        return dependents

    async def execute_hook(
        self,
        hook_name: str,
        *args,
        **kwargs
    ) -> list[Any]:
        """Execute all handlers for a hook"""
        return await self.hooks.execute(hook_name, *args, **kwargs)
