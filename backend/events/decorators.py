"""
Event Decorators

Convenience decorators for event handling.
"""

from collections.abc import Callable
from functools import wraps

from .bus import Event, EventBus, EventPriority, event_bus


def on_event(
    *event_types: type[Event],
    priority: EventPriority = EventPriority.NORMAL,
    filter_func: Callable = None,
    bus: EventBus = None
) -> Callable:
    """
    Decorator to register an event handler.
    
    Usage:
        @on_event(ModelDeployedEvent)
        async def handle_deployment(event: ModelDeployedEvent):
            print(f"Model deployed: {event.model_name}")
    """
    def decorator(func: Callable) -> Callable:
        target_bus = bus or event_bus
        target_bus.subscribe(
            func,
            *event_types,
            priority=priority,
            filter_func=filter_func
        )
        return func
    return decorator


async def emit(event: Event, bus: EventBus = None, wait: bool = False):
    """
    Emit an event.
    
    Usage:
        await emit(ModelDeployedEvent(model_id="123", model_name="test"))
    """
    target_bus = bus or event_bus
    await target_bus.emit(event, wait=wait)


def event_emitter(event_class: type[Event], bus: EventBus = None) -> Callable:
    """
    Decorator that emits an event after successful function execution.
    
    Usage:
        @event_emitter(ModelDeployedEvent)
        async def deploy_model(model_id: str, model_name: str) -> Dict:
            # Deploy logic
            return {"model_id": model_id, "model_name": model_name}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Create event from result if it's a dict
            if isinstance(result, dict):
                event = event_class(**result)
            else:
                event = event_class()

            target_bus = bus or event_bus
            await target_bus.emit(event)

            return result
        return wrapper
    return decorator
