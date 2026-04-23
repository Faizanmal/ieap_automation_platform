"""
Event Bus Module

Async event-driven architecture for decoupled component communication.
"""

from .bus import Event, EventBus, EventHandler
from .decorators import emit, on_event

__all__ = ["Event", "EventBus", "EventHandler", "emit", "on_event"]
