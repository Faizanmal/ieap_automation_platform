"""
Event Bus Implementation

High-performance async event bus for internal communication.
"""

import asyncio
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event handler priority levels"""
    HIGHEST = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    LOWEST = 4


@dataclass
class Event:
    """
    Base event class.
    
    All events should inherit from this class.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        """Get event type name"""
        return self.__class__.__name__


# Pre-defined events
@dataclass
class ModelDeployedEvent(Event):
    """Fired when an ML model is deployed"""
    model_id: str = ""
    model_name: str = ""
    version: str = ""
    replicas: int = 1


@dataclass
class ModelPredictionEvent(Event):
    """Fired when a prediction is made"""
    model_id: str = ""
    prediction_id: str = ""
    latency_ms: float = 0.0
    success: bool = True


@dataclass
class DecisionMadeEvent(Event):
    """Fired when an autonomous decision is made"""
    decision_id: str = ""
    decision_type: str = ""
    confidence: float = 0.0
    requires_approval: bool = False


@dataclass
class PipelineStatusEvent(Event):
    """Fired when pipeline status changes"""
    pipeline_id: str = ""
    pipeline_name: str = ""
    old_status: str = ""
    new_status: str = ""


@dataclass
class AlertEvent(Event):
    """Fired when an alert is triggered"""
    alert_id: str = ""
    severity: str = "medium"  # low, medium, high, critical
    message: str = ""
    component: str = ""


@dataclass
class UserActionEvent(Event):
    """Fired when a user performs an action"""
    user_id: str = ""
    action: str = ""
    resource: str = ""
    resource_id: str = ""


@dataclass
class SystemHealthEvent(Event):
    """Fired on system health changes"""
    component: str = ""
    status: str = "healthy"  # healthy, degraded, unhealthy
    message: str = ""


