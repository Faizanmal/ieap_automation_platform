"""
Plugin Loader

Load plugins from various sources.
"""

import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any

from .base import Plugin, PluginInfo

logger = logging.getLogger(__name__)


class PluginLoader:
    """
    Loads plugins from various sources.
    
    Supports:
    - Python packages
    - Single Python files
    - Plugin manifest files (plugin.yaml)
    - Entry points (for installed packages)
    """

    def __init__(self, plugins_dir: str = "./plugins"):
        self.plugins_dir = Path(plugins_dir)
        self._loaded_modules: dict[str, Any] = {}

    async def discover(
        self,
        path: str | None = None,
        recursive: bool = True
    ) -> list[PluginInfo]:
        """
        Discover available plugins.
        
        Returns list of PluginInfo for discovered plugins.
        """
        search_path = Path(path) if path else self.plugins_dir
        discovered = []

        if not search_path.exists():
            logger.warning(f"Plugin directory does not exist: {search_path}")
            return discovered

        # Search for plugin packages
        for item in search_path.iterdir():
            if item.is_dir():
                # Check for plugin package
                init_file = item / "__init__.py"
                manifest_file = item / "plugin.yaml"

                if init_file.exists():
                    info = await self._discover_package(item)
                    if info:
                        discovered.append(info)

                elif manifest_file.exists():
                    info = await self._discover_from_manifest(manifest_file)
                    if info:
                        discovered.append(info)

                elif recursive:
                    # Recursive search
                    sub_discovered = await self.discover(str(item), recursive=True)
                    discovered.extend(sub_discovered)

            elif item.suffix == ".py" and not item.name.startswith("_"):
                # Single file plugin
                info = await self._discover_file(item)
                if info:
                    discovered.append(info)

        # Also discover from entry points
        entry_point_plugins = await self._discover_entry_points()
        discovered.extend(entry_point_plugins)

        return discovered

    async def _discover_package(self, path: Path) -> PluginInfo | None:
        """Discover plugin from a package directory"""
        try:
            # Try to load the module to get plugin info
            spec = importlib.util.spec_from_file_location(
                path.name,
                path / "__init__.py"
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)

                # Look for plugin class or info
                if hasattr(module, "PLUGIN_INFO"):
                    return module.PLUGIN_INFO

                if hasattr(module, "Plugin"):
                    plugin_class = module.Plugin
                    if hasattr(plugin_class, "info"):
                        instance = plugin_class()
                        return instance.info

                # Basic info from package name
                return PluginInfo(
                    name=path.name,
                    version="0.0.0",
                    description=f"Plugin from {path}",
                    entry_point=str(path / "__init__.py")
                )

        except Exception as e:
            logger.warning(f"Could not discover package {path}: {e}")

        return None

    async def _discover_file(self, path: Path) -> PluginInfo | None:
        """Discover plugin from a single file"""
        try:
            return PluginInfo(
                name=path.stem,
                version="0.0.0",
                description=f"Plugin from {path.name}",
                entry_point=str(path)
            )
        except Exception as e:
            logger.warning(f"Could not discover file {path}: {e}")

        return None

    async def _discover_from_manifest(self, manifest_path: Path) -> PluginInfo | None:
        """Discover plugin from manifest file"""
        try:
            import yaml

            with open(manifest_path) as f:
                data = yaml.safe_load(f)

            return PluginInfo(
                name=data.get("name", manifest_path.parent.name),
                version=data.get("version", "0.0.0"),
                description=data.get("description", ""),
                author=data.get("author", ""),
                author_email=data.get("author_email", ""),
                homepage=data.get("homepage", ""),
                license=data.get("license", ""),
                dependencies=data.get("dependencies", []),
                tags=data.get("tags", []),
                entry_point=data.get("entry_point", str(manifest_path.parent / "__init__.py")),
                config_schema=data.get("config_schema")
            )

        except ImportError:
            logger.warning("PyYAML not installed, cannot read manifest files")
        except Exception as e:
            logger.warning(f"Could not read manifest {manifest_path}: {e}")

        return None

    async def _discover_entry_points(self) -> list[PluginInfo]:
        """Discover plugins from installed packages using entry points"""
        discovered = []

        try:
            if sys.version_info >= (3, 10):
                from importlib.metadata import entry_points
                eps = entry_points(group="ieap.plugins")
            else:
                from importlib.metadata import entry_points
                all_eps = entry_points()
                eps = all_eps.get("ieap.plugins", [])

            for ep in eps:
                try:
                    discovered.append(PluginInfo(
                        name=ep.name,
                        version="0.0.0",
                        description=f"Entry point plugin: {ep.name}",
                        entry_point=f"{ep.value}"
                    ))
                except Exception as e:
                    logger.warning(f"Could not load entry point {ep.name}: {e}")

        except Exception as e:
            logger.debug(f"Could not discover entry points: {e}")

        return discovered

    async def load(self, name: str) -> type[Plugin] | None:
        """
        Load a plugin class by name.
        
        Returns the Plugin subclass.
        """
        # Check if already loaded
        if name in self._loaded_modules:
            return self._find_plugin_class(self._loaded_modules[name])

        # Try different loading strategies
        plugin_class = None

        # 1. Try as installed package
        plugin_class = await self._load_from_package(name)
        if plugin_class:
            return plugin_class

        # 2. Try from plugins directory
        plugin_class = await self._load_from_directory(name)
        if plugin_class:
            return plugin_class

        # 3. Try as entry point
        plugin_class = await self._load_from_entry_point(name)
        if plugin_class:
            return plugin_class

        logger.error(f"Could not load plugin: {name}")
        return None

    async def _load_from_package(self, name: str) -> type[Plugin] | None:
        """Load plugin from an installed package"""
        try:
            module = importlib.import_module(f"ieap_plugins.{name}")
            self._loaded_modules[name] = module
            return self._find_plugin_class(module)
        except ImportError:
            pass

        try:
            module = importlib.import_module(name)
            self._loaded_modules[name] = module
            return self._find_plugin_class(module)
        except ImportError:
            pass

        return None

    async def _load_from_directory(self, name: str) -> type[Plugin] | None:
        """Load plugin from plugins directory"""
        plugin_path = self.plugins_dir / name

        # Try as package
        if (plugin_path / "__init__.py").exists():
            return await self._load_module_from_path(
                name,
                plugin_path / "__init__.py"
            )

        # Try as single file
        plugin_file = self.plugins_dir / f"{name}.py"
        if plugin_file.exists():
            return await self._load_module_from_path(name, plugin_file)

        return None

    async def _load_from_entry_point(self, name: str) -> type[Plugin] | None:
        """Load plugin from entry point"""
        try:
            if sys.version_info >= (3, 10):
                from importlib.metadata import entry_points
                eps = entry_points(group="ieap.plugins")
            else:
                from importlib.metadata import entry_points
                all_eps = entry_points()
                eps = all_eps.get("ieap.plugins", [])

            for ep in eps:
                if ep.name == name:
                    plugin_class = ep.load()
                    if issubclass(plugin_class, Plugin):
                        return plugin_class

        except Exception as e:
            logger.debug(f"Could not load from entry point: {e}")

        return None

    async def _load_module_from_path(
        self,
        name: str,
        path: Path
    ) -> type[Plugin] | None:
        """Load a module from a file path"""
        try:
            # Load as part of plugins package to support relative imports
            module_name = f"plugins.{name}"
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                self._loaded_modules[name] = module
                return self._find_plugin_class(module)
        except Exception as e:
            logger.error(f"Failed to load module from {path}: {e}")

        return None

    def _find_plugin_class(self, module: Any) -> type[Plugin] | None:
        """Find Plugin subclass in a module"""
        # Look for explicit plugin class
        if hasattr(module, "Plugin") and issubclass(module.Plugin, Plugin):
            return module.Plugin

        if hasattr(module, "plugin_class"):
            return module.plugin_class

        # Search for any Plugin subclass
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type) and
                issubclass(obj, Plugin) and
                obj is not Plugin
            ):
                return obj

        return None

    def unload(self, name: str):
        """Unload a plugin module"""
        if name in self._loaded_modules:
            del self._loaded_modules[name]

        if name in sys.modules:
            del sys.modules[name]
