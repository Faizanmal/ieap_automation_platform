"""
Plugin System Module

Extensible plugin architecture for third-party integrations.
"""

from .base import (
    Plugin,
    PluginContext,
    PluginHook,
    PluginInfo,
    PluginState,
    plugin_hook,
)
from .hooks import Hook, HookManager, hook
from .loader import PluginLoader
from .manager import PluginManager
from .registry import PluginRegistry

__all__ = [
    "Hook",
    "HookManager",
    "Plugin",
    "PluginContext",
    "PluginHook",
    "PluginInfo",
    "PluginLoader",
    "PluginManager",
    "PluginRegistry",
    "PluginState",
    "hook",
    "plugin_hook"
]