@dataclass
class EventHandler:
    """Event handler registration"""
    callback: Callable
    event_types: set[str]
    priority: EventPriority = EventPriority.NORMAL
    filter_func: Callable | None = None
    one_time: bool = False
    async_handler: bool = True
    handler_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class EventBus:
    """
    Async event bus for publish-subscribe messaging.
    
    Features:
    - Async event processing
    - Event filtering
    - Handler priorities
    - Event history
    - Dead letter queue
    - Metrics and monitoring
    
    Usage:
        bus = EventBus()
        
        # Subscribe to events
        @bus.on(ModelDeployedEvent)
        async def handle_deployment(event: ModelDeployedEvent):
            print(f"Model {event.model_name} deployed!")
        
        # Publish events
        await bus.emit(ModelDeployedEvent(
            model_id="model_123",
            model_name="anomaly-detector",
            version="1.0.0"
        ))
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        max_history: int = 1000,
        dead_letter_max: int = 100,
        enable_metrics: bool = True
    ):
        if self._initialized:
            return

        self._handlers: dict[str, list[EventHandler]] = {}
        self._history: list[Event] = []
        self._dead_letter: list[tuple] = []
        self._max_history = max_history
        self._dead_letter_max = dead_letter_max
        self._enable_metrics = enable_metrics

        # Metrics
        self._events_published = 0
        self._events_handled = 0
        self._events_failed = 0

        # Processing queue
        self._queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: asyncio.Task | None = None
        self._running = False

        self._initialized = True
        logger.info("EventBus initialized")

    async def start(self):
        """Start the event bus processing loop"""
        self._running = True
        self._processing_task = asyncio.create_task(self._process_loop())
        logger.info("EventBus started")

    async def stop(self):
        """Stop the event bus"""
        self._running = False

        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

        logger.info("EventBus stopped")

    async def _process_loop(self):
        """Main event processing loop"""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._dispatch_event(event)
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")

    def on(
        self,
        *event_types: type[Event],
        priority: EventPriority = EventPriority.NORMAL,
        filter_func: Callable | None = None,
        one_time: bool = False
    ) -> Callable:
        """
        Decorator to register an event handler.
        
        Usage:
            @bus.on(ModelDeployedEvent, ModelPredictionEvent)
            async def handler(event):
                pass
        """
        def decorator(func: Callable) -> Callable:
            self.subscribe(
                func,
                *event_types,
                priority=priority,
                filter_func=filter_func,
                one_time=one_time
            )
            return func
        return decorator

    def subscribe(
        self,
        callback: Callable,
        *event_types: type[Event],
        priority: EventPriority = EventPriority.NORMAL,
        filter_func: Callable | None = None,
        one_time: bool = False
    ) -> str:
        """
        Subscribe to events.
        
        Returns handler ID for later unsubscription.
        """
        handler = EventHandler(
            callback=callback,
            event_types={et.__name__ for et in event_types} if event_types else {"*"},
            priority=priority,
            filter_func=filter_func,
            one_time=one_time,
            async_handler=asyncio.iscoroutinefunction(callback)
        )

        for event_type in handler.event_types:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
            # Sort by priority
            self._handlers[event_type].sort(key=lambda h: h.priority.value)

        logger.debug(f"Handler {handler.handler_id} subscribed to {handler.event_types}")
        return handler.handler_id

    def unsubscribe(self, handler_id: str):
        """Unsubscribe a handler"""
        for event_type in list(self._handlers.keys()):
            self._handlers[event_type] = [
                h for h in self._handlers[event_type]
                if h.handler_id != handler_id
            ]

    async def emit(self, event: Event, wait: bool = False):
        """
        Emit an event.
        
        Args:
            event: The event to emit
            wait: If True, wait for all handlers to complete
        """
        self._events_published += 1

        # Add to history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        if wait:
            await self._dispatch_event(event)
        else:
            await self._queue.put(event)

        logger.debug(f"Event {event.event_type} emitted")

    def emit_sync(self, event: Event):
        """Emit an event synchronously (for use in sync context)"""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.emit(event))
        except RuntimeError:
            # No running loop, create new one
            asyncio.run(self.emit(event, wait=True))

    async def _dispatch_event(self, event: Event):
        """Dispatch event to all registered handlers"""
        event_type = event.event_type
        handlers_to_call = []

        # Get type-specific handlers
        if event_type in self._handlers:
            handlers_to_call.extend(self._handlers[event_type])

        # Get wildcard handlers
        if "*" in self._handlers:
            handlers_to_call.extend(self._handlers["*"])

        # Sort by priority
        handlers_to_call.sort(key=lambda h: h.priority.value)

        handlers_to_remove = []

        for handler in handlers_to_call:
            try:
                # Check filter
                if handler.filter_func:
                    if not handler.filter_func(event):
                        continue

                # Call handler
                if handler.async_handler:
                    await handler.callback(event)
                else:
                    handler.callback(event)

                self._events_handled += 1

                # Mark one-time handlers for removal
                if handler.one_time:
                    handlers_to_remove.append(handler.handler_id)

            except Exception as e:
                self._events_failed += 1
                logger.error(f"Handler error for {event_type}: {e}")

                # Add to dead letter queue
                self._dead_letter.append((event, handler.handler_id, str(e)))
                if len(self._dead_letter) > self._dead_letter_max:
                    self._dead_letter.pop(0)

        # Remove one-time handlers
        for handler_id in handlers_to_remove:
            self.unsubscribe(handler_id)

    def get_history(
        self,
        event_type: str | None = None,
        limit: int = 100
    ) -> list[Event]:
        """Get event history"""
        events = self._history

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return events[-limit:]

    def get_dead_letters(self) -> list[tuple]:
        """Get dead letter queue"""
        return self._dead_letter.copy()

    def get_stats(self) -> dict[str, Any]:
        """Get event bus statistics"""
        return {
            "events_published": self._events_published,
            "events_handled": self._events_handled,
            "events_failed": self._events_failed,
            "queue_size": self._queue.qsize(),
            "history_size": len(self._history),
            "dead_letters": len(self._dead_letter),
            "handlers": {
                event_type: len(handlers)
                for event_type, handlers in self._handlers.items()
            }
        }

    def clear_history(self):
        """Clear event history"""
        self._history.clear()

    def clear_dead_letters(self):
        """Clear dead letter queue"""
        self._dead_letter.clear()


# Global event bus instance
event_bus = EventBus()
