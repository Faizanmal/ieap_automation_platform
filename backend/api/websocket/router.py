"""
WebSocket Router

FastAPI WebSocket endpoints for real-time communication.
"""

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from .manager import Channel, ws_manager

logger = logging.getLogger(__name__)

websocket_router = APIRouter(tags=["WebSocket"])


@websocket_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(None),
    channels: str | None = Query(None)
):
    """
    Main WebSocket endpoint for real-time communication.

    Query parameters:
    - token: Optional authentication token
    - channels: Comma-separated list of channels to subscribe to

    Message format (JSON):
    ```json
    {
        "type": "subscribe|unsubscribe|ping",
        "channel": "predictions|decisions|alerts|metrics|...",
        "data": {}
    }
    ```
    """
    user_id = None

    # Authenticate if token provided
    if token:
        # TODO: Validate token and extract user_id
        user_id = f"user_{token[:8]}"

    connection_id = await ws_manager.connect(
        websocket,
        user_id=user_id,
        metadata={"source": "websocket_endpoint"}
    )

    try:
        # Auto-subscribe to requested channels
        if channels:
            for raw_channel_name in channels.split(","):
                channel_name = raw_channel_name.strip().lower()
                try:
                    channel = Channel(channel_name)
                    await ws_manager.subscribe(connection_id, channel)
                except ValueError:
                    logger.warning(f"Invalid channel: {channel_name}")

        # Message handling loop
        while True:
            data = await websocket.receive_text()
            await ws_manager.handle_message(connection_id, data)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(connection_id)


@websocket_router.websocket("/ws/predictions/{model_id}")
async def prediction_stream(
    websocket: WebSocket,
    model_id: str,
    token: str | None = Query(None)
):
    """
    Stream predictions from a specific model in real-time.

    Useful for:
    - Live anomaly detection monitoring
    - Real-time fraud detection alerts
    - Streaming inference results
    """
    user_id = f"user_{token[:8]}" if token else None

    connection_id = await ws_manager.connect(
        websocket,
        user_id=user_id,
        metadata={"model_id": model_id, "type": "prediction_stream"}
    )

    try:
        # Auto-subscribe to predictions channel
        await ws_manager.subscribe(connection_id, Channel.PREDICTIONS)

        while True:
            data = await websocket.receive_text()
            await ws_manager.handle_message(connection_id, data)

    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(connection_id)


@websocket_router.websocket("/ws/dashboard")
async def dashboard_stream(
    websocket: WebSocket,
    token: str | None = Query(None)
):
    """
    Real-time dashboard data stream.

    Provides:
    - Live metrics updates
    - Health status changes
    - Alert notifications
    - Pipeline status updates
    """
    user_id = f"user_{token[:8]}" if token else None

    connection_id = await ws_manager.connect(
        websocket,
        user_id=user_id,
        metadata={"type": "dashboard"}
    )

    try:
        # Subscribe to dashboard-relevant channels
        for channel in [Channel.METRICS, Channel.HEALTH, Channel.ALERTS]:
            await ws_manager.subscribe(connection_id, channel)

        while True:
            data = await websocket.receive_text()
            await ws_manager.handle_message(connection_id, data)

    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(connection_id)


@websocket_router.websocket("/ws/alerts")
async def alerts_stream(
    websocket: WebSocket,
    severity: str | None = Query(None),
    token: str | None = Query(None)
):
    """
    Real-time alerts stream.

    Severity levels: critical, high, medium, low
    """
    user_id = f"user_{token[:8]}" if token else None

    connection_id = await ws_manager.connect(
        websocket,
        user_id=user_id,
        metadata={"type": "alerts", "severity_filter": severity}
    )

    try:
        await ws_manager.subscribe(connection_id, Channel.ALERTS)

        while True:
            data = await websocket.receive_text()
            await ws_manager.handle_message(connection_id, data)

    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(connection_id)
