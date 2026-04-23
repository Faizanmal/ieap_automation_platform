"""
Example Plugin Implementation

Demonstrates how to create a plugin for the IEAP platform.
"""

import logging
from typing import Any

from fastapi import APIRouter

from plugins import Plugin, PluginContext, PluginInfo, plugin_hook

logger = logging.getLogger(__name__)


class ExamplePlugin(Plugin):
    """
    Example plugin demonstrating the plugin system.
    
    This plugin:
    - Adds custom API endpoints
    - Registers hook handlers
    - Provides custom CLI commands
    """

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="example-plugin",
            version="1.0.0",
            description="Example plugin demonstrating IEAP plugin system",
            author="IEAP Team",
            author_email="team@ieap.io",
            homepage="https://ieap.io/plugins/example",
            license="MIT",
            dependencies=[],
            tags=["example", "demo"],
            config_schema={
                "enabled": {"type": "boolean", "default": True},
                "greeting": {"type": "string", "default": "Hello"}
            }
        )

    async def on_load(self, context: PluginContext) -> None:
        """Called when plugin is loaded"""
        logger.info(f"Loading {self.name} v{self.version}")
        self._context = context

        # Access services from context
        # db = context.get_service("database")
        # cache = context.get_service("cache")

    async def on_unload(self) -> None:
        """Called when plugin is unloaded"""
        logger.info(f"Unloading {self.name}")

    async def on_activate(self) -> None:
        """Called when plugin is activated"""
        logger.info(f"Plugin {self.name} activated")

    async def on_deactivate(self) -> None:
        """Called when plugin is deactivated"""
        logger.info(f"Plugin {self.name} deactivated")

    def get_routes(self):
        """Return FastAPI routes for this plugin"""
        router = APIRouter(prefix="/example", tags=["example-plugin"])

        @router.get("/hello")
        async def hello():
            greeting = self.config.get("greeting", "Hello")
            return {"message": f"{greeting} from {self.name}!"}

        @router.get("/status")
        async def status():
            return self.get_status()

        return [router]

    def get_event_handlers(self) -> dict[str, Any]:
        """Return event handlers"""
        return {
            "model_deployed": self.handle_model_deployed,
            "prediction_made": self.handle_prediction
        }

    async def handle_model_deployed(self, event):
        """Handle model deployment events"""
        logger.info(f"[{self.name}] Model deployed: {event}")

    async def handle_prediction(self, event):
        """Handle prediction events"""
        logger.info(f"[{self.name}] Prediction made")

    @plugin_hook("before_prediction", priority=10)
    async def modify_prediction_input(self, model, data):
        """Hook handler for before_prediction"""
        logger.debug(f"[{self.name}] Pre-processing prediction data")
        # Modify or validate data before prediction
        return data

    @plugin_hook("after_prediction", priority=10)
    async def log_prediction(self, model, data, prediction):
        """Hook handler for after_prediction"""
        logger.debug(f"[{self.name}] Logging prediction result")
        # Log, audit, or modify prediction result
        return prediction


# Export the plugin class
Plugin = ExamplePlugin


# Plugin metadata for discovery
PLUGIN_INFO = PluginInfo(
    name="example-plugin",
    version="1.0.0",
    description="Example plugin demonstrating IEAP plugin system",
    author="IEAP Team",
    entry_point="example_plugin.py"
)
