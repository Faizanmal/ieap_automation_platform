"""
Plugin Registry

Registry for tracking available and loaded plugins.
"""

import logging
from collections.abc import Iterator

from .base import Plugin, PluginInfo

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Registry for managing plugin state.
    
    Tracks:
    - Available plugins (discovered)
    - Loaded plugins (instances)
    - Plugin metadata
    """

    def __init__(self):
        self._available: dict[str, PluginInfo] = {}
        self._loaded: dict[str, Plugin] = {}

    def register_available(self, info: PluginInfo):
        """Register a plugin as available"""
        self._available[info.name] = info
        logger.debug(f"Registered available plugin: {info.name}")

    def register(self, name: str, plugin: Plugin):
        """Register a loaded plugin"""
        self._loaded[name] = plugin
        logger.debug(f"Registered loaded plugin: {name}")

    def unregister(self, name: str):
        """Unregister a plugin"""
        self._loaded.pop(name, None)
        logger.debug(f"Unregistered plugin: {name}")

    def get(self, name: str) -> Plugin | None:
        """Get a loaded plugin by name"""
        return self._loaded.get(name)

    def get_info(self, name: str) -> PluginInfo | None:
        """Get plugin info by name"""
        if name in self._loaded:
            return self._loaded[name].info
        return self._available.get(name)

    def is_available(self, name: str) -> bool:
        """Check if a plugin is available"""
        return name in self._available

    def is_loaded(self, name: str) -> bool:
        """Check if a plugin is loaded"""
        return name in self._loaded

    def list_available(self) -> list[PluginInfo]:
        """List all available plugins"""
        return list(self._available.values())

    def list_loaded(self) -> Iterator[Plugin]:
        """List all loaded plugins"""
        return iter(self._loaded.values())

    def count_available(self) -> int:
        """Count available plugins"""
        return len(self._available)

    def count_loaded(self) -> int:
        """Count loaded plugins"""
        return len(self._loaded)

    def clear(self):
        """Clear all registrations"""
        self._available.clear()
        self._loaded.clear()
