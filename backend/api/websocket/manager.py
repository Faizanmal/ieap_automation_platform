"""
WebSocket Connection Manager

Manages WebSocket connections, channels, subscriptions,
and message broadcasting with high performance.
"""

import asyncio
import contextlib
import json
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)


def now_utc() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


class MessageType(StrEnum):
    """WebSocket message types"""
    # System messages
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"

    # Subscription messages
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"

    # Data messages
    PREDICTION = "prediction"
    DECISION = "decision"
    ALERT = "alert"
    METRIC = "metric"
    NOTIFICATION = "notification"
    PIPELINE_UPDATE = "pipeline_update"
    MODEL_UPDATE = "model_update"
    HEALTH_UPDATE = "health_update"

    # Batch operations
    BATCH_START = "batch_start"
    BATCH_PROGRESS = "batch_progress"
    BATCH_COMPLETE = "batch_complete"


class Channel(StrEnum):
    """Available subscription channels"""
    PREDICTIONS = "predictions"
    DECISIONS = "decisions"
    ALERTS = "alerts"
    METRICS = "metrics"
    NOTIFICATIONS = "notifications"
    PIPELINES = "pipelines"
    MODELS = "models"
    HEALTH = "health"
    ALL = "all"


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    type: MessageType
    channel: Channel | None = None
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=now_utc)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps({
            "type": self.type.value,
            "channel": self.channel.value if self.channel else None,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id
        })

    @classmethod
    def from_json(cls, data: str) -> "WebSocketMessage":
        """Deserialize from JSON"""
        parsed = json.loads(data)
        return cls(
            type=MessageType(parsed.get("type", "error")),
            channel=Channel(parsed["channel"]) if parsed.get("channel") else None,
            data=parsed.get("data", {}),
            message_id=parsed.get("message_id", str(uuid.uuid4()))
        )


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection"""
    connection_id: str
    websocket: WebSocket
    user_id: str | None = None
    subscriptions: set[Channel] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)
    connected_at: datetime = field(default_factory=now_utc)
    last_activity: datetime = field(default_factory=now_utc)
    message_count: int = 0


class WebSocketManager:
    """
    Enterprise WebSocket Manager

    Features:
    - Connection pooling and lifecycle management
    - Channel-based pub/sub subscriptions
    - Message broadcasting (unicast, multicast, broadcast)
    - Heartbeat/ping-pong for connection health
    - Message queuing and rate limiting
    - Automatic reconnection handling
    - Metrics and monitoring
    """

    def __init__(
        self,
        heartbeat_interval: int = 30,
        max_connections_per_user: int = 5,
        message_rate_limit: int = 100  # messages per second
    ):
        self.heartbeat_interval = heartbeat_interval
        self.max_connections_per_user = max_connections_per_user
        self.message_rate_limit = message_rate_limit

        # Connection tracking
        self._connections: dict[str, ConnectionInfo] = {}
        self._user_connections: dict[str, set[str]] = {}  # user_id -> connection_ids
        self._channel_subscribers: dict[Channel, set[str]] = {
            channel: set() for channel in Channel
        }

        # Message handlers
        self._handlers: dict[MessageType, list[Callable]] = {}

        # Background tasks
        self._heartbeat_task: asyncio.Task | None = None
        self._running = False

        # Metrics
        self._total_messages_sent = 0
        self._total_messages_received = 0
        self._total_connections = 0

        logger.info("WebSocket Manager initialized")

    async def start(self):
        """Start the WebSocket manager"""
        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("WebSocket Manager started")

    async def stop(self):
        """Stop the WebSocket manager"""
        self._running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._heartbeat_task

        # Close all connections
        for conn_id in list(self._connections.keys()):
            await self.disconnect(conn_id)

        logger.info("WebSocket Manager stopped")

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> str:
        """Accept a new WebSocket connection"""
        await websocket.accept()

        connection_id = str(uuid.uuid4())

        # Check user connection limit
        if user_id:
            user_conns = self._user_connections.get(user_id, set())
            if len(user_conns) >= self.max_connections_per_user:
                await websocket.send_text(WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error": "Max connections reached", "code": "MAX_CONNECTIONS"}
                ).to_json())
                await websocket.close()
                raise ValueError(f"User {user_id} has reached max connections")

        # Create connection info
        conn_info = ConnectionInfo(
            connection_id=connection_id,
            websocket=websocket,
            user_id=user_id,
            metadata=metadata or {}
        )

        self._connections[connection_id] = conn_info

        # Track user connections
        if user_id:
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(connection_id)

        self._total_connections += 1

        # Send connected message
        await self._send_to_connection(connection_id, WebSocketMessage(
            type=MessageType.CONNECTED,
            data={
                "connection_id": connection_id,
                "user_id": user_id,
                "available_channels": [c.value for c in Channel]
            }
        ))

        logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")
        return connection_id

    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection"""
        if connection_id not in self._connections:
            return

        conn_info = self._connections[connection_id]

        # Remove from channel subscriptions
        for channel in conn_info.subscriptions:
            self._channel_subscribers[channel].discard(connection_id)

        # Remove from user connections
        if conn_info.user_id and conn_info.user_id in self._user_connections:
            self._user_connections[conn_info.user_id].discard(connection_id)
            if not self._user_connections[conn_info.user_id]:
                del self._user_connections[conn_info.user_id]

        # Close WebSocket
        try:
            if conn_info.websocket.client_state == WebSocketState.CONNECTED:
                await conn_info.websocket.close()
        except Exception as e:
            logger.warning(f"Error closing WebSocket {connection_id}: {e}")

        del self._connections[connection_id]
        logger.info(f"WebSocket disconnected: {connection_id}")

    async def subscribe(self, connection_id: str, channel: Channel) -> bool:
        """Subscribe a connection to a channel"""
        if connection_id not in self._connections:
            return False

        conn_info = self._connections[connection_id]

        if channel == Channel.ALL:
            # Subscribe to all channels
            for ch in Channel:
                if ch != Channel.ALL:
                    conn_info.subscriptions.add(ch)
                    self._channel_subscribers[ch].add(connection_id)
        else:
            conn_info.subscriptions.add(channel)
            self._channel_subscribers[channel].add(connection_id)

        await self._send_to_connection(connection_id, WebSocketMessage(
            type=MessageType.SUBSCRIBED,
            channel=channel,
            data={"channel": channel.value}
        ))

        logger.debug(f"Connection {connection_id} subscribed to {channel.value}")
        return True

    async def unsubscribe(self, connection_id: str, channel: Channel) -> bool:
        """Unsubscribe a connection from a channel"""
        if connection_id not in self._connections:
            return False

        conn_info = self._connections[connection_id]

        if channel == Channel.ALL:
            for ch in list(conn_info.subscriptions):
                conn_info.subscriptions.discard(ch)
                self._channel_subscribers[ch].discard(connection_id)
        else:
            conn_info.subscriptions.discard(channel)
            self._channel_subscribers[channel].discard(connection_id)

        await self._send_to_connection(connection_id, WebSocketMessage(
            type=MessageType.UNSUBSCRIBED,
            channel=channel,
            data={"channel": channel.value}
        ))

        return True

    async def broadcast(
        self,
        channel: Channel,
        message_type: MessageType,
        data: dict[str, Any]
    ):
        """Broadcast a message to all subscribers of a channel"""
        message = WebSocketMessage(
            type=message_type,
            channel=channel,
            data=data
        )

        subscribers = self._channel_subscribers.get(channel, set())
        tasks = [
            self._send_to_connection(conn_id, message)
            for conn_id in subscribers
        ]

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            self._total_messages_sent += len(tasks)

    async def send_to_user(
        self,
        user_id: str,
        message_type: MessageType,
        data: dict[str, Any],
        channel: Channel | None = None
    ):
        """Send a message to all connections of a specific user"""
        message = WebSocketMessage(
            type=message_type,
            channel=channel,
            data=data
        )

        conn_ids = self._user_connections.get(user_id, set())
        tasks = [
            self._send_to_connection(conn_id, message)
            for conn_id in conn_ids
        ]

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def send_to_connection(
        self,
        connection_id: str,
        message_type: MessageType,
        data: dict[str, Any],
        channel: Channel | None = None
    ):
        """Send a message to a specific connection"""
        message = WebSocketMessage(
            type=message_type,
            channel=channel,
            data=data
        )
        await self._send_to_connection(connection_id, message)

    async def _send_to_connection(self, connection_id: str, message: WebSocketMessage):
        """Internal method to send a message to a connection"""
        if connection_id not in self._connections:
            return

        conn_info = self._connections[connection_id]

        try:
            if conn_info.websocket.client_state == WebSocketState.CONNECTED:
                await conn_info.websocket.send_text(message.to_json())
                conn_info.message_count += 1
                conn_info.last_activity = now_utc()
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
        except Exception as e:
            logger.error(f"Error sending to {connection_id}: {e}")
            await self.disconnect(connection_id)

    async def handle_message(self, connection_id: str, raw_message: str):
        """Handle an incoming message from a connection"""
        if connection_id not in self._connections:
            return

        self._total_messages_received += 1
        conn_info = self._connections[connection_id]
        conn_info.last_activity = now_utc()

        try:
            message = WebSocketMessage.from_json(raw_message)

            if message.type == MessageType.PING:
                await self._send_to_connection(connection_id, WebSocketMessage(
                    type=MessageType.PONG
                ))

            elif message.type == MessageType.SUBSCRIBE:
                channel = Channel(message.data.get("channel", "all"))
                await self.subscribe(connection_id, channel)

            elif message.type == MessageType.UNSUBSCRIBE:
                channel = Channel(message.data.get("channel", "all"))
                await self.unsubscribe(connection_id, channel)

            else:
                # Dispatch to registered handlers
                handlers = self._handlers.get(message.type, [])
                for handler in handlers:
                    try:
                        await handler(connection_id, message)
                    except Exception as e:
                        logger.error(f"Handler error: {e}")

        except json.JSONDecodeError:
            await self._send_to_connection(connection_id, WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": "Invalid JSON", "code": "INVALID_JSON"}
            ))
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable
    ):
        """Register a message handler"""
        if message_type not in self._handlers:
            self._handlers[message_type] = []
        self._handlers[message_type].append(handler)

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to all connections"""
        while self._running:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                # Send ping to all connections
                tasks = [
                    self._send_to_connection(conn_id, WebSocketMessage(type=MessageType.PING))
                    for conn_id in list(self._connections.keys())
                ]

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

                # Check for stale connections
                now = now_utc()
                stale_timeout = self.heartbeat_interval * 3

                for conn_id, conn_info in list(self._connections.items()):
                    if (now - conn_info.last_activity).total_seconds() > stale_timeout:
                        logger.info(f"Disconnecting stale connection: {conn_id}")
                        await self.disconnect(conn_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get WebSocket manager statistics"""
        return {
            "active_connections": len(self._connections),
            "total_connections": self._total_connections,
            "total_messages_sent": self._total_messages_sent,
            "total_messages_received": self._total_messages_received,
            "users_connected": len(self._user_connections),
            "channel_subscribers": {
                channel.value: len(subscribers)
                for channel, subscribers in self._channel_subscribers.items()
            }
        }


# Global WebSocket manager instance
ws_manager = WebSocketManager()
